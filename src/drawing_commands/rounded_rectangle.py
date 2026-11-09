"""Rounded-rectangle command built from straight edges and quarter-circle arcs."""

from __future__ import annotations

from drawing_commands.arc import arc
from drawing_commands.line import Segment, line


def rounded_rectangle(
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
    *,
    segments_per_corner: int = 6,
) -> list[Segment]:
    """Describe a closed rounded rectangle as sampled segment geometry.

    ``(x, y)`` is the lower-left of the complete shape. Corner radius is clamped
    to half the shorter side. The returned list is ordered around the perimeter.
    """
    if width <= 0 or height <= 0:
        raise ValueError("rounded-rectangle width and height must be positive")
    if radius < 0:
        raise ValueError("corner radius cannot be negative")
    if segments_per_corner < 1:
        raise ValueError("each rounded corner needs at least one segment")

    r = min(radius, width / 2, height / 2)
    if r == 0:
        return [
            line(x, y, x + width, y),
            line(x + width, y, x + width, y + height),
            line(x + width, y + height, x, y + height),
            line(x, y + height, x, y),
        ]

    result: list[Segment] = []
    # Begin along the lower edge and travel counterclockwise.
    result.append(line(x + r, y, x + width - r, y))
    result.extend(arc(x + width - r, y + r, r, -90, 90, segments=segments_per_corner))
    result.append(line(x + width, y + r, x + width, y + height - r))
    result.extend(arc(x + width - r, y + height - r, r, 0, 90,
                      segments=segments_per_corner))
    result.append(line(x + width - r, y + height, x + r, y + height))
    result.extend(arc(x + r, y + height - r, r, 90, 90,
                      segments=segments_per_corner))
    result.append(line(x, y + height - r, x, y + r))
    result.extend(arc(x + r, y + r, r, 180, 90, segments=segments_per_corner))
    return result
