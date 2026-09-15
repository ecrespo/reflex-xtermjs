"""Page 1 - a real shell running on the backend, piped over a WebSocket."""

from __future__ import annotations

import reflex as rx
from reflex_xtermjs import THEME_NAMES, THEMES, XTermAPI, xterm

from ..pty_config import pty_websocket_url
from ..shared import TERMINAL_FRAME, page_layout

term = XTermAPI("live-shell")


class ShellState(rx.State):
    """Connection state of the live shell."""

    endpoint: str = ""
    status: str = "Disconnected"
    connected: bool = False
    title: str = ""
    cols: int = 0
    rows: int = 0
    theme_name: str = "dracula"

    @rx.var
    def theme(self) -> dict:
        """The selected theme, as a plain dict for the component."""
        return THEMES[self.theme_name].dict()

    @rx.event
    def connect(self):
        """Point the terminal at the PTY endpoint."""
        self.endpoint = pty_websocket_url()
        self.status = "Connecting..."

    @rx.event
    def disconnect(self):
        """Drop the socket."""
        self.endpoint = ""
        self.connected = False
        self.status = "Disconnected"

    @rx.event
    def on_open(self, url: str):
        """Mark the shell as live."""
        self.connected = True
        self.status = "Connected"

    @rx.event
    def on_close(self, code: int, reason: str):
        """Report why the shell went away."""
        self.connected = False
        self.status = f"Closed ({code}){f': {reason}' if reason else ''}"

    @rx.event
    def on_error(self, message: str):
        """Surface socket errors."""
        self.connected = False
        self.status = f"Error: {message}"

    @rx.event
    def on_title(self, title: str):
        """Track the title the shell sets through OSC 0/2."""
        self.title = title

    @rx.event
    def on_resize(self, cols: int, rows: int):
        """Track the terminal geometry."""
        self.cols, self.rows = cols, rows

    @rx.event
    def set_theme(self, name: str):
        """Switch the colour theme without reconnecting."""
        self.theme_name = name


def status_badge() -> rx.Component:
    """Colour-coded connection indicator."""
    return rx.badge(
        ShellState.status,
        color_scheme=rx.cond(ShellState.connected, "green", "gray"),
        variant="soft",
        size="2",
    )


def index() -> rx.Component:
    """The live-shell page."""
    return page_layout(
        "Live shell",
        "A real pseudo-terminal spawned by the Reflex backend and attached to "
        "xterm.js through @xterm/addon-attach. Resizing the browser sends a "
        "TIOCSWINSZ to the shell, so full-screen programs like htop or vim "
        "behave correctly.",
        rx.hstack(
            rx.button(
                rx.icon("plug", size=16),
                "Connect",
                on_click=ShellState.connect,
                disabled=ShellState.connected,
            ),
            rx.button(
                rx.icon("power-off", size=16),
                "Disconnect",
                on_click=ShellState.disconnect,
                disabled=~ShellState.connected,
                variant="soft",
                color_scheme="red",
            ),
            rx.button(
                rx.icon("eraser", size=16),
                "Clear",
                on_click=term.clear(),
                variant="soft",
            ),
            rx.button(
                rx.icon("maximize-2", size=16),
                "Fit",
                on_click=term.fit(),
                variant="soft",
            ),
            rx.select(
                THEME_NAMES,
                value=ShellState.theme_name,
                on_change=ShellState.set_theme,
                width="200px",
            ),
            rx.spacer(),
            status_badge(),
            rx.cond(
                ShellState.cols > 0,
                rx.badge(f"{ShellState.cols}x{ShellState.rows}", variant="outline"),
            ),
            width="100%",
            align="center",
            spacing="3",
            wrap="wrap",
        ),
        rx.cond(
            ShellState.title != "",
            rx.text(ShellState.title, size="2", color="var(--gray-11)"),
        ),
        rx.box(
            xterm(
                terminal_id="live-shell",
                websocket_url=ShellState.endpoint,
                theme=ShellState.theme,
                addons=["fit", "web-links", "clipboard", "unicode-graphemes"],
                renderer="webgl",
                font_family='"JetBrains Mono", "Fira Code", Menlo, Consolas, monospace',
                font_size=14,
                cursor_blink=True,
                scrollback=5000,
                initial_text=(
                    "\x1b[1;36mreflex-xtermjs\x1b[0m - press "
                    "\x1b[1mConnect\x1b[0m to start a shell.\r\n"
                ),
                on_socket_open=ShellState.on_open,
                on_socket_close=ShellState.on_close,
                on_socket_error=ShellState.on_error,
                on_title_change=ShellState.on_title,
                on_resize=ShellState.on_resize,
            ),
            height="480px",
            width="100%",
            **TERMINAL_FRAME,
        ),
        rx.callout(
            "The PTY endpoint runs a shell with the privileges of the backend "
            "process and is protected by a per-process token, refusing remote "
            "clients by default. Never expose it on an untrusted network.",
            icon="triangle-alert",
            color_scheme="amber",
            width="100%",
        ),
    )
