"""Page 2 - every terminal option wired to a live control."""

from __future__ import annotations

import reflex as rx
from reflex_xtermjs import THEME_NAMES, THEMES, XTermAPI, xterm

from ..shared import TERMINAL_FRAME, page_layout

term = XTermAPI("playground")

SAMPLE = (
    "\x1b[1;35m reflex-xtermjs playground\x1b[0m\r\n\r\n"
    "  \x1b[30;47m 30 \x1b[0m\x1b[31m 31 \x1b[32m 32 \x1b[33m 33 "
    "\x1b[34m 34 \x1b[35m 35 \x1b[36m 36 \x1b[37m 37 \x1b[0m\r\n"
    "  \x1b[90m 90 \x1b[91m 91 \x1b[92m 92 \x1b[93m 93 "
    "\x1b[94m 94 \x1b[95m 95 \x1b[96m 96 \x1b[97m 97 \x1b[0m\r\n\r\n"
    "  \x1b[1mbold\x1b[0m  \x1b[3mitalic\x1b[0m  \x1b[4munderline\x1b[0m  "
    "\x1b[9mstrikethrough\x1b[0m  \x1b[7minverse\x1b[0m\r\n\r\n"
    "  box drawing: ┌─┬─┐  │ │ │  "
    "└─┴─┘   blocks: █▓▒░\r\n"
    "  unicode: café ñandú 日本語 中文 "
    "🚀 🌐 ─ emoji need the graphemes addon\r\n\r\n"
    "  \x1b[38;5;208m256-colour\x1b[0m and "
    "\x1b[38;2;80;250;123mtruecolour\x1b[0m are both supported.\r\n\r\n"
    "\x1b[32m$\x1b[0m "
)


class PlaygroundState(rx.State):
    """Every knob exposed by the playground."""

    theme_name: str = "tokyo-night"
    font_size: int = 15
    line_height: float = 1.2
    letter_spacing: float = 0.0
    font_family: str = '"JetBrains Mono", Menlo, Consolas, monospace'
    cursor_style: str = "block"
    cursor_inactive_style: str = "outline"
    cursor_blink: bool = True
    renderer: str = "webgl"
    scrollback: int = 1000
    minimum_contrast_ratio: float = 1.0
    draw_bold_bright: bool = True
    allow_transparency: bool = False
    screen_reader_mode: bool = False
    auto_fit: bool = True
    cols: int = 80
    rows: int = 24
    reported: str = ""

    @rx.var
    def theme(self) -> dict:
        """Selected theme as a plain dict."""
        return THEMES[self.theme_name].dict()

    @rx.event
    def set_theme_name(self, value: str):
        """Select a colour theme."""
        self.theme_name = value

    @rx.event
    def set_renderer(self, value: str):
        """Switch renderer backend."""
        self.renderer = value

    @rx.event
    def set_cursor_style(self, value: str):
        """Change the focused cursor shape."""
        self.cursor_style = value

    @rx.event
    def set_cursor_inactive_style(self, value: str):
        """Change the unfocused cursor shape."""
        self.cursor_inactive_style = value

    @rx.event
    def set_font_family(self, value: str):
        """Change the font stack."""
        self.font_family = value

    @rx.event
    def set_font_size(self, value: list[float]):
        """Change the font size."""
        self.font_size = int(value[0])

    @rx.event
    def set_line_height(self, value: list[float]):
        """Change the line height multiplier."""
        self.line_height = float(value[0])

    @rx.event
    def set_letter_spacing(self, value: list[float]):
        """Change the letter spacing."""
        self.letter_spacing = float(value[0])

    @rx.event
    def set_minimum_contrast_ratio(self, value: list[float]):
        """Change the enforced contrast ratio."""
        self.minimum_contrast_ratio = float(value[0])

    @rx.event
    def set_scrollback(self, value: list[float]):
        """Change the scrollback size."""
        self.scrollback = int(value[0])

    @rx.event
    def set_cursor_blink(self, value: bool):
        """Toggle cursor blinking."""
        self.cursor_blink = value

    @rx.event
    def set_draw_bold_bright(self, value: bool):
        """Toggle bright colours for bold text."""
        self.draw_bold_bright = value

    @rx.event
    def set_allow_transparency(self, value: bool):
        """Toggle background transparency."""
        self.allow_transparency = value

    @rx.event
    def set_screen_reader_mode(self, value: bool):
        """Toggle the accessibility DOM."""
        self.screen_reader_mode = value

    @rx.event
    def set_auto_fit(self, value: bool):
        """Toggle automatic fitting to the container."""
        self.auto_fit = value

    @rx.event
    def report_size(self, size: dict | None):
        """Show the geometry reported back by the fit addon."""
        if isinstance(size, dict) and "cols" in size:
            self.reported = f"{size['cols']} x {size['rows']}"

    @rx.event
    def track_size(self, cols: int, rows: int):
        """Keep the sliders in step with the actual terminal size."""
        self.reported = f"{cols} x {rows}"


