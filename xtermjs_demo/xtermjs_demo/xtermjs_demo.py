"""reflex-xtermjs demo app.

Four pages exercising the component: a real PTY shell, a live options
playground, a terminal driven entirely from Reflex State, and the addon
surface.

Run it with::

    cd xtermjs_demo
    reflex run
"""

from __future__ import annotations

import reflex as rx
from reflex_xtermjs.pty import pty_app

from .pages import addons, live_shell, playground, state_driven
from .pty_config import PTY_SETTINGS

app = rx.App(api_transformer=pty_app(PTY_SETTINGS))

app.add_page(live_shell.index, route="/", title="reflex-xtermjs - live shell")
app.add_page(playground.index, route="/playground", title="reflex-xtermjs - playground")
app.add_page(state_driven.index, route="/state-driven", title="reflex-xtermjs - state driven")
app.add_page(addons.index, route="/addons", title="reflex-xtermjs - addons")
