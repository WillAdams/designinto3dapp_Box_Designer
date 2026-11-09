"""Primitive line segments used by both the canvas and DXF backends.

The command returns data only; it does not depend on Flet or a DXF library.
Coordinates are ordinary Cartesian millimeters or preview-space coordinates.
"""

from __future__ import annotations

from typing import TypeAlias

Point: TypeAlias = tuple[float, float]
Segment: TypeAlias = tuple[Point, Point]


def line(x1: float, y1: float, x2: float, y2: float) -> Segment:
    """Describe one straight segment from ``(x1, y1)`` to ``(x2, y2)``."""
    return ((float(x1), float(y1)), (float(x2), float(y2)))


def polyline(points: list[Point] | tuple[Point, ...], *, closed: bool = False) -> list[Segment]:
    """Turn ordered points into segments; optionally connect the final point to the first."""
    segments = [line(*start, *end) for start, end in zip(points, points[1:])]
    if closed and len(points) > 2:
        segments.append(line(*points[-1], *points[0]))
    return segments
