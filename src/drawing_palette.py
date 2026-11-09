"""Flet color counterparts for the DXF layer palette."""

from __future__ import annotations

import flet as ft

from drawing_layers import LAYERS_BY_NAME

# Colors are intentionally bright on the app's dark drawing surface. Their
# matching AutoCAD Color Index values are defined once in drawing_layers.py.
LAYER_COLORS = {
    "RECTANGLE": ft.Colors.GREY_300,
    "LINE": ft.Colors.AMBER_300,
    "ROUNDED_RECTANGLE": ft.Colors.LIGHT_BLUE_300,
    "CIRCLE": ft.Colors.LIGHT_GREEN_300,
    "ARC": ft.Colors.PINK_300,
    "DIMENSION": ft.Colors.CYAN_300,
    "LABEL": ft.Colors.GREY_100,
    "GRID": ft.Colors.BLUE_GREY_300,
}

if LAYER_COLORS.keys() != LAYERS_BY_NAME.keys():
    raise RuntimeError("every DXF layer must have exactly one Flet preview color")


def color_for_layer(name: str) -> str:
    """Return the Flet enum color corresponding to a named DXF layer."""
    try:
        return LAYER_COLORS[name]
    except KeyError as error:
        raise KeyError(f"unknown drawing layer: {name}") from error
