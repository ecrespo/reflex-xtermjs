# reflex-xtermjs

[xterm.js](https://xtermjs.org/) - the terminal that powers VS Code, Hyper and
Azure Cloud Shell - as a [Reflex](https://reflex.dev) custom component, with the
official addons, twelve built-in themes, an imperative API you drive from Python,
and an optional PTY backend that gives the browser a real shell.

```bash
pip install reflex-xtermjs
```

## What you get

- **The full terminal.** Every `ITerminalOptions` field from xterm.js 6 is a
  typed Reflex prop, applied in place so changing a font or a theme never
  destroys the buffer.
- **The official addons** - fit, search, web-links, serialize, clipboard,
  unicode11, unicode-graphemes, image (SIXEL / iTerm / Kitty), ligatures and
  progress - selected with a single `addons=[...]` list.
- **DOM, WebGL and canvas renderers**, switchable at runtime.
- **Events into Python**: `on_data`, `on_key`, `on_resize`, `on_title_change`,
  `on_selection_change`, `on_search_results`, `on_progress` and more.
- **An imperative API**: `XTermAPI` turns `write`, `clear`, `fit`, `find_next`,
  `serialize`, `connect` and the rest into ordinary Reflex event handlers.
- **A reference PTY backend** (`reflex_xtermjs.pty`) that spawns a real
  pseudo-terminal, forwards resizes as `TIOCSWINSZ`, and is locked down to
  localhost with a token by default.
- **Twelve themes** out of the box: VS Code Dark+, Dracula, Nord, Solarized
  (dark and light), Gruvbox Dark, One Dark, Tokyo Night, Catppuccin Mocha,
  Monokai, GitHub Dark and GitHub Light.

## Quick start

```python
import reflex as rx
from reflex_xtermjs import THEMES, XTermAPI, xterm

term = XTermAPI("hello")


class State(rx.State):
    @rx.event
    def greet(self):
        return term.writeln("\x1b[1;32mhello from the backend\x1b[0m")

    @rx.event
    def echo(self, data: str):
        """Every keystroke arrives here."""
        return term.write(data)


def index() -> rx.Component:
    return rx.vstack(
        rx.button("Greet", on_click=State.greet),
        rx.box(
            xterm(
                terminal_id="hello",
                theme=THEMES["dracula"],
                addons=["fit", "web-links", "search"],
                renderer="webgl",
                font_size=14,
                cursor_blink=True,
                on_data=State.echo,
            ),
            height="400px",
            width="100%",
        ),
    )


app = rx.App()
app.add_page(index)
```

The terminal fills its parent, so give the wrapping box a height.

## The component

`xterm(...)` accepts the props below. Python `snake_case` names are emitted as
the `camelCase` names xterm.js expects.

### Identity and layout

| Prop | Type | Default | Meaning |
| --- | --- | --- | --- |
| `terminal_id` | `str` | `"default"` | Key the imperative API uses. Unique per page. |
| `auto_fit` | `bool` | `True` | Resize to the container through the fit addon. |
| `fit_debounce_ms` | `int` | `60` | Debounce on container resize events. |
| `cols` / `rows` | `int` | - | Explicit geometry; used when `auto_fit` is off. |
| `width` / `height` | `str` | `"100%"` | CSS size of the terminal container. |

### Addons and rendering

| Prop | Type | Default | Meaning |
| --- | --- | --- | --- |
| `addons` | `list[str]` | `["fit", "web-links"]` | Any of `fit`, `search`, `web-links`, `serialize`, `clipboard`, `unicode11`, `unicode-graphemes`, `image`, `ligatures`, `progress`. |
| `renderer` | `"dom" \| "webgl" \| "canvas"` | `"dom"` | Renderer backend. |
| `unicode_version` | `str` | addon default | Unicode version activated by the unicode addons. |
| `image_options` | `ImageOptions` | - | SIXEL / iTerm / Kitty limits. |
| `ligature_options` | `LigatureOptions` | - | Ligature fallbacks and font features. |
| `search_options` | `SearchOptions` | - | Defaults merged into every search. |

An unknown addon name raises `ValueError` while the page is being built, rather
than failing silently in the browser. Addons that use xterm.js' proposed API
(`unicode11`, `unicode-graphemes`, `ligatures`, `image`, `progress`,
`serialize`) turn `allow_proposed_api` on automatically unless you set it
yourself.

### Terminal options

All of them are optional and fall back to the xterm.js default:
`allow_proposed_api`, `allow_transparency`, `alt_click_moves_cursor`,
`convert_eol`, `cursor_blink`, `cursor_style`, `cursor_inactive_style`,
`cursor_width`, `custom_glyphs`, `disable_stdin`,
`draw_bold_text_in_bright_colors`, `fast_scroll_modifier`,
`fast_scroll_sensitivity`, `font_family`, `font_size`, `font_weight`,
`font_weight_bold`, `ignore_bracketed_paste_mode`, `letter_spacing`,
`line_height`, `log_level`, `mac_option_click_forces_selection`,
`mac_option_is_meta`, `minimum_contrast_ratio`, `overview_ruler`,
`reflow_cursor_line`, `rescale_overlapping_glyphs`, `right_click_selects_word`,
`screen_reader_mode`, `scroll_on_erase_in_display`, `scroll_on_user_input`,
`scroll_sensitivity`, `scrollback`, `smooth_scroll_duration`, `tab_stop_width`,
`theme`, `window_options`, `windows_pty`, `word_separator`.

Plus two conveniences: `initial_text` (written once on mount) and `read_only`
(a friendlier spelling of `disable_stdin`).

### Events

| Event | Handler signature |
| --- | --- |
| `on_data` | `(data: str)` |
| `on_binary` | `(data: str)` |
| `on_key` | `(key: str, event: dict)` |
| `on_title_change` | `(title: str)` |
| `on_resize` | `(cols: int, rows: int)` |
| `on_ready` | `(cols: int, rows: int)` |
| `on_bell`, `on_line_feed`, `on_cursor_move`, `on_write_parsed`, `on_context_loss` | `()` |
| `on_scroll` | `(position: int)` |
| `on_selection_change` | `(selection: str)` |
| `on_render` | `(start: int, end: int)` |
| `on_search_results` | `(result_index: int, result_count: int)` |
| `on_progress` | `(state: int, value: int)` |
| `on_link_click` | `(uri: str)` |
| `on_socket_open` | `(url: str)` |
| `on_socket_close` | `(code: int, reason: str)` |
| `on_socket_error` | `(message: str)` |

## Driving the terminal from Python

The React shim registers each mounted terminal on
`window.__reflexXterm[terminal_id]`. `XTermAPI` wraps that registry in event
specs, so you never re-render the component to change what it shows.

```python
from reflex_xtermjs import XTermAPI

term = XTermAPI("hello")

rx.button("Clear", on_click=term.clear())
rx.button("Fit", on_click=term.fit())
rx.button("Find", on_click=term.find_next("ERROR", {"caseSensitive": True}))
```

Output, input and focus: `write`, `writeln`, `clear`, `reset`, `refresh`,
`input`, `paste`, `focus`, `blur`.
Geometry: `fit`, `propose_dimensions`, `resize`, `get_size`.
Options: `set_option`, `set_options`, `get_option`, `set_renderer`,
`load_addons`, `clear_texture_atlas`.
Selection: `select_all`, `select`, `clear_selection`, `get_selection`.
Scrolling: `scroll_to_top`, `scroll_to_bottom`, `scroll_to_line`,
`scroll_lines`, `scroll_pages`.
Search: `find_next`, `find_previous`, `clear_search_decorations`.
Serialize: `serialize`, `serialize_as_html`.
Socket: `connect`, `disconnect`, `send`, `is_connected`.
Anything else: `term.call("someMethod", arg1, arg2)`.

Calls that produce a value take a `callback`:

```python
class State(rx.State):
    transcript: str = ""

    @rx.event
    def save(self, value: str):
        self.transcript = value


rx.button("Save transcript", on_click=term.serialize(callback=State.save))
```

## Themes

```python
from reflex_xtermjs import THEMES, THEME_NAMES, XTermTheme, get_theme

xterm(theme=THEMES["nord"])
xterm(theme=get_theme("gruvbox-dark"))

# start from a built-in theme and override a colour
mine = XTermTheme(**{**THEMES["dracula"].dict(), "background": "#1a1a24"})
```

A theme is an `XTermTheme`, which mirrors xterm.js' `ITheme`: `background`,
`foreground`, `cursor`, `cursor_accent`, `selection_background`, the eight ANSI
colours, their eight bright variants, the scrollbar slider colours and
`extended_ansi` for palette entries 16-255. Unset colours are omitted rather
than sent as `null`, so xterm.js keeps its own defaults. Plain dicts work
wherever a theme is accepted, which is what you want for a computed var.

## The PTY backend

`reflex_xtermjs.pty` spawns a real pseudo-terminal and pipes it to the browser
through `@xterm/addon-attach`.

```python
import reflex as rx
from reflex_xtermjs import xterm
from reflex_xtermjs.pty import PtyConfig, pty_app

app = rx.App(
    api_transformer=pty_app(PtyConfig(command="/bin/bash", token="a-secret")),
)
```

```python
xterm(
    terminal_id="shell",
    websocket_url="ws://localhost:8000/pty?token=a-secret",
    addons=["fit", "web-links", "clipboard"],
)
```

`PtyConfig` takes `command`, `args`, `cwd`, `env`, `term`, `cols`, `rows`,
`path`, `token`, `max_sessions`, `allow_remote` and `allowed_origins`.

On the wire it is the plain `addon-attach` protocol - raw bytes both ways - plus
one control frame the component sends whenever the terminal is resized:

```json
{"type": "resize", "cols": 120, "rows": 30}
```

The backend only treats a text frame as control if it parses as JSON *and*
carries a known `type`; everything else goes to the shell verbatim. Set
`send_resize_on_socket=False` on the component if your own backend does not want
those frames.

> **Security.** A PTY endpoint hands whoever reaches it a shell with the
> backend's privileges, with no sandbox. The defaults are deliberately tight:
> without a `token` only loopback clients are accepted, and even with a token
> remote clients need `allow_remote=True`. Browser connections are also
> checked against their `Origin`: only pages served from the same hostname as
> the backend, or listed in `allowed_origins`, may open a shell - this blocks
> cross-site WebSocket hijacking of a localhost terminal. Behind a reverse proxy
> every client looks local, so always set a `token` there. Run the backend as an unprivileged
> user, in a container, on a network you trust - or restrict `command` to a
> single program instead of a login shell.

During development Reflex serves the frontend and the backend on different
ports, so a bare `/pty` path would hit the Vite dev server. Build the URL from
the configured backend API URL; the demo app's `pty_config.py` shows one way.

## Running the demo

```bash
git clone https://github.com/ecrespo/reflex-xtermjs
cd reflex-xtermjs
uv venv && uv pip install -e . && uv pip install -r xtermjs_demo/requirements.txt
cd xtermjs_demo && uv run reflex run
```

Four pages: a live PTY shell, a playground where every option is a control, a
terminal driven entirely from Reflex State (a small shell implemented in
Python), and the addon surface - search, serialize, web-links and progress.

## npm dependencies

The component pins the packages it imports:

```
@xterm/xterm@6.0.0            @xterm/addon-clipboard@0.2.0
@xterm/addon-fit@0.11.0       @xterm/addon-webgl@0.19.0
@xterm/addon-search@0.16.0    @xterm/addon-unicode11@0.9.0
@xterm/addon-web-links@0.12.0 @xterm/addon-unicode-graphemes@0.4.0
@xterm/addon-serialize@0.14.0 @xterm/addon-image@0.9.0
@xterm/addon-attach@0.12.0    @xterm/addon-ligatures@0.10.0
                              @xterm/addon-progress@0.2.0
```

Two official addons are deliberately left out of that set:

- **`@xterm/addon-canvas`** still declares a peer dependency on xterm 5.x, so
  installing it alongside xterm 6 breaks dependency resolution for everyone.
  `renderer="canvas"` loads it lazily and falls back to the DOM renderer with a
  console warning when it is absent. Add `@xterm/addon-canvas` to your own app's
  frontend dependencies if you want it.
- **`@xterm/addon-web-fonts`** currently requires an xterm 6.1 beta.

## Development

```bash
uv pip install -e ".[dev]"
uv run pytest                 # unit tests
PYTHONPATH=. uv run reflex component build   # regenerate .pyi stubs, build dist/
```

## License

Apache-2.0. xterm.js itself is MIT-licensed by the xterm.js authors.
