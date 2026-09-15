"""Tests for the bundled colour themes."""

from __future__ import annotations

import pytest
from reflex_xtermjs import THEME_NAMES, THEMES, get_theme

ANSI_FIELDS = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
)


def test_theme_names_are_sorted_and_complete():
    """``THEME_NAMES`` mirrors ``THEMES``."""
    assert THEME_NAMES == sorted(THEMES)
    assert len(THEME_NAMES) >= 10


@pytest.mark.parametrize("name", sorted(THEMES))
def test_theme_defines_a_full_palette(name: str):
    """Each theme sets a background, a foreground and all 16 ANSI colours."""
    theme = THEMES[name]
    assert theme.background and theme.background.startswith("#")
    assert theme.foreground and theme.foreground.startswith("#")
    for field in ANSI_FIELDS:
        value = getattr(theme, field)
        assert value and value.startswith("#"), f"{name}.{field}"
        assert len(value) == 7, f"{name}.{field} = {value}"


def test_get_theme_returns_the_same_object():
    """Lookup by name is a plain dict access."""
    assert get_theme("nord") is THEMES["nord"]


def test_get_theme_reports_the_available_names():
    """An unknown name fails with a helpful message."""
    with pytest.raises(KeyError, match="Available themes"):
        get_theme("no-such-theme")


def test_theme_dict_is_camel_cased_and_dense():
    """Serialization matches xterm.js' ITheme and skips unset fields."""
    data = THEMES["nord"].dict()
    assert "selectionBackground" in data
    assert "brightWhite" in data
    assert all(value is not None for value in data.values())
