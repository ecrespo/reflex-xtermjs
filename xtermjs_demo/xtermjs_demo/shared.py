"""Shared layout, navigation and constants for the demo app."""

from __future__ import annotations

import reflex as rx

PAGES: list[tuple[str, str, str]] = [
    ("/", "Live shell", "terminal"),
    ("/playground", "Playground", "sliders-horizontal"),
    ("/state-driven", "State-driven", "arrow-left-right"),
    ("/addons", "Addons", "puzzle"),
]

TERMINAL_FRAME = {
    "border": "1px solid var(--gray-5)",
    "border_radius": "12px",
    "padding": "12px",
    "background": "var(--gray-2)",
    "overflow": "hidden",
}


def nav_link(path: str, label: str, icon: str) -> rx.Component:
    """One item of the top navigation bar."""
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label, size="2"),
            align="center",
            spacing="2",
        ),
        href=path,
        padding="8px 14px",
        border_radius="8px",
        _hover={"background": "var(--accent-3)"},
    )


def page_layout(title: str, description: str, *content: rx.Component) -> rx.Component:
    """Wrap page content in the shared shell."""
    return rx.container(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("square-terminal", size=22),
                    rx.heading("reflex-xtermjs", size="5"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.hstack(
                    *[nav_link(path, label, icon) for path, label, icon in PAGES],
                    spacing="1",
                ),
                rx.color_mode.button(),
                width="100%",
                align="center",
                padding_y="16px",
            ),
            rx.divider(),
            rx.vstack(
                rx.heading(title, size="7"),
                rx.text(description, color="var(--gray-11)", size="3"),
                spacing="1",
                padding_y="16px",
                width="100%",
            ),
            *content,
            spacing="3",
            width="100%",
            padding_bottom="48px",
        ),
        size="4",
    )