def labelled(label: str, control: rx.Component, hint: str = "") -> rx.Component:
    """A control with a label above it."""
    return rx.vstack(
        rx.text(label, size="1", weight="medium", color="var(--gray-11)"),
        control,
        rx.cond(hint != "", rx.text(hint, size="1", color="var(--gray-9)")),
        spacing="1",
        align="start",
        width="100%",
    )


def controls() -> rx.Component:
    """The whole control panel."""
    return rx.grid(
        labelled(
            "Theme",
            rx.select(
                THEME_NAMES,
                value=PlaygroundState.theme_name,
                on_change=PlaygroundState.set_theme_name,
                width="100%",
            ),
        ),
        labelled(
            "Renderer",
            rx.select(
                ["dom", "webgl", "canvas"],
                value=PlaygroundState.renderer,
                on_change=PlaygroundState.set_renderer,
                width="100%",
            ),
            "canvas needs @xterm/addon-canvas installed",
        ),
        labelled(
            "Cursor style",
            rx.select(
                ["block", "underline", "bar"],
                value=PlaygroundState.cursor_style,
                on_change=PlaygroundState.set_cursor_style,
                width="100%",
            ),
        ),
        labelled(
            "Cursor when unfocused",
            rx.select(
                ["outline", "block", "bar", "underline", "none"],
                value=PlaygroundState.cursor_inactive_style,
                on_change=PlaygroundState.set_cursor_inactive_style,
                width="100%",
            ),
        ),
        labelled(
            "Font size",
            rx.hstack(
                rx.slider(
                    min=8,
                    max=32,
                    step=1,
                    value=[PlaygroundState.font_size],
                    on_change=PlaygroundState.set_font_size,
                    width="100%",
                ),
                rx.badge(PlaygroundState.font_size),
                align="center",
                width="100%",
            ),
        ),
        labelled(
            "Line height",
            rx.hstack(
                rx.slider(
                    min=1.0,
                    max=2.0,
                    step=0.05,
                    value=[PlaygroundState.line_height],
                    on_change=PlaygroundState.set_line_height,
                    width="100%",
                ),
                rx.badge(PlaygroundState.line_height.to_string()),
                align="center",
                width="100%",
            ),
        ),
        labelled(
            "Letter spacing",
            rx.hstack(
                rx.slider(
                    min=0,
                    max=5,
                    step=0.5,
                    value=[PlaygroundState.letter_spacing],
                    on_change=PlaygroundState.set_letter_spacing,
                    width="100%",
                ),
                rx.badge(PlaygroundState.letter_spacing.to_string()),
                align="center",
                width="100%",
            ),
        ),
        labelled(
            "Minimum contrast ratio",
            rx.hstack(
                rx.slider(
                    min=1,
                    max=21,
                    step=1,
                    value=[PlaygroundState.minimum_contrast_ratio],
                    on_change=PlaygroundState.set_minimum_contrast_ratio,
                    width="100%",
                ),
                rx.badge(PlaygroundState.minimum_contrast_ratio.to_string()),
                align="center",
                width="100%",
            ),
        ),
        labelled(
            "Scrollback",
            rx.hstack(
                rx.slider(
                    min=0,
                    max=10000,
                    step=500,
                    value=[PlaygroundState.scrollback],
                    on_change=PlaygroundState.set_scrollback,
                    width="100%",
                ),
                rx.badge(PlaygroundState.scrollback),
                align="center",
                width="100%",
            ),
        ),
        labelled(
            "Font family",
            rx.input(
                value=PlaygroundState.font_family,
                on_change=PlaygroundState.set_font_family,
                width="100%",
            ),
        ),
        rx.vstack(
            rx.checkbox(
                "Cursor blink",
                checked=PlaygroundState.cursor_blink,
                on_change=PlaygroundState.set_cursor_blink,
            ),
            rx.checkbox(
                "Bold text in bright colours",
                checked=PlaygroundState.draw_bold_bright,
                on_change=PlaygroundState.set_draw_bold_bright,
            ),
            rx.checkbox(
                "Allow transparency",
                checked=PlaygroundState.allow_transparency,
                on_change=PlaygroundState.set_allow_transparency,
            ),
            rx.checkbox(
                "Screen reader mode",
                checked=PlaygroundState.screen_reader_mode,
                on_change=PlaygroundState.set_screen_reader_mode,
            ),
            rx.checkbox(
                "Auto fit to container",
                checked=PlaygroundState.auto_fit,
                on_change=PlaygroundState.set_auto_fit,
            ),
            spacing="2",
            align="start",
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
        spacing="4",
        width="100%",
    )


def index() -> rx.Component:
    """The playground page."""
    return page_layout(
        "Playground",
        "Every prop below maps to an xterm.js terminal option and is applied "
        "in place - the terminal is never re-created, so the buffer survives.",
        controls(),
        rx.hstack(
            rx.button(
                rx.icon("maximize-2", size=16),
                "Fit now",
                on_click=term.fit(callback=PlaygroundState.report_size),
                variant="soft",
            ),
            rx.button(
                rx.icon("rotate-ccw", size=16),
                "Reset",
                on_click=[term.reset(), term.write(SAMPLE)],
                variant="soft",
            ),
            rx.button(
                rx.icon("type", size=16),
                "Redraw sample",
                on_click=term.write(SAMPLE),
                variant="soft",
            ),
            rx.spacer(),
            rx.cond(
                PlaygroundState.reported != "",
                rx.badge(PlaygroundState.reported, variant="outline"),
            ),
            width="100%",
            align="center",
            spacing="3",
            wrap="wrap",
        ),
        rx.box(
            xterm(
                terminal_id="playground",
                theme=PlaygroundState.theme,
                addons=["fit", "web-links", "unicode-graphemes", "ligatures"],
                renderer=PlaygroundState.renderer,
                font_family=PlaygroundState.font_family,
                font_size=PlaygroundState.font_size,
                line_height=PlaygroundState.line_height,
                letter_spacing=PlaygroundState.letter_spacing,
                cursor_style=PlaygroundState.cursor_style,
                cursor_inactive_style=PlaygroundState.cursor_inactive_style,
                cursor_blink=PlaygroundState.cursor_blink,
                scrollback=PlaygroundState.scrollback,
                minimum_contrast_ratio=PlaygroundState.minimum_contrast_ratio,
                draw_bold_text_in_bright_colors=PlaygroundState.draw_bold_bright,
                allow_transparency=PlaygroundState.allow_transparency,
                screen_reader_mode=PlaygroundState.screen_reader_mode,
                auto_fit=PlaygroundState.auto_fit,
                cols=PlaygroundState.cols,
                rows=PlaygroundState.rows,
                initial_text=SAMPLE,
                read_only=True,
                on_resize=PlaygroundState.track_size,
            ),
            height="420px",
            width="100%",
            **TERMINAL_FRAME,
        ),
    )
