"""Tests for the XTerm component wrapper."""

from __future__ import annotations

import pathlib

import pytest
import reflex as rx
from reflex_xtermjs import ADDONS, THEMES, XTerm, xterm
from reflex_xtermjs.props import SearchOptions, XTermTheme


def rendered_props(component: XTerm) -> dict[str, str]:
    """Return the component's rendered props as a ``name -> value`` mapping."""
    props = {}
    for entry in component.render()["props"]:
        name, _, value = entry.partition(":")
        props[name] = value
    return props


def test_wrapper_asset_exists():
    """The JSX shim ships next to the Python module."""
    module_dir = pathlib.Path(__import__("reflex_xtermjs").__file__).parent
    assert (module_dir / "xterm_wrapper.jsx").is_file()


def test_library_points_at_the_local_asset():
    """The component imports the bundled shim, not an npm package."""
    component = xterm()
    assert component.library.startswith("$/public")
    assert component.library.endswith("xterm_wrapper.jsx")
    assert component.tag == "XTerm"
    assert component.is_default is False


def test_npm_dependencies_are_pinned():
    """Every npm dependency carries an explicit version."""
    for dependency in XTerm.lib_dependencies:
        assert "@" in dependency.removeprefix("@"), dependency
    assert "@xterm/xterm@6.0.0" in XTerm.lib_dependencies


def test_snake_case_props_become_camel_case():
    """Reflex maps Python prop names to the names xterm.js expects."""
    props = rendered_props(
        xterm(
            terminal_id="t",
            font_size=13,
            cursor_blink=True,
            scroll_on_user_input=False,
            fit_debounce_ms=42,
        )
    )
    assert props["terminalId"] == '"t"'
    assert props["fontSize"] == "13"
    assert props["cursorBlink"] == "true"
    assert props["scrollOnUserInput"] == "false"
    assert props["fitDebounceMs"] == "42"


def test_defaults_are_conservative():
    """A bare terminal fits its container and loads only two addons."""
    props = rendered_props(xterm())
    assert props["autoFit"] == "true"
    assert props["renderer"] == '"dom"'
    assert props["addons"] == '["fit", "web-links"]'
    assert props["readOnly"] == "false"


def test_theme_is_serialized_as_camel_case_object():
    """A theme reaches JS as an ITheme-shaped object."""
    props = rendered_props(xterm(theme=THEMES["dracula"]))
    assert '"selectionBackground"' in props["theme"]
    assert '"brightBlack"' in props["theme"]
    assert "#282a36" in props["theme"]


def test_theme_accepts_a_plain_dict():
    """Computed vars and plain dicts work as themes too."""
    props = rendered_props(xterm(theme={"background": "#101010"}))
    assert "#101010" in props["theme"]


def test_unset_theme_colours_are_omitted():
    """``None`` fields never reach xterm.js as ``null``."""
    props = rendered_props(xterm(theme=XTermTheme(background="#000000")))
    assert "null" not in props["theme"]
    assert "foreground" not in props["theme"]


def test_search_options_are_camel_cased():
    """Nested props objects are converted recursively."""
    props = rendered_props(
        xterm(search_options=SearchOptions(case_sensitive=True, whole_word=False))
    )
    assert '"caseSensitive"' in props["searchOptions"]
    assert '"wholeWord"' in props["searchOptions"]


@pytest.mark.parametrize("addon", ADDONS)
def test_every_documented_addon_is_accepted(addon: str):
    """The advertised addon names all pass validation."""
    assert rendered_props(xterm(addons=[addon]))["addons"] == f'["{addon}"]'


def test_unknown_addon_is_rejected():
    """A typo in the addon list fails loudly at build time."""
    with pytest.raises(ValueError, match="Unknown xterm.js addon"):
        xterm(addons=["fit", "webgl"])


def test_addons_may_be_a_state_var():
    """A dynamic addon list is passed through untouched."""

    class _State(rx.State):
        addons: list[str] = ["fit"]

    assert rendered_props(xterm(addons=_State.addons))["addons"]


def test_event_triggers_are_declared():
    """Every documented event is a real trigger on the component."""
    triggers = xterm().get_event_triggers()
    for name in (
        "on_data",
        "on_key",
        "on_binary",
        "on_resize",
        "on_title_change",
        "on_bell",
        "on_scroll",
        "on_selection_change",
        "on_ready",
        "on_search_results",
        "on_progress",
        "on_context_loss",
        "on_link_click",
        "on_socket_open",
        "on_socket_close",
        "on_socket_error",
    ):
        assert name in triggers, name
