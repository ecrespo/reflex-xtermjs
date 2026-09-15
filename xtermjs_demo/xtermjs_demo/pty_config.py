"""PTY endpoint settings shared by the demo app and its live-shell page."""

from __future__ import annotations

import os
import secrets

from reflex_xtermjs.pty import PtyConfig

#: Shared secret for the demo PTY endpoint. Set ``XTERMJS_DEMO_PTY_TOKEN`` to
#: pin it; otherwise a fresh one is generated per backend process.
PTY_TOKEN: str = os.environ.get("XTERMJS_DEMO_PTY_TOKEN") or secrets.token_urlsafe(16)

#: The shell handed to every connection. Override with ``XTERMJS_DEMO_SHELL``.
PTY_COMMAND: str | None = os.environ.get("XTERMJS_DEMO_SHELL")

PTY_SETTINGS = PtyConfig(
    **({"command": PTY_COMMAND} if PTY_COMMAND else {}),
    path="/pty",
    token=PTY_TOKEN,
    cols=100,
    rows=28,
    max_sessions=4,
)


def pty_websocket_url() -> str:
    """Build the WebSocket URL of the demo PTY endpoint.

    Reflex serves the frontend and the backend on different ports during
    development, so a bare ``/pty`` path would hit the Vite dev server. The
    URL is derived from the configured backend API URL instead, falling back
    to a same-origin path when no API URL is configured.

    Returns:
        A ``ws://`` / ``wss://`` URL, or a same-origin path.
    """
    import reflex as rx

    api_url = (getattr(rx.config.get_config(), "api_url", "") or "").rstrip("/")
    if api_url.startswith("https://"):
        base = "wss://" + api_url[len("https://") :]
    elif api_url.startswith("http://"):
        base = "ws://" + api_url[len("http://") :]
    else:
        base = api_url
    return f"{base}{PTY_SETTINGS.path}?token={PTY_TOKEN}"
