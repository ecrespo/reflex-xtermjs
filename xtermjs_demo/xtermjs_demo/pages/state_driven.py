"""Page 3 - a shell emulated entirely in Python State, no PTY involved.

Every keystroke reaches the backend through ``on_data``; the backend decides
what to echo and writes it back through the imperative API. This is the
pattern to use when you want a terminal UI without giving anyone a real shell.
"""

from __future__ import annotations

import datetime
import platform
import sys

import reflex as rx
from reflex_xtermjs import THEMES, XTermAPI, xterm

from ..shared import TERMINAL_FRAME, page_layout

term = XTermAPI("state-shell")

PROMPT = "\x1b[1;32mreflex\x1b[0m:\x1b[1;34m~\x1b[0m$ "


def _banner() -> str:
    """Build the boot banner.

    It starts by homing the cursor and erasing the screen and the scrollback,
    so a development re-mount (React runs effects twice) redraws the banner
    instead of stacking a second copy underneath the first.
    """
    title = "reflex-xtermjs"
    subtitle = " - a shell written in Python"
    inner = f"  {title}{subtitle}  "
    rule = "\u2500" * len(inner)
    return (
        "\x1b[H\x1b[2J\x1b[3J"
        f"\x1b[1;36m\u256d{rule}\u256e\r\n"
        f"\u2502  \x1b[0m\x1b[1m{title}\x1b[0m\x1b[36m{subtitle}\x1b[1;36m  \u2502\r\n"
        f"\u2570{rule}\u256f\x1b[0m\r\n\r\n"
        " Every keystroke travels to a Reflex event handler, and the answer is\r\n"
        " written back from Python. Type \x1b[1mhelp\x1b[0m to see what it knows."
        "\r\n\r\n"
    )


BANNER = _banner()

FAKE_FS = {
    "README.md": "the docs you are reading",
    "pyproject.toml": "package metadata",
    "custom_components/": "the component source",
    "xtermjs_demo/": "this demo app",
}


class ShellState(rx.State):
    """Line editor and command dispatcher."""

    buffer: str = ""
    history: list[str] = []
    history_index: int = -1
    command_count: int = 0
    last_command: str = ""

    def _emit(self, text: str):
        """Write text to the terminal."""
        return term.write(text)

    @rx.event
    def boot(self, cols: int, rows: int):
        """Print the banner once the terminal is ready.

        The banner clears the screen first, so a development re-mount
        redraws it instead of stacking a second copy underneath.
        """
        self.buffer = ""
        return self._emit(BANNER + PROMPT)

    @rx.event
    def handle_data(self, data: str):
        """Process one chunk of terminal input."""
        events = []
        for char in data:
            if char == "\r":
                events.extend(self._submit())
            elif char in ("\x7f", "\b"):
                if self.buffer:
                    self.buffer = self.buffer[:-1]
                    events.append(self._emit("\b \b"))
            elif char == "\x03":  # Ctrl+C
                self.buffer = ""
                events.append(self._emit("^C\r\n" + PROMPT))
            elif char == "\x0c":  # Ctrl+L
                self.buffer = ""
                events.append(term.clear())
                events.append(self._emit(PROMPT))
            elif char == "\x1b":
                # Swallow the escape introducer; arrow keys are handled below.
                continue
            elif char in ("[", "A", "B", "C", "D") and not self.buffer:
                continue
            elif char.isprintable():
                self.buffer += char
                events.append(self._emit(char))
        return events

    def _submit(self) -> list:
        """Run the buffered line."""
        line = self.buffer.strip()
        self.buffer = ""
        if not line:
            return [self._emit("\r\n" + PROMPT)]

        self.history.append(line)
        self.history_index = len(self.history)
        self.command_count += 1
        self.last_command = line
        output = self._run(line)
        if output is None:  # `clear` handles its own output
            return [term.clear(), self._emit(PROMPT)]
        return [self._emit(f"\r\n{output}{PROMPT}")]

    def _run(self, line: str) -> str | None:
        """Execute one command and return what to print."""
        parts = line.split()
        command, args = parts[0], parts[1:]

        if command == "help":
            rows = [
                ("help", "this message"),
                ("date", "current date and time"),
                ("echo <text>", "print text back"),
                ("ls", "list a make-believe directory"),
                ("cat <file>", "describe one of those files"),
                ("whoami", "who the backend thinks you are"),
                ("version", "Python and platform info"),
                ("colors", "an ANSI colour chart"),
                ("history", "commands you have run"),
                ("clear", "wipe the screen"),
            ]
            body = "".join(f"  \x1b[1;36m{name:<14}\x1b[0m {desc}\r\n" for name, desc in rows)
            return f"\x1b[1mAvailable commands\x1b[0m\r\n{body}"

        if command == "date":
            now = datetime.datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
            return f"{now}\r\n"

        if command == "echo":
            return " ".join(args) + "\r\n"

        if command == "ls":
            return "".join(
                f"  \x1b[1;34m{name}\x1b[0m\r\n" if name.endswith("/") else f"  {name}\r\n"
                for name in FAKE_FS
            )

        if command == "cat":
            if not args:
                return "\x1b[31mcat: missing file operand\x1b[0m\r\n"
            target = args[0]
            if target in FAKE_FS:
                return f"{FAKE_FS[target]}\r\n"
            return f"\x1b[31mcat: {target}: No such file or directory\x1b[0m\r\n"

        if command == "whoami":
            return "a browser talking to a Reflex backend\r\n"

        if command == "version":
            return (
                f"Python {sys.version.split()[0]} on {platform.system()} {platform.release()}\r\n"
            )

        if command == "colors":
            chart = ""
            for row in range(16):
                for col in range(16):
                    code = row * 16 + col
                    chart += f"\x1b[48;5;{code}m {code:>3} \x1b[0m"
                chart += "\r\n"
            return chart

        if command == "history":
            return "".join(
                f"  {index + 1:>3}  {entry}\r\n" for index, entry in enumerate(self.history)
            )

        if command == "clear":
            return None

        return f"\x1b[31m{command}: command not found\x1b[0m  (try \x1b[1mhelp\x1b[0m)\r\n"


def index() -> rx.Component:
    """The state-driven page."""
    return page_layout(
        "State-driven terminal",
        "No PTY here: on_data carries every keystroke to a Reflex event "
        "handler, and the handler writes the response back with "
        "XTermAPI.write. The shell, the line editing and the command set all "
        "live in Python.",
        rx.hstack(
            rx.badge(f"commands run: {ShellState.command_count}", variant="soft"),
            rx.cond(
                ShellState.last_command != "",
                rx.badge(f"last: {ShellState.last_command}", variant="outline"),
            ),
            rx.spacer(),
            rx.button(
                rx.icon("eraser", size=16),
                "Clear",
                on_click=[term.clear(), term.write(PROMPT)],
                variant="soft",
            ),
            rx.button(
                rx.icon("mouse-pointer-click", size=16),
                "Focus",
                on_click=term.focus(),
                variant="soft",
            ),
            width="100%",
            align="center",
            spacing="3",
            wrap="wrap",
        ),
        rx.box(
            xterm(
                terminal_id="state-shell",
                theme=THEMES["catppuccin-mocha"].dict(),
                addons=["fit", "web-links", "unicode-graphemes"],
                renderer="webgl",
                font_size=14,
                cursor_blink=True,
                convert_eol=False,
                on_data=ShellState.handle_data,
                on_ready=ShellState.boot,
            ),
            height="480px",
            width="100%",
            **TERMINAL_FRAME,
        ),
    )
