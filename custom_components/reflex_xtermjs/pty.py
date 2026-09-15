"""A reference PTY backend for :mod:`reflex_xtermjs`.

This module exposes a Starlette sub-application with a single WebSocket route
that spawns a real pseudo-terminal and pipes it to a browser terminal through
``@xterm/addon-attach``. Mount it on a Reflex app with ``api_transformer``::

    import reflex as rx
    from reflex_xtermjs.pty import PtyConfig, pty_app

    app = rx.App(
        api_transformer=pty_app(PtyConfig(command="/bin/bash", token="secret")),
    )

and point the component at it::

    xterm(websocket_url="/pty?token=secret", addons=["fit"])

.. warning::

   A PTY endpoint gives whoever can reach it a shell with the privileges of
   the Reflex backend process. There is no sandbox here. Only expose it on a
   trusted network, always set a ``token``, and prefer running the backend as
   an unprivileged user in a container. :class:`PtyConfig` defaults are
   deliberately restrictive: no token means the endpoint refuses every
   connection that is not from localhost.

The protocol on the wire is the one ``@xterm/addon-attach`` speaks - raw bytes
in both directions - plus one out-of-band control frame the component sends on
resize::

    {"type": "resize", "cols": 120, "rows": 30}

Only a text frame that parses as JSON *and* carries a known ``type`` is treated
as control; anything else is forwarded to the shell verbatim.
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import json
import logging
import os
import pty
import shutil
import signal
import struct
import termios
from dataclasses import dataclass, field
from typing import Any

__all__ = ["PtyConfig", "PtySession", "pty_app", "pty_websocket_endpoint"]

logger = logging.getLogger(__name__)

_CONTROL_TYPES = frozenset({"resize", "ping"})
_READ_SIZE = 65536
_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1"})


def _default_shell() -> str:
    """Pick a sensible interactive shell for the host."""
    return os.environ.get("SHELL") or shutil.which("bash") or shutil.which("sh") or "/bin/sh"


@dataclass
class PtyConfig:
    """Settings for the PTY endpoint.

    Attributes:
        command: Program to run. Defaults to the user's shell.
        args: Extra arguments passed to ``command``.
        cwd: Working directory of the child process.
        env: Extra environment variables merged into the child environment.
        term: Value of ``TERM`` for the child.
        cols: Initial column count, before the first resize frame arrives.
        rows: Initial row count.
        path: WebSocket route to serve.
        token: Shared secret required as a ``token`` query parameter. When it
            is ``None`` only loopback clients are accepted.
        max_sessions: Refuse new connections beyond this many live shells.
        allow_remote: Accept non-loopback clients. Requires ``token``.
    """

    command: str = field(default_factory=_default_shell)
    args: tuple[str, ...] = ()
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    term: str = "xterm-256color"
    cols: int = 80
    rows: int = 24
    path: str = "/pty"
    token: str | None = None
    max_sessions: int = 8
    allow_remote: bool = False

    def child_env(self) -> dict[str, str]:
        """Build the environment handed to the child process."""
        environment = dict(os.environ)
        environment["TERM"] = self.term
        environment.pop("LINES", None)
        environment.pop("COLUMNS", None)
        environment.update(self.env)
        return environment


class PtySession:
    """One pseudo-terminal wired to one WebSocket."""

    def __init__(self, config: PtyConfig) -> None:
        self.config = config
        self.pid: int | None = None
        self.fd: int | None = None

    def spawn(self) -> None:
        """Fork a child process attached to a new pseudo-terminal."""
        pid, fd = pty.fork()
        if pid == 0:  # pragma: no cover - runs only in the forked child
            try:
                if self.config.cwd:
                    os.chdir(self.config.cwd)
                argv = [self.config.command, *self.config.args]
                os.execvpe(self.config.command, argv, self.config.child_env())
            except Exception:  # noqa: BLE001 - last resort in the child
                os._exit(1)
        self.pid = pid
        self.fd = fd
        os.set_blocking(fd, False)
        self.resize(self.config.cols, self.config.rows)

    def resize(self, cols: int, rows: int) -> None:
        """Apply a new window size to the pseudo-terminal."""
        if self.fd is None:
            return
        cols = max(1, min(int(cols), 1000))
        rows = max(1, min(int(rows), 1000))
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        with contextlib.suppress(OSError):
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

    def write(self, data: bytes) -> None:
        """Forward bytes to the child process."""
        if self.fd is None:
            return
        with contextlib.suppress(OSError):
            os.write(self.fd, data)

    def close(self) -> None:
        """Terminate the child and release the pseudo-terminal."""
        if self.pid is not None:
            with contextlib.suppress(ProcessLookupError, OSError):
                os.kill(self.pid, signal.SIGHUP)
            with contextlib.suppress(ChildProcessError, OSError):
                os.waitpid(self.pid, os.WNOHANG)
            self.pid = None
        if self.fd is not None:
            with contextlib.suppress(OSError):
                os.close(self.fd)
            self.fd = None


def _authorize(websocket: Any, config: PtyConfig, live: int) -> str | None:
    """Return a rejection reason, or ``None`` when the client may connect."""
    if live >= config.max_sessions:
        return "too many terminal sessions"

    client_host = getattr(getattr(websocket, "client", None), "host", None)
    is_local = client_host in _LOCAL_HOSTS

    if config.token is not None:
        supplied = websocket.query_params.get("token")
        if supplied != config.token:
            return "invalid token"
        if not is_local and not config.allow_remote:
            return "remote connections are disabled"
        return None

    if not is_local:
        return "a token is required for non-local connections"
    return None


def pty_websocket_endpoint(config: PtyConfig | None = None):
    """Build the WebSocket endpoint coroutine for a PTY.

    Args:
        config: Endpoint settings. Defaults to a localhost-only shell.

    Returns:
        An ``async def endpoint(websocket)`` suitable for a Starlette route.
    """
    settings = config or PtyConfig()
    live_sessions: set[PtySession] = set()

    async def endpoint(websocket: Any) -> None:
        reason = _authorize(websocket, settings, len(live_sessions))
        if reason is not None:
            logger.warning("Refusing PTY connection: %s", reason)
            await websocket.close(code=4403, reason=reason)
            return

        await websocket.accept()

        session = PtySession(settings)
        try:
            session.spawn()
        except OSError:
            logger.exception("Could not start the PTY")
            await websocket.close(code=1011, reason="could not start a terminal")
            return

        live_sessions.add(session)
        loop = asyncio.get_running_loop()
        finished: asyncio.Future[None] = loop.create_future()
        fd = session.fd
        assert fd is not None

        def on_readable() -> None:
            """Pump PTY output to the browser."""
            try:
                data = os.read(fd, _READ_SIZE)
            except BlockingIOError:
                return
            except OSError:
                data = b""
            if not data:
                loop.remove_reader(fd)
                if not finished.done():
                    finished.set_result(None)
                return
            asyncio.ensure_future(_safe_send(data))

        async def _safe_send(data: bytes) -> None:
            try:
                await websocket.send_bytes(data)
            except Exception:  # noqa: BLE001 - socket went away mid-write
                if not finished.done():
                    finished.set_result(None)

        loop.add_reader(fd, on_readable)

        async def pump_input() -> None:
            """Pump browser input (and control frames) to the PTY."""
            while True:
                message = await websocket.receive()
                kind = message.get("type")
                if kind == "websocket.disconnect":
                    return
                text = message.get("text")
                if text is not None:
                    if not _handle_control(session, text):
                        session.write(text.encode("utf-8", "surrogateescape"))
                    continue
                payload = message.get("bytes")
                if payload:
                    session.write(payload)

        pump = asyncio.ensure_future(pump_input())
        try:
            await asyncio.wait([pump, finished], return_when=asyncio.FIRST_COMPLETED)
        finally:
            pump.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await pump
            with contextlib.suppress(ValueError, OSError):
                loop.remove_reader(fd)
            live_sessions.discard(session)
            session.close()
            with contextlib.suppress(Exception):
                await websocket.close()

    return endpoint


def _handle_control(session: PtySession, text: str) -> bool:
    """Apply an out-of-band control frame; report whether it was one."""
    stripped = text.lstrip()
    if not stripped.startswith("{"):
        return False
    try:
        message = json.loads(stripped)
    except (ValueError, TypeError):
        return False
    if not isinstance(message, dict):
        return False
    kind = message.get("type")
    if kind not in _CONTROL_TYPES:
        return False
    if kind == "resize":
        session.resize(message.get("cols", 80), message.get("rows", 24))
    return True


def pty_app(config: PtyConfig | None = None):
    """Build a Starlette app serving the PTY WebSocket route.

    Args:
        config: Endpoint settings. Defaults to a localhost-only shell on
            ``/pty``.

    Returns:
        A Starlette application to pass as ``rx.App(api_transformer=...)``.
    """
    from starlette.applications import Starlette
    from starlette.routing import WebSocketRoute

    settings = config or PtyConfig()
    return Starlette(
        routes=[
            WebSocketRoute(
                settings.path,
                pty_websocket_endpoint(settings),
                name="reflex_xtermjs_pty",
            )
        ]
    )
