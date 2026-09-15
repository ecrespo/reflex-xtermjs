# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

## [0.1.0] - 2026-09-15

First release.

### Added

- `XTerm` component wrapping xterm.js 6.0.0 through a local React shim, loaded
  client-side only (`NoSSRComponent`).
- Every `ITerminalOptions` field exposed as a typed Reflex prop, applied in
  place so option changes never re-create the terminal.
- Addon support for fit, search, web-links, serialize, clipboard, unicode11,
  unicode-graphemes, image, ligatures and progress, with build-time validation
  of the `addons` list and automatic `allow_proposed_api` for the addons that
  need it.
- DOM, WebGL and canvas renderers, switchable at runtime; canvas is loaded
  lazily so its stale peer dependency does not affect installs.
- Event triggers: `on_data`, `on_binary`, `on_key`, `on_title_change`,
  `on_resize`, `on_ready`, `on_bell`, `on_line_feed`, `on_cursor_move`,
  `on_scroll`, `on_selection_change`, `on_render`, `on_write_parsed`,
  `on_search_results`, `on_progress`, `on_context_loss`, `on_link_click`,
  `on_socket_open`, `on_socket_close`, `on_socket_error`.
- `XTermAPI`, an imperative handle turning terminal methods into Reflex event
  specs, including value-returning calls with a `callback`.
- `XTermTheme`, `SearchOptions`, `ImageOptions`, `LigatureOptions`,
  `OverviewRulerOptions` and `WindowsPty` typed option objects.
- Twelve built-in themes with `THEMES`, `THEME_NAMES` and `get_theme`.
- `reflex_xtermjs.pty`: a reference PTY WebSocket backend with token auth,
  loopback-only defaults, a session cap and `TIOCSWINSZ` resize handling.
- A four-page demo app and a 60-test suite.

[0.1.0]: https://github.com/ecrespo/reflex-xtermjs/releases/tag/v0.1.0
