"""Drive a mounted terminal from Reflex event handlers.

The React shim publishes an imperative API for every mounted terminal on
``window.__reflexXterm[terminal_id]``. :class:`XTermAPI` turns that API into
Reflex event specs built on ``rx.call_script``, so a backend handler can write
to, clear, search or resize a terminal without re-rendering the component::

    term = XTermAPI("shell")

    class State(rx.State):
        @rx.event
        def greet(self):
            return term.writeln("hello from the backend")

    rx.button("Greet", on_click=State.greet)

Calls that produce a value (``get_selection``, ``serialize``, ``fit``, ...)
accept a ``callback`` event handler which receives the result::

    term.serialize(callback=State.store_dump)
"""

from __future__ import annotations

from typing import Any

import reflex as rx
from reflex.vars import Var

__all__ = ["XTermAPI"]


def _js(value: Any) -> str:
    """Render a Python value (or Var) as a JavaScript expression."""
    if isinstance(value, Var):
        return str(value)
    return str(Var.create(value))


class XTermAPI:
    """Imperative handle on a terminal rendered with the same ``terminal_id``.

    Args:
        terminal_id: The ``terminal_id`` prop of the target terminal. May be a
            plain string or a Reflex ``Var`` when the id is computed at
            runtime.
    """

    def __init__(self, terminal_id: str | Var[str] = "default") -> None:
        self.terminal_id = terminal_id

    # -- plumbing --------------------------------------------------------

    @property
    def _handle(self) -> str:
        """JS expression resolving to the terminal API object, or undefined."""
        return f"(window.__reflexXterm && window.__reflexXterm[{_js(self.terminal_id)}])"

    def call(
        self,
        method: str,
        *args: Any,
        callback: Any = None,
    ) -> rx.event.EventSpec:
        """Call any method of the underlying JS API.

        Args:
            method: Name of the method on the terminal API object.
            *args: Arguments, serialized as JavaScript values.
            callback: Event handler receiving the return value.

        Returns:
            An event spec that runs the call in the browser.
        """
        rendered = ", ".join(_js(arg) for arg in args)
        return rx.call_script(
            f"{self._handle}?.{method}({rendered})",
            callback=callback,
        )

    # -- output ----------------------------------------------------------

    def write(self, data: str | Var[str]) -> rx.event.EventSpec:
        """Write raw data (ANSI escapes included) to the terminal."""
        return self.call("write", data)

    def writeln(self, data: str | Var[str]) -> rx.event.EventSpec:
        """Write data followed by a line break."""
        return self.call("writeln", data)

    def clear(self) -> rx.event.EventSpec:
        """Clear the viewport, keeping the prompt line."""
        return self.call("clear")

    def reset(self) -> rx.event.EventSpec:
        """Reset the terminal to its initial state."""
        return self.call("reset")

    def refresh(self, start: int | None = None, end: int | None = None):
        """Force a redraw of the given row range."""
        return self.call("refresh", start, end)

    # -- input -----------------------------------------------------------

    def input(self, data: str | Var[str], was_user_input: bool = True) -> rx.event.EventSpec:
        """Feed data to the terminal as if the user had typed it."""
        return self.call("input", data, was_user_input)

    def paste(self, data: str | Var[str]) -> rx.event.EventSpec:
        """Paste data into the terminal."""
        return self.call("paste", data)

    def focus(self) -> rx.event.EventSpec:
        """Move keyboard focus to the terminal."""
        return self.call("focus")

    def blur(self) -> rx.event.EventSpec:
        """Remove keyboard focus from the terminal."""
        return self.call("blur")

    # -- geometry --------------------------------------------------------

    def fit(self, callback: Any = None) -> rx.event.EventSpec:
        """Resize the terminal to its container; returns ``{cols, rows}``."""
        return self.call("fit", callback=callback)

    def propose_dimensions(self, callback: Any = None) -> rx.event.EventSpec:
        """Report the size the fit addon would choose, without applying it."""
        return self.call("proposeDimensions", callback=callback)

    def resize(self, cols: int | Var[int], rows: int | Var[int]):
        """Resize the terminal to an explicit geometry."""
        return self.call("resize", cols, rows)

    def get_size(self, callback: Any = None) -> rx.event.EventSpec:
        """Report the current ``{cols, rows}``."""
        return self.call("getSize", callback=callback)

    # -- options ---------------------------------------------------------

    def set_option(self, name: str, value: Any) -> rx.event.EventSpec:
        """Set a single xterm.js option (camelCase name)."""
        return self.call("setOption", name, value)

    def set_options(self, options: dict[str, Any] | Var) -> rx.event.EventSpec:
        """Merge a dict of xterm.js options into the terminal."""
        return self.call("setOptions", options)

    def get_option(self, name: str, callback: Any = None) -> rx.event.EventSpec:
        """Read a single xterm.js option."""
        return self.call("getOption", name, callback=callback)

    def set_renderer(self, renderer: str | Var[str]) -> rx.event.EventSpec:
        """Switch the renderer between ``dom``, ``webgl`` and ``canvas``."""
        return self.call("setRenderer", renderer)

    def load_addons(self, names: list[str] | Var) -> rx.event.EventSpec:
        """Load additional addons at runtime."""
        return self.call("loadAddons", names)

    def clear_texture_atlas(self) -> rx.event.EventSpec:
        """Drop the glyph texture atlas (useful after a font change)."""
        return self.call("clearTextureAtlas")

    # -- selection -------------------------------------------------------

    def select_all(self) -> rx.event.EventSpec:
        """Select the whole buffer."""
        return self.call("selectAll")

    def select(self, column: int, row: int, length: int) -> rx.event.EventSpec:
        """Select ``length`` cells starting at ``(column, row)``."""
        return self.call("select", column, row, length)

    def clear_selection(self) -> rx.event.EventSpec:
        """Drop the current selection."""
        return self.call("clearSelection")

    def get_selection(self, callback: Any = None) -> rx.event.EventSpec:
        """Read the selected text."""
        return self.call("getSelection", callback=callback)

    # -- scrolling -------------------------------------------------------

    def scroll_to_top(self) -> rx.event.EventSpec:
        """Scroll to the top of the scrollback."""
        return self.call("scrollToTop")

    def scroll_to_bottom(self) -> rx.event.EventSpec:
        """Scroll to the bottom of the scrollback."""
        return self.call("scrollToBottom")

    def scroll_to_line(self, line: int | Var[int]) -> rx.event.EventSpec:
        """Scroll so that ``line`` is at the top of the viewport."""
        return self.call("scrollToLine", line)

    def scroll_lines(self, amount: int | Var[int]) -> rx.event.EventSpec:
        """Scroll by a number of lines (negative scrolls up)."""
        return self.call("scrollLines", amount)

    def scroll_pages(self, pages: int | Var[int]) -> rx.event.EventSpec:
        """Scroll by a number of pages (negative scrolls up)."""
        return self.call("scrollPages", pages)

    # -- search (needs the "search" addon) -------------------------------

    def find_next(
        self,
        needle: str | Var[str],
        options: dict[str, Any] | Var | None = None,
        callback: Any = None,
    ) -> rx.event.EventSpec:
        """Find the next occurrence of ``needle``."""
        return self.call("findNext", needle, options or {}, callback=callback)

    def find_previous(
        self,
        needle: str | Var[str],
        options: dict[str, Any] | Var | None = None,
        callback: Any = None,
    ) -> rx.event.EventSpec:
        """Find the previous occurrence of ``needle``."""
        return self.call("findPrevious", needle, options or {}, callback=callback)

    def clear_search_decorations(self) -> rx.event.EventSpec:
        """Remove search highlights."""
        return self.call("clearSearchDecorations")

    # -- serialize (needs the "serialize" addon) -------------------------

    def serialize(
        self,
        options: dict[str, Any] | Var | None = None,
        callback: Any = None,
    ) -> rx.event.EventSpec:
        """Dump the buffer as a string with ANSI escapes."""
        return self.call("serialize", options or {}, callback=callback)

    def serialize_as_html(
        self,
        options: dict[str, Any] | Var | None = None,
        callback: Any = None,
    ) -> rx.event.EventSpec:
        """Dump the buffer as styled HTML."""
        return self.call("serializeAsHtml", options or {}, callback=callback)

    # -- websocket -------------------------------------------------------

    def connect(self, url: str | Var[str]) -> rx.event.EventSpec:
        """Attach the terminal to a WebSocket endpoint."""
        return self.call("connect", url)

    def disconnect(self) -> rx.event.EventSpec:
        """Detach from the current WebSocket."""
        return self.call("disconnect")

    def send(self, data: str | Var[str], callback: Any = None):
        """Send data over the attached socket; reports whether it was sent."""
        return self.call("send", data, callback=callback)

    def is_connected(self, callback: Any = None) -> rx.event.EventSpec:
        """Report whether the socket is open."""
        return self.call("isConnected", callback=callback)
