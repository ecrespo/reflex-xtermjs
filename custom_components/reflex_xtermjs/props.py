"""Typed option objects for the xterm.js Reflex component.

Every class here is an ``rx.PropsBase`` subclass, so Python ``snake_case``
fields are emitted as the ``camelCase`` keys xterm.js expects, and unset
(``None``) fields are dropped instead of overriding an xterm default with
``null``.
"""

from __future__ import annotations

import reflex as rx

__all__ = [
    "ImageOptions",
    "LigatureOptions",
    "OverviewRulerOptions",
    "SearchDecorationOptions",
    "SearchOptions",
    "WindowsPty",
    "XTermTheme",
]


class XTermTheme(rx.PropsBase):
    """Colour theme for the terminal (xterm.js ``ITheme``).

    Every value is a CSS colour string. ``extended_ansi`` carries the
    256-colour palette entries 16-255.
    """

    background: str | None = None
    foreground: str | None = None
    cursor: str | None = None
    cursor_accent: str | None = None
    selection_background: str | None = None
    selection_foreground: str | None = None
    selection_inactive_background: str | None = None
    scrollbar_slider_background: str | None = None
    scrollbar_slider_hover_background: str | None = None
    scrollbar_slider_active_background: str | None = None
    overview_ruler_border: str | None = None

    black: str | None = None
    red: str | None = None
    green: str | None = None
    yellow: str | None = None
    blue: str | None = None
    magenta: str | None = None
    cyan: str | None = None
    white: str | None = None

    bright_black: str | None = None
    bright_red: str | None = None
    bright_green: str | None = None
    bright_yellow: str | None = None
    bright_blue: str | None = None
    bright_magenta: str | None = None
    bright_cyan: str | None = None
    bright_white: str | None = None

    extended_ansi: list[str] | None = None


class SearchDecorationOptions(rx.PropsBase):
    """Highlight colours used by the search addon."""

    match_background: str | None = None
    match_border: str | None = None
    match_overview_ruler: str | None = None
    active_match_background: str | None = None
    active_match_border: str | None = None
    active_match_color_overview_ruler: str | None = None


class SearchOptions(rx.PropsBase):
    """Default search behaviour (xterm.js ``ISearchOptions``)."""

    regex: bool | None = None
    whole_word: bool | None = None
    case_sensitive: bool | None = None
    incremental: bool | None = None
    decorations: SearchDecorationOptions | None = None


class ImageOptions(rx.PropsBase):
    """Options for ``@xterm/addon-image`` (SIXEL / iTerm / Kitty graphics)."""

    enable_size_reports: bool | None = None
    pixel_limit: int | None = None
    storage_limit: int | None = None
    show_placeholder: bool | None = None
    sixel_support: bool | None = None
    sixel_scrolling: bool | None = None
    sixel_palette_limit: int | None = None
    sixel_size_limit: int | None = None
    iip_support: bool | None = None
    iip_size_limit: int | None = None
    kitty_support: bool | None = None
    kitty_size_limit: int | None = None


class LigatureOptions(rx.PropsBase):
    """Options for ``@xterm/addon-ligatures``."""

    fallback_ligatures: list[str] | None = None
    font_feature_settings: str | None = None


class OverviewRulerOptions(rx.PropsBase):
    """Geometry of the decoration overview ruler."""

    width: int | None = None
    show_top_border: bool | None = None
    show_bottom_border: bool | None = None


class WindowsPty(rx.PropsBase):
    """Describes the Windows pty backend feeding the terminal."""

    backend: str | None = None
    build_number: int | None = None
