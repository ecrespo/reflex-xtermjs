"""Ready-made colour themes for the xterm.js Reflex component.

Each entry is an :class:`~reflex_xtermjs.props.XTermTheme` instance, so it can
be handed straight to ``xterm(theme=...)``. Use :func:`get_theme` to look one
up by name, or copy one and override individual colours::

    from reflex_xtermjs import THEMES, xterm

    my_theme = XTermTheme(**{**THEMES["dracula"].dict(), "background": "#1a1a24"})
    xterm(theme=my_theme)
"""

from __future__ import annotations

from .props import XTermTheme

__all__ = ["THEMES", "THEME_NAMES", "get_theme"]


def _theme(
    background: str,
    foreground: str,
    cursor: str,
    selection: str,
    normal: tuple[str, str, str, str, str, str, str, str],
    bright: tuple[str, str, str, str, str, str, str, str],
) -> XTermTheme:
    """Build a theme from a background/foreground pair and two ANSI rows."""
    black, red, green, yellow, blue, magenta, cyan, white = normal
    (
        bright_black,
        bright_red,
        bright_green,
        bright_yellow,
        bright_blue,
        bright_magenta,
        bright_cyan,
        bright_white,
    ) = bright
    return XTermTheme(
        background=background,
        foreground=foreground,
        cursor=cursor,
        cursor_accent=background,
        selection_background=selection,
        black=black,
        red=red,
        green=green,
        yellow=yellow,
        blue=blue,
        magenta=magenta,
        cyan=cyan,
        white=white,
        bright_black=bright_black,
        bright_red=bright_red,
        bright_green=bright_green,
        bright_yellow=bright_yellow,
        bright_blue=bright_blue,
        bright_magenta=bright_magenta,
        bright_cyan=bright_cyan,
        bright_white=bright_white,
    )


THEMES: dict[str, XTermTheme] = {
    "vscode-dark": _theme(
        "#1e1e1e",
        "#cccccc",
        "#ffffff",
        "#264f78",
        ("#000000", "#cd3131", "#0dbc79", "#e5e510", "#2472c8", "#bc3fbc", "#11a8cd", "#e5e5e5"),
        ("#666666", "#f14c4c", "#23d18b", "#f5f543", "#3b8eea", "#d670d6", "#29b8db", "#e5e5e5"),
    ),
    "dracula": _theme(
        "#282a36",
        "#f8f8f2",
        "#f8f8f2",
        "#44475a",
        ("#21222c", "#ff5555", "#50fa7b", "#f1fa8c", "#bd93f9", "#ff79c6", "#8be9fd", "#f8f8f2"),
        ("#6272a4", "#ff6e6e", "#69ff94", "#ffffa5", "#d6acff", "#ff92df", "#a4ffff", "#ffffff"),
    ),
    "nord": _theme(
        "#2e3440",
        "#d8dee9",
        "#d8dee9",
        "#434c5e",
        ("#3b4252", "#bf616a", "#a3be8c", "#ebcb8b", "#81a1c1", "#b48ead", "#88c0d0", "#e5e9f0"),
        ("#4c566a", "#bf616a", "#a3be8c", "#ebcb8b", "#81a1c1", "#b48ead", "#8fbcbb", "#eceff4"),
    ),
    "solarized-dark": _theme(
        "#002b36",
        "#839496",
        "#93a1a1",
        "#073642",
        ("#073642", "#dc322f", "#859900", "#b58900", "#268bd2", "#d33682", "#2aa198", "#eee8d5"),
        ("#002b36", "#cb4b16", "#586e75", "#657b83", "#839496", "#6c71c4", "#93a1a1", "#fdf6e3"),
    ),
    "solarized-light": _theme(
        "#fdf6e3",
        "#657b83",
        "#586e75",
        "#eee8d5",
        ("#073642", "#dc322f", "#859900", "#b58900", "#268bd2", "#d33682", "#2aa198", "#eee8d5"),
        ("#002b36", "#cb4b16", "#586e75", "#657b83", "#839496", "#6c71c4", "#93a1a1", "#fdf6e3"),
    ),
    "gruvbox-dark": _theme(
        "#282828",
        "#ebdbb2",
        "#ebdbb2",
        "#504945",
        ("#282828", "#cc241d", "#98971a", "#d79921", "#458588", "#b16286", "#689d6a", "#a89984"),
        ("#928374", "#fb4934", "#b8bb26", "#fabd2f", "#83a598", "#d3869b", "#8ec07c", "#ebdbb2"),
    ),
    "one-dark": _theme(
        "#282c34",
        "#abb2bf",
        "#528bff",
        "#3e4451",
        ("#282c34", "#e06c75", "#98c379", "#e5c07b", "#61afef", "#c678dd", "#56b6c2", "#abb2bf"),
        ("#5c6370", "#e06c75", "#98c379", "#e5c07b", "#61afef", "#c678dd", "#56b6c2", "#ffffff"),
    ),
    "tokyo-night": _theme(
        "#1a1b26",
        "#a9b1d6",
        "#c0caf5",
        "#33467c",
        ("#15161e", "#f7768e", "#9ece6a", "#e0af68", "#7aa2f7", "#bb9af7", "#7dcfff", "#a9b1d6"),
        ("#414868", "#f7768e", "#9ece6a", "#e0af68", "#7aa2f7", "#bb9af7", "#7dcfff", "#c0caf5"),
    ),
    "catppuccin-mocha": _theme(
        "#1e1e2e",
        "#cdd6f4",
        "#f5e0dc",
        "#585b70",
        ("#45475a", "#f38ba8", "#a6e3a1", "#f9e2af", "#89b4fa", "#f5c2e7", "#94e2d5", "#bac2de"),
        ("#585b70", "#f38ba8", "#a6e3a1", "#f9e2af", "#89b4fa", "#f5c2e7", "#94e2d5", "#a6adc8"),
    ),
    "monokai": _theme(
        "#272822",
        "#f8f8f2",
        "#f8f8f0",
        "#49483e",
        ("#272822", "#f92672", "#a6e22e", "#f4bf75", "#66d9ef", "#ae81ff", "#a1efe4", "#f8f8f2"),
        ("#75715e", "#f92672", "#a6e22e", "#f4bf75", "#66d9ef", "#ae81ff", "#a1efe4", "#f9f8f5"),
    ),
    "github-dark": _theme(
        "#0d1117",
        "#c9d1d9",
        "#58a6ff",
        "#264f78",
        ("#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"),
        ("#6e7681", "#ffa198", "#56d364", "#e3b341", "#79c0ff", "#d2a8ff", "#56d4dd", "#f0f6fc"),
    ),
    "github-light": _theme(
        "#ffffff",
        "#24292f",
        "#0969da",
        "#add6ff",
        ("#24292f", "#cf222e", "#116329", "#4d2d00", "#0969da", "#8250df", "#1b7c83", "#6e7781"),
        ("#57606a", "#a40e26", "#1a7f37", "#633c01", "#218bff", "#a475f9", "#3192aa", "#8c959f"),
    ),
}

THEME_NAMES: list[str] = sorted(THEMES)


def get_theme(name: str) -> XTermTheme:
    """Return a built-in theme by name.

    Args:
        name: One of :data:`THEME_NAMES`.

    Returns:
        The matching theme.

    Raises:
        KeyError: If no built-in theme has that name.
    """
    try:
        return THEMES[name]
    except KeyError as exc:
        msg = f"Unknown theme {name!r}. Available themes: {', '.join(THEME_NAMES)}"
        raise KeyError(msg) from exc
