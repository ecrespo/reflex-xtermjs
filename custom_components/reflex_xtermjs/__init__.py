"""reflex-xtermjs - the xterm.js terminal emulator as a Reflex component.

Quick start::

    import reflex as rx
    from reflex_xtermjs import THEMES, XTermAPI, xterm

    term = XTermAPI("shell")

    class State(rx.State):
        @rx.event
        def greet(self):
            return term.writeln("hello from Reflex")

    def index():
        return rx.vstack(
            rx.button("Greet", on_click=State.greet),
            rx.box(
                xterm(
                    terminal_id="shell",
                    theme=THEMES["dracula"],
                    addons=["fit", "web-links", "search"],
                ),
                height="400px",
                width="100%",
            ),
        )

The PTY backend lives in :mod:`reflex_xtermjs.pty` and is imported explicitly,
so apps that only need a display terminal never pull it in.
"""

from .api import XTermAPI
from .props import (
    ImageOptions,
    LigatureOptions,
    OverviewRulerOptions,
    SearchDecorationOptions,
    SearchOptions,
    WindowsPty,
    XTermTheme,
)
from .themes import THEME_NAMES, THEMES, get_theme
from .xtermjs import ADDONS, XTerm, xterm

__all__ = [
    "ADDONS",
    "THEMES",
    "THEME_NAMES",
    "ImageOptions",
    "LigatureOptions",
    "OverviewRulerOptions",
    "SearchDecorationOptions",
    "SearchOptions",
    "WindowsPty",
    "XTerm",
    "XTermAPI",
    "XTermTheme",
    "get_theme",
    "xterm",
]

__version__ = "0.1.0"
