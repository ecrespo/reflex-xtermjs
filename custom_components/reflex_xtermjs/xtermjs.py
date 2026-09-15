"""xterm.js terminal emulator as a Reflex custom component.

The component wraps the local React shim in ``xterm_wrapper.jsx``, which owns
the xterm.js ``Terminal`` instance, loads addons, and publishes an imperative
API the Python side reaches through :mod:`reflex_xtermjs.api`.

Because xterm.js needs a real DOM, the component is a ``NoSSRComponent``: the
browser bundle imports it lazily and the server never evaluates it.
"""

from __future__ import annotations

from typing import Any, Literal

import reflex as rx
from reflex.components.component import NoSSRComponent

from .props import (
    ImageOptions,
    LigatureOptions,
    OverviewRulerOptions,
    SearchOptions,
    WindowsPty,
    XTermTheme,
)

__all__ = ["ADDONS", "XTerm", "xterm"]

#: Addon names accepted by the ``addons`` prop.
ADDONS = (
    "fit",
    "search",
    "web-links",
    "serialize",
    "clipboard",
    "unicode11",
    "unicode-graphemes",
    "image",
    "ligatures",
    "progress",
)

AddonName = Literal[
    "fit",
    "search",
    "web-links",
    "serialize",
    "clipboard",
    "unicode11",
    "unicode-graphemes",
    "image",
    "ligatures",
    "progress",
]

CursorStyle = Literal["block", "underline", "bar"]
CursorInactiveStyle = Literal["outline", "block", "bar", "underline", "none"]
LogLevel = Literal["trace", "debug", "info", "warn", "error", "off"]
Renderer = Literal["dom", "webgl", "canvas"]
FontWeight = Literal[
    "normal", "bold", "100", "200", "300", "400", "500", "600", "700", "800", "900"
]

_wrapper = rx.asset("xterm_wrapper.jsx", shared=True)


