"""Sampled circular arcs expressed as reusable straight line segments."""

from __future__ import annotations

from math import cos, pi, sin

from drawing_commands.line import Point, Segment, line


def arc(
    center_x: float,
    center_y: float,
    radius: float,
    start_degrees: float,
    sweep_degrees: float,
    *,
    segments: int = 12,
) -> list[Segment]:
    """Approximate a circular arc with segments.

    Angles are measured counterclockwise from the positive X axis. A positive
    sweep runs counterclockwise and a negative sweep runs clockwise. ``segments``
    is the number of straight chords used for the curve.
    """
    if radius <= 0:
        raise ValueError("arc radius must be positive")
    if segments < 1:
        raise ValueError("an arc needs at least one segment")

    start = start_degrees * pi / 180
    sweep = sweep_degrees * pi / 180
    points: list[Point] = []
    for index in range(segments + 1):
        angle = start + sweep * index / segments
        points.append((
            center_x + radius * cos(angle),
            center_y + radius * sin(angle),
        ))
    return [line(*first, *second) for first, second in zip(points, points[1:])]
