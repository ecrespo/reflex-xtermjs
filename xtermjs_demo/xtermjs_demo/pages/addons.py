"""Page 4 - the addon surface: search, serialize, links and progress."""

from __future__ import annotations

import reflex as rx
from reflex_xtermjs import THEMES, SearchOptions, XTermAPI, xterm

from ..shared import TERMINAL_FRAME, page_layout

term = XTermAPI("addons")

LOG_LINES = [
    "\x1b[2m2026-09-15 08:14:02\x1b[0m \x1b[32mINFO \x1b[0m  starting reflex backend",
    "\x1b[2m2026-09-15 08:14:02\x1b[0m \x1b[32mINFO \x1b[0m  docs at https://xtermjs.org/docs/",
    "\x1b[2m2026-09-15 08:14:03\x1b[0m \x1b[32mINFO \x1b[0m  compiled 4 pages",
    "\x1b[2m2026-09-15 08:14:03\x1b[0m \x1b[33mWARN \x1b[0m  webgl context is software backed",
    "\x1b[2m2026-09-15 08:14:04\x1b[0m \x1b[32mINFO \x1b[0m  source https://github.com/xtermjs/xterm.js",
    "\x1b[2m2026-09-15 08:14:05\x1b[0m \x1b[31mERROR\x1b[0m  connection refused on port 5432",
    "\x1b[2m2026-09-15 08:14:06\x1b[0m \x1b[32mINFO \x1b[0m  retrying in 2s",
    "\x1b[2m2026-09-15 08:14:08\x1b[0m \x1b[32mINFO \x1b[0m  database connected",
    "\x1b[2m2026-09-15 08:14:09\x1b[0m \x1b[31mERROR\x1b[0m  migration 0042 failed",
    "\x1b[2m2026-09-15 08:14:10\x1b[0m \x1b[32mINFO \x1b[0m  rolled back cleanly",
]

SAMPLE_LOG = "".join(f"{line}\r\n" for line in LOG_LINES)


class AddonState(rx.State):
    """Search, serialize and progress state."""

    needle: str = "ERROR"
    case_sensitive: bool = False
    whole_word: bool = False
    use_regex: bool = False
    result_index: int = -1
    result_count: int = 0

    dump: str = ""
    dump_kind: str = ""

    last_link: str = ""
    progress_state: int = 0
    progress_value: int = 0

    @rx.var
    def search_options(self) -> dict:
        """Search options as xterm.js expects them."""
        return {
            "caseSensitive": self.case_sensitive,
            "wholeWord": self.whole_word,
            "regex": self.use_regex,
        }

    @rx.var
    def matches_label(self) -> str:
        """Human-readable match counter."""
        if self.result_count == 0:
            return "no matches"
        return f"{self.result_index + 1} of {self.result_count}"

    @rx.event
    def set_needle(self, value: str):
        """Update the search term."""
        self.needle = value

    @rx.event
    def set_case_sensitive(self, value: bool):
        """Toggle case sensitivity."""
        self.case_sensitive = value

    @rx.event
    def set_whole_word(self, value: bool):
        """Toggle whole-word matching."""
        self.whole_word = value

    @rx.event
    def set_use_regex(self, value: bool):
        """Toggle regular-expression matching."""
        self.use_regex = value

    @rx.event
    def clear_dump(self):
        """Drop the serialized buffer."""
        self.dump = ""
        self.dump_kind = ""

    @rx.event
    def on_results(self, result_index: int, result_count: int):
        """Track the search addon's result event."""
        self.result_index = result_index
        self.result_count = result_count

    @rx.event
    def find_next(self):
        """Search forwards."""
        return term.find_next(self.needle, self.search_options)

    @rx.event
    def find_previous(self):
        """Search backwards."""
        return term.find_previous(self.needle, self.search_options)

    @rx.event
    def store_dump(self, value: str):
        """Keep the serialized buffer for display."""
        self.dump = value or ""

    @rx.event
    def dump_text(self):
        """Serialize the buffer with ANSI escapes."""
        self.dump_kind = "text (ANSI)"
        return term.serialize(callback=AddonState.store_dump)

    @rx.event
    def dump_html(self):
        """Serialize the buffer as styled HTML."""
        self.dump_kind = "html"
        return term.serialize_as_html(callback=AddonState.store_dump)

    @rx.event
    def on_link(self, uri: str):
        """Record a clicked link instead of opening it."""
        self.last_link = uri

    @rx.event
    def on_progress(self, state: int, value: int):
        """Track OSC 9;4 progress reports."""
        self.progress_state = state
        self.progress_value = value

    @rx.event
    def fill_log(self):
        """Print the sample log again."""
        return term.write(SAMPLE_LOG)

    @rx.event
    def emit_progress(self):
        """Emit a ConEmu progress sequence the progress addon understands."""
        return term.write("\x1b]9;4;1;65\x07\x1b[2mprogress set to 65%\x1b[0m\r\n")