class XTerm(NoSSRComponent):
    """A full xterm.js terminal.

    Example:
        ```python
        import reflex as rx
        from reflex_xtermjs import THEMES, xterm

        rx.box(
            xterm(
                terminal_id="shell",
                theme=THEMES["dracula"],
                addons=["fit", "search", "web-links"],
                renderer="webgl",
                on_data=State.handle_input,
            ),
            height="420px",
        )
        ```
    """

    library = _wrapper.importable_path
    tag = "XTerm"

    lib_dependencies: list[str] = [
        "@xterm/xterm@6.0.0",
        "@xterm/addon-fit@0.11.0",
        "@xterm/addon-search@0.16.0",
        "@xterm/addon-web-links@0.12.0",
        "@xterm/addon-serialize@0.14.0",
        "@xterm/addon-attach@0.12.0",
        "@xterm/addon-clipboard@0.2.0",
        "@xterm/addon-webgl@0.19.0",
        "@xterm/addon-unicode11@0.9.0",
        "@xterm/addon-unicode-graphemes@0.4.0",
        "@xterm/addon-image@0.9.0",
        "@xterm/addon-ligatures@0.10.0",
        "@xterm/addon-progress@0.2.0",
    ]

    # --- identity ------------------------------------------------------

    # Key used by the imperative API to reach this terminal. Must be unique
    # within a page.
    terminal_id: rx.Var[str] = rx.Var.create("default")

    # --- geometry ------------------------------------------------------

    # Initial column count. Ignored once ``auto_fit`` takes over.
    cols: rx.Var[int]

    # Initial row count. Ignored once ``auto_fit`` takes over.
    rows: rx.Var[int]

    # Resize the terminal to its container using the fit addon.
    auto_fit: rx.Var[bool] = rx.Var.create(True)

    # Debounce applied to container resize events, in milliseconds.
    fit_debounce_ms: rx.Var[int] = rx.Var.create(60)

    # CSS width of the terminal container.
    width: rx.Var[str] = rx.Var.create("100%")

    # CSS height of the terminal container.
    height: rx.Var[str] = rx.Var.create("100%")

    # --- addons and rendering -----------------------------------------

    # Addons to load. See :data:`ADDONS`.
    addons: rx.Var[list[AddonName]] = rx.Var.create(["fit", "web-links"])

    # Renderer backend. ``canvas`` additionally requires
    # ``@xterm/addon-canvas`` to be installed by the app; it falls back to
    # ``dom`` when the package is missing.
    renderer: rx.Var[Renderer] = rx.Var.create("dom")

    # Unicode version activated by the unicode addons.
    unicode_version: rx.Var[str]

    # --- websocket / PTY ----------------------------------------------

    # WebSocket endpoint to attach the terminal to. A path such as
    # ``/pty`` is resolved against the current origin.
    websocket_url: rx.Var[str]

    # Forward terminal input to the socket as well as socket output to the
    # terminal.
    attach_bidirectional: rx.Var[bool] = rx.Var.create(True)

    # Reopen the socket automatically after it closes.
    reconnect: rx.Var[bool] = rx.Var.create(False)

    # Delay before a reconnection attempt, in milliseconds.
    reconnect_delay_ms: rx.Var[int] = rx.Var.create(2000)

    # Send ``{"type": "resize", "cols": .., "rows": ..}`` over the socket
    # whenever the terminal is resized.
    send_resize_on_socket: rx.Var[bool] = rx.Var.create(True)

    # --- content -------------------------------------------------------

    # Text (ANSI escapes allowed) written once when the terminal mounts.
    initial_text: rx.Var[str]

    # Convenience flag that sets ``disable_stdin``.
    read_only: rx.Var[bool] = rx.Var.create(False)

    # --- xterm.js terminal options -------------------------------------

    # Allow addons to use the proposed (unstable) API surface.
    allow_proposed_api: rx.Var[bool]

    # Let the background show through the terminal.
    allow_transparency: rx.Var[bool]

    # Alt+click moves the prompt cursor to the click position.
    alt_click_moves_cursor: rx.Var[bool]

    # Translate lone ``\n`` into ``\r\n``.
    convert_eol: rx.Var[bool]

    # Blink the cursor.
    cursor_blink: rx.Var[bool]

    # Cursor shape while focused.
    cursor_style: rx.Var[CursorStyle]

    # Cursor shape while unfocused.
    cursor_inactive_style: rx.Var[CursorInactiveStyle]

    # Cursor width in pixels when ``cursor_style`` is ``bar``.
    cursor_width: rx.Var[int]

    # Draw box-drawing and block characters with custom glyphs.
    custom_glyphs: rx.Var[bool]

    # Ignore keyboard input.
    disable_stdin: rx.Var[bool]

    # Render bold text using the bright ANSI palette.
    draw_bold_text_in_bright_colors: rx.Var[bool]

    # Modifier key that triggers fast scrolling.
    fast_scroll_modifier: rx.Var[Literal["none", "alt", "ctrl", "shift"]]

    # Scroll multiplier while the fast-scroll modifier is held.
    fast_scroll_sensitivity: rx.Var[int]

    # Font stack. Prefer a monospaced family.
    font_family: rx.Var[str]

    # Font size in pixels.
    font_size: rx.Var[int]

    # Weight used for normal text.
    font_weight: rx.Var[FontWeight]

    # Weight used for bold text.
    font_weight_bold: rx.Var[FontWeight]

    # Ignore bracketed paste mode.
    ignore_bracketed_paste_mode: rx.Var[bool]

    # Extra horizontal spacing between characters, in pixels.
    letter_spacing: rx.Var[float]

    # Line height as a multiplier of the font size.
    line_height: rx.Var[float]

    # Console verbosity of xterm.js itself.
    log_level: rx.Var[LogLevel]

    # On macOS, Option+click forces a selection.
    mac_option_click_forces_selection: rx.Var[bool]

    # On macOS, treat the Option key as Meta.
    mac_option_is_meta: rx.Var[bool]

    # Minimum contrast ratio enforced between foreground and background.
    minimum_contrast_ratio: rx.Var[float]

    # Geometry of the decoration overview ruler.
    overview_ruler: rx.Var[OverviewRulerOptions | dict[str, Any]]

    # Reflow the cursor line when the terminal is resized.
    reflow_cursor_line: rx.Var[bool]

    # Rescale glyphs that overflow their cell.
    rescale_overlapping_glyphs: rx.Var[bool]

    # Right click selects the word under the pointer.
    right_click_selects_word: rx.Var[bool]

    # Optimize the DOM for screen readers.
    screen_reader_mode: rx.Var[bool]

    # Scroll to the bottom on an erase-in-display sequence.
    scroll_on_erase_in_display: rx.Var[bool]

    # Scroll to the bottom whenever the user types.
    scroll_on_user_input: rx.Var[bool]

    # Number of lines scrolled per wheel notch.
    scroll_sensitivity: rx.Var[int]

    # Number of lines kept in the scrollback buffer.
    scrollback: rx.Var[int]

    # Duration of smooth scrolling animations, in milliseconds.
    smooth_scroll_duration: rx.Var[int]

    # Width of a tab stop, in columns.
    tab_stop_width: rx.Var[int]

    # Colour theme.
    theme: rx.Var[XTermTheme | dict[str, Any]]

    # Which DEC window operations the terminal honours.
    window_options: rx.Var[dict[str, bool]]

    # Description of the Windows pty feeding this terminal.
    windows_pty: rx.Var[WindowsPty | dict[str, Any]]

    # Characters treated as word boundaries for double-click selection.
    word_separator: rx.Var[str]

    # --- addon options -------------------------------------------------

    # Defaults merged into every search performed through the API.
    search_options: rx.Var[SearchOptions | dict[str, Any]]

    # Options for the image addon.
    image_options: rx.Var[ImageOptions | dict[str, Any]]

    # Options for the ligatures addon.
    ligature_options: rx.Var[LigatureOptions | dict[str, Any]]

    # --- events --------------------------------------------------------

    # Fired for every piece of user input (keystrokes, paste, mouse codes).
    on_data: rx.EventHandler[lambda data: [data]]

    # Fired for binary (non-UTF8) input.
    on_binary: rx.EventHandler[lambda data: [data]]

    # Fired on each keypress with the produced sequence and a plain
    # description of the keyboard event.
    on_key: rx.EventHandler[lambda key, event: [key, event]]

    # Fired when the program running in the terminal changes the title.
    on_title_change: rx.EventHandler[lambda title: [title]]

    # Fired whenever the terminal geometry changes.
    on_resize: rx.EventHandler[lambda cols, rows: [cols, rows]]

    # Fired on the bell character.
    on_bell: rx.EventHandler[rx.event.no_args_event_spec]

    # Fired on each line feed.
    on_line_feed: rx.EventHandler[rx.event.no_args_event_spec]

    # Fired when the cursor moves.
    on_cursor_move: rx.EventHandler[rx.event.no_args_event_spec]

    # Fired when the viewport scrolls, with the new scroll position.
    on_scroll: rx.EventHandler[lambda position: [position]]

    # Fired when the selection changes, with the selected text.
    on_selection_change: rx.EventHandler[lambda selection: [selection]]

    # Fired after a render pass, with the affected row range.
    on_render: rx.EventHandler[lambda start, end: [start, end]]

    # Fired once a `write` call has been fully parsed.
    on_write_parsed: rx.EventHandler[rx.event.no_args_event_spec]

    # Fired once the terminal is attached to the DOM and sized.
    on_ready: rx.EventHandler[lambda cols, rows: [cols, rows]]

    # Fired by the search addon with the active index and the match count.
    on_search_results: rx.EventHandler[
        lambda result_index, result_count: [result_index, result_count]
    ]

    # Fired by the progress addon (ConEmu OSC 9;4) with state and value.
    on_progress: rx.EventHandler[lambda state, value: [state, value]]

    # Fired when the WebGL context is lost and the renderer falls back.
    on_context_loss: rx.EventHandler[rx.event.no_args_event_spec]

    # Fired when a link detected by the web-links addon is clicked.
    on_link_click: rx.EventHandler[lambda uri: [uri]]

    # Fired when the attached WebSocket opens, with the resolved URL.
    on_socket_open: rx.EventHandler[lambda url: [url]]

    # Fired when the attached WebSocket closes, with close code and reason.
    on_socket_close: rx.EventHandler[lambda code, reason: [code, reason]]

    # Fired when the attached WebSocket errors.
    on_socket_error: rx.EventHandler[lambda message: [message]]

    @classmethod
    def create(cls, *children, **props: Any) -> XTerm:
        """Create a terminal, validating the requested addons.

        Args:
            *children: Ignored; the terminal renders its own container.
            **props: Component props.

        Returns:
            The terminal component.

        Raises:
            ValueError: If ``addons`` contains an unknown addon name.
        """
        addons = props.get("addons")
        if isinstance(addons, (list, tuple)):
            unknown = [name for name in addons if name not in ADDONS]
            if unknown:
                msg = (
                    f"Unknown xterm.js addon(s): {', '.join(map(str, unknown))}. "
                    f"Available addons: {', '.join(ADDONS)}"
                )
                raise ValueError(msg)
        return super().create(*children, **props)  # pyright: ignore[reportReturnType]


xterm = XTerm.create
