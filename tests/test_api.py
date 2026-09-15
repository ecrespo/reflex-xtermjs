"""Tests for the imperative XTermAPI helpers."""

from __future__ import annotations

import reflex as rx
from reflex_xtermjs import XTermAPI

term = XTermAPI("demo")


def script_of(event_spec) -> str:
    """Extract the JavaScript that an ``rx.call_script`` spec will run."""
    for var, value in event_spec.args:
        if str(var) == "javascript_code":
            return value._var_value
    raise AssertionError("no javascript_code argument in the event spec")


def test_handle_is_guarded_against_a_missing_terminal():
    """Calls are no-ops when the terminal is not mounted."""
    script = script_of(term.clear())
    assert "window.__reflexXterm" in script
    assert '"demo"' in script
    assert "?." in script


def test_write_serializes_its_payload():
    """Strings are JSON-encoded, so escapes survive the trip."""
    assert script_of(term.write("hi")).endswith('.write("hi")')
    assert "\\r\\n" in script_of(term.write("a\r\n"))


def test_numeric_and_boolean_arguments():
    """Non-string arguments keep their JS types."""
    assert script_of(term.resize(120, 40)).endswith(".resize(120, 40)")
    assert script_of(term.input("x", False)).endswith('.input("x", false)')


def test_dict_arguments_become_object_literals():
    """Search options are passed as a real JS object."""
    script = script_of(term.find_next("needle", {"caseSensitive": True}))
    assert "findNext" in script
    assert '"caseSensitive"' in script


def test_state_vars_are_inlined_as_expressions():
    """A Var argument compiles to the JS expression, not to a quoted string."""

    class _State(rx.State):
        text: str = ""

    script = script_of(term.write(_State.text))
    assert "_state" in script
    assert '"' + "_state" not in script


def test_terminal_id_may_be_a_var():
    """The terminal id can be computed at runtime."""

    class _IdState(rx.State):
        term_id: str = "a"

    script = script_of(XTermAPI(_IdState.term_id).focus())
    assert "focus()" in script
    assert "term_id" in script


def test_callback_is_attached_for_value_returning_calls():
    """Reads route their result back into a state handler."""

    class _DumpState(rx.State):
        dump: str = ""

        @rx.event
        def store(self, value: str):
            self.dump = value

    spec = term.serialize(callback=_DumpState.store)
    callback = {str(name): value for name, value in spec.args}["callback"]
    assert "store" in str(callback)


def test_generic_call_reaches_any_method():
    """``call`` is the escape hatch for anything not wrapped explicitly."""
    assert script_of(term.call("scrollToLine", 5)).endswith(".scrollToLine(5)")