def search_panel() -> rx.Component:
    """Search controls backed by @xterm/addon-search."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("search", size=16),
                rx.heading("Search", size="3"),
                align="center",
                spacing="2",
            ),
            rx.hstack(
                rx.input(
                    value=AddonState.needle,
                    on_change=AddonState.set_needle,
                    placeholder="search the buffer",
                    width="100%",
                ),
                rx.button(
                    rx.icon("chevron-up", size=16),
                    on_click=AddonState.find_previous,
                    variant="soft",
                ),
                rx.button(
                    rx.icon("chevron-down", size=16),
                    on_click=AddonState.find_next,
                    variant="soft",
                ),
                width="100%",
                spacing="2",
            ),
            rx.hstack(
                rx.checkbox(
                    "Aa",
                    checked=AddonState.case_sensitive,
                    on_change=AddonState.set_case_sensitive,
                ),
                rx.checkbox(
                    "whole word",
                    checked=AddonState.whole_word,
                    on_change=AddonState.set_whole_word,
                ),
                rx.checkbox(
                    "regex",
                    checked=AddonState.use_regex,
                    on_change=AddonState.set_use_regex,
                ),
                rx.spacer(),
                rx.badge(AddonState.matches_label, variant="soft"),
                width="100%",
                align="center",
                spacing="3",
            ),
            rx.button(
                "Clear highlights",
                on_click=term.clear_search_decorations(),
                variant="ghost",
                size="1",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def serialize_panel() -> rx.Component:
    """Serialize controls backed by @xterm/addon-serialize."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("file-code", size=16),
                rx.heading("Serialize", size="3"),
                rx.spacer(),
                rx.cond(
                    AddonState.dump_kind != "",
                    rx.badge(AddonState.dump_kind, variant="outline"),
                ),
                align="center",
                spacing="2",
                width="100%",
            ),
            rx.text(
                "Pull the whole buffer back into Python - handy for saving a "
                "session transcript or attaching terminal output to a report.",
                size="1",
                color="var(--gray-11)",
            ),
            rx.hstack(
                rx.button("As ANSI text", on_click=AddonState.dump_text, variant="soft"),
                rx.button("As HTML", on_click=AddonState.dump_html, variant="soft"),
                rx.button(
                    "Clear",
                    on_click=AddonState.clear_dump,
                    variant="ghost",
                ),
                spacing="2",
            ),
            rx.cond(
                AddonState.dump != "",
                rx.scroll_area(
                    rx.code_block(
                        AddonState.dump,
                        language="bash",
                        wrap_long_lines=True,
                    ),
                    height="180px",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def misc_panel() -> rx.Component:
    """Web-links and progress addons."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("link", size=16),
                rx.heading("Links and progress", size="3"),
                align="center",
                spacing="2",
            ),
            rx.text(
                "URLs in the buffer are detected by @xterm/addon-web-links. "
                "This page intercepts the click and reports it to the backend "
                "instead of opening a tab.",
                size="1",
                color="var(--gray-11)",
            ),
            rx.cond(
                AddonState.last_link != "",
                rx.callout(AddonState.last_link, icon="link", size="1"),
                rx.text("no link clicked yet", size="1", color="var(--gray-9)"),
            ),
            rx.divider(),
            rx.hstack(
                rx.button(
                    "Emit OSC 9;4 progress",
                    on_click=AddonState.emit_progress,
                    variant="soft",
                ),
                rx.badge(
                    f"state {AddonState.progress_state} / {AddonState.progress_value}%",
                    variant="outline",
                ),
                align="center",
                spacing="3",
                wrap="wrap",
            ),
            rx.progress(value=AddonState.progress_value, width="100%"),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def index() -> rx.Component:
    """The addons page."""
    return page_layout(
        "Addons",
        "Search, serialize, web-links and progress, each driven from Python "
        "through the same imperative API.",
        rx.hstack(
            rx.button(
                rx.icon("list-restart", size=16),
                "Print sample log",
                on_click=AddonState.fill_log,
                variant="soft",
            ),
            rx.button(
                rx.icon("eraser", size=16),
                "Clear",
                on_click=term.clear(),
                variant="soft",
            ),
            rx.button(
                rx.icon("text-select", size=16),
                "Select all",
                on_click=term.select_all(),
                variant="soft",
            ),
            spacing="2",
            wrap="wrap",
        ),
        rx.box(
            xterm(
                terminal_id="addons",
                theme=THEMES["github-dark"].dict(),
                addons=[
                    "fit",
                    "search",
                    "serialize",
                    "web-links",
                    "clipboard",
                    "progress",
                    "unicode-graphemes",
                ],
                renderer="webgl",
                font_size=13,
                scrollback=2000,
                read_only=True,
                initial_text=SAMPLE_LOG,
                search_options=SearchOptions(
                    decorations={
                        "match_background": "#ffd33d55",
                        "match_overview_ruler": "#ffd33d",
                        "active_match_background": "#ff7b72aa",
                        "active_match_color_overview_ruler": "#ff7b72",
                    }
                ),
                on_search_results=AddonState.on_results,
                on_link_click=AddonState.on_link,
                on_progress=AddonState.on_progress,
            ),
            height="360px",
            width="100%",
            **TERMINAL_FRAME,
        ),
        rx.grid(
            search_panel(),
            serialize_panel(),
            misc_panel(),
            columns=rx.breakpoints(initial="1", md="2", lg="3"),
            spacing="4",
            width="100%",
        ),
    )
