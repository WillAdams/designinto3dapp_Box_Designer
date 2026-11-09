"""Axis-aligned rectangle command, returned as four independent line segments."""

from __future__ import annotations

from drawing_commands.line import Segment, line


def rectangle(x: float, y: float, width: float, height: float) -> list[Segment]:
    """Describe the four edges of a rectangle whose lower-left is ``(x, y)``."""
    if width <= 0 or height <= 0:
        raise ValueError("rectangle width and height must be positive")
    lower_left = (x, y)
    lower_right = (x + width, y)
    upper_right = (x + width, y + height)
    upper_left = (x, y + height)
    return [
        line(*lower_left, *lower_right),
        line(*lower_right, *upper_right),
        line(*upper_right, *upper_left),
        line(*upper_left, *lower_left),
    ]
