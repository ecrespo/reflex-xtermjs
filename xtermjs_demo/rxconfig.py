"""Reflex configuration for the reflex-xtermjs demo app."""

import reflex as rx

config = rx.Config(
    app_name="xtermjs_demo",
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="dark", accent_color="iris", radius="large"),
        ),
        rx.plugins.SitemapPlugin(),
    ],
)
