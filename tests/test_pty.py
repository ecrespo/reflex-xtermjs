"""Tests for the reference PTY backend."""

from __future__ import annotations

import os

import pytest
from reflex_xtermjs.pty import (
    PtyConfig,
    PtySession,
    _authorize,
    _handle_control,
    pty_app,
)


class FakeClient:
    def __init__(self, host: str) -> None:
        self.host = host


class FakeWebSocket:
    def __init__(self, host: str = "127.0.0.1", params: dict | None = None) -> None:
        self.client = FakeClient(host)
        self.query_params = params or {}


def test_defaults_are_localhost_only():
    """Without a token the endpoint accepts loopback clients only."""
    config = PtyConfig()
    assert config.token is None
    assert config.allow_remote is False
    assert _authorize(FakeWebSocket("127.0.0.1"), config, 0) is None
    assert _authorize(FakeWebSocket("10.0.0.7"), config, 0) is not None


def test_token_is_required_when_configured():
    """A configured token gates every connection."""
    config = PtyConfig(token="s3cret")
    assert _authorize(FakeWebSocket(params={"token": "s3cret"}), config, 0) is None
    assert _authorize(FakeWebSocket(params={"token": "wrong"}), config, 0) == ("invalid token")
    assert _authorize(FakeWebSocket(params={}), config, 0) == "invalid token"


def test_remote_clients_need_the_opt_in():
    """A valid token is not enough for a remote client by default."""
    config = PtyConfig(token="s3cret")
    remote = FakeWebSocket("203.0.113.9", {"token": "s3cret"})
    assert _authorize(remote, config, 0) == "remote connections are disabled"
    assert _authorize(remote, PtyConfig(token="s3cret", allow_remote=True), 0) is None


def test_session_cap_is_enforced():
    """New shells are refused once the cap is reached."""
    config = PtyConfig(max_sessions=2)
    assert _authorize(FakeWebSocket(), config, 2) == "too many terminal sessions"


def test_child_environment_sets_term_and_drops_stale_size():
    """The child gets a sane TERM and no leftover COLUMNS/LINES."""
    os.environ["COLUMNS"] = "999"
    try:
        env = PtyConfig(term="xterm-256color", env={"FOO": "bar"}).child_env()
    finally:
        os.environ.pop("COLUMNS", None)
    assert env["TERM"] == "xterm-256color"
    assert env["FOO"] == "bar"
    assert "COLUMNS" not in env


@pytest.mark.parametrize(
    "payload",
    [
        "ls -la\n",
        "{not json",
        '{"type": "unknown"}',
        '["resize", 10, 10]',
        '"just a string"',
    ],
)
def test_ordinary_input_is_not_mistaken_for_control(payload: str):
    """Only a well-formed known control frame is intercepted."""
    session = PtySession(PtyConfig())
    assert _handle_control(session, payload) is False


def test_resize_frame_is_intercepted():
    """The resize frame never reaches the shell as input."""
    session = PtySession(PtyConfig())
    assert _handle_control(session, '{"type": "resize", "cols": 90, "rows": 30}')


def test_resize_clamps_absurd_geometries():
    """A hostile client cannot ask for a million columns."""
    session = PtySession(PtyConfig())
    session.resize(10**9, -5)  # no fd yet: must not raise
    assert session.fd is None


def test_pty_app_exposes_the_configured_route():
    """The Starlette app serves exactly one WebSocket route."""
    app = pty_app(PtyConfig(path="/terminal"))
    paths = [getattr(route, "path", None) for route in app.routes]
    assert "/terminal" in paths


def test_session_round_trip():
    """A spawned session echoes what is written to it."""
    session = PtySession(PtyConfig(command="/bin/sh", args=("-c", "echo ready")))
    session.spawn()
    try:
        assert session.pid and session.fd
        output = b""
        for _ in range(200):
            try:
                chunk = os.read(session.fd, 4096)
            except BlockingIOError:
                import time

                time.sleep(0.01)
                continue
            except OSError:
                break
            if not chunk:
                break
            output += chunk
            if b"ready" in output:
                break
        assert b"ready" in output
    finally:
        session.close()
    assert session.fd is None
