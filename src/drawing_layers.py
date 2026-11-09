"""Shared DXF layer names and AutoCAD Color Index values.

This module is renderer-independent. The ACI numbers are written into the DXF
layer table; the matching Flet enum colors live in ``drawing_palette.py``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DrawingLayer:
    """One semantic drawing layer and its AutoCAD Color Index color."""

    name: str
    aci_color: int
    purpose: str


LAYERS = (
    DrawingLayer("RECTANGLE", 8, "Outer face and box boundaries"),
    DrawingLayer("LINE", 2, "Straight decorative strokes"),
    DrawingLayer("ROUNDED_RECTANGLE", 5, "Inset rounded face panels"),
    DrawingLayer("CIRCLE", 3, "Centered face apertures"),
    DrawingLayer("ARC", 6, "Detached inward-facing corner accents"),
    DrawingLayer("DIMENSION", 4, "Dimension lines and values"),
    DrawingLayer("LABEL", 7, "Face titles and annotations"),
    DrawingLayer("GRID", 9, "Isometric reference grid; preview-only"),
)

LAYERS_BY_NAME = {layer.name: layer for layer in LAYERS}
