"""Explanatory parameter guide shown when both previews are collapsed."""

from __future__ import annotations

import flet as ft


def create_hints_panel(restore_isometric, restore_faces) -> ft.Container:
    """Build a scrollable guide and controls to restore either preview."""
    return ft.Container(
        expand=True,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Box design hints"),
                ft.Text("All dimensions are entered in millimeters (mm)."),
                ft.Text("Width (X): the box's left-to-right dimension."),
                ft.Text("Depth (Y): the box's front-to-back dimension."),
                ft.Text("Height (Z): the box's bottom-to-top dimension."),
                ft.Text(
                    "Use the up and down arrows beside a field to adjust it by "
                    "1 mm, or type a value directly. Dimensions must be positive."
                ),
                ft.Text(
                    "The isometric preview shows the box in three dimensions. "
                    "Its ground grid and height ticks use millimeter spacing."
                ),
                ft.Text(
                    "The face previews show the top, bottom, front, back, left, "
                    "and right sides. Each face has a rounded panel inset by "
                    "10% of its width and height."
                ),
                ft.Text(
                    "The centered circle's diameter is half the smaller "
                    "dimension of that face. Decorative edge strokes and corner "
                    "arcs are separate from the panel."
                ),
                ft.Text(
                    "Download DXF saves the six labeled and dimensioned face "
                    "drawings. The drawing geometry is in millimeters."
                ),
                ft.Row(
                    wrap=True,
                    controls=[
                        ft.Button(
                            content="Restore isometric preview",
                            icon=ft.Icons.VIEW_IN_AR,
                            on_click=restore_isometric,
                        ),
                        ft.Button(
                            content="Restore face previews",
                            icon=ft.Icons.GRID_VIEW,
                            on_click=restore_faces,
                        ),
                    ],
                ),
            ],
        ),
    )
