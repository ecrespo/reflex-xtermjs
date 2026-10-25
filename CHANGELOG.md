# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

## [0.2.0] - 2026-10-25

### Changed

- **Requires Reflex 0.10 or newer** (`reflex>=0.10.0`) and therefore
  **Python 3.11+**; Python 3.10 support is dropped. Stay on 0.1.x for
  Reflex 0.9.
- Python 3.14 is now tested and declared as supported.
- Build requirement raised to `setuptools>=78.1.1`.
- The demo app requires `reflex>=0.10.0` and `reflex-xtermjs>=0.2.0`.
- Development docs: Reflex 0.10 removed `reflex component build`; type stubs
  are now regenerated with `python -m reflex_base.utils.pyi_generator`, and
  packages are built with `uv build`. Added a release checklist to the README.

### CI

- All workflows run JavaScript actions on the Node 24 runtime
  (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`), and `astral-sh/setup-uv` is bumped
  to v10.3.2.
- Test matrix is now Python 3.11-3.14.
- New `Demo app builds (Node 24)` job compiles the demo and builds its
  production frontend with Reflex 0.10 on Node 24.

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
- A four-page demo app and a test suite.
- CI workflows for code quality (ruff, pytest on Python 3.10-3.13, build and
  `twine check`) and security (bandit, pip-audit, gitleaks, CodeQL,
  dependency review), plus a tag-driven release workflow that publishes to
  GitHub Releases and PyPI through Trusted Publishing.

### Security

- The PTY endpoint checks the WebSocket `Origin` header and refuses pages from
  foreign hosts (new `allowed_origins` setting), closing a cross-site WebSocket
  hijacking path to a localhost shell.
- Tokens are compared in constant time (`hmac.compare_digest`).
- A malformed `resize` control frame no longer aborts the session.

[0.2.0]: https://github.com/ecrespo/reflex-xtermjs/releases/tag/v0.2.0
[0.1.0]: https://github.com/ecrespo/reflex-xtermjs/releases/tag/v0.1.0
