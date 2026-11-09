"""Circle command and point sampling for projected views."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

from drawing_commands.line import Point


@dataclass(frozen=True)
class Circle:
    """A circle in a two-dimensional coordinate plane."""

    center_x: float
    center_y: float
    radius: float


def circle(center_x: float, center_y: float, radius: float) -> Circle:
    """Create circle geometry; renderers may keep it native or project its points."""
    if radius <= 0:
        raise ValueError("circle radius must be positive")
    return Circle(float(center_x), float(center_y), float(radius))


def circle_points(shape: Circle, *, segments: int = 40) -> list[Point]:
    """Return points around the circle, without repeating the first point at the end."""
    if segments < 3:
        raise ValueError("a circle needs at least three sample points")
    return [
        (
            shape.center_x + shape.radius * cos(2 * pi * index / segments),
            shape.center_y + shape.radius * sin(2 * pi * index / segments),
        )
        for index in range(segments)
    ]
