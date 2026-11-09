"""Compose renderer-independent element commands into a standard box-face motif."""

from __future__ import annotations

from dataclasses import dataclass

from drawing_commands.arc import arc
from drawing_commands.circle import Circle, circle
from drawing_commands.line import Segment, line
from drawing_commands.rectangle import rectangle
from drawing_commands.rounded_rectangle import rounded_rectangle


@dataclass(frozen=True)
class FaceDesign:
    """Local face geometry, separated by element type/layer.

    Coordinates use millimeters with the face's lower-left at ``(0, 0)``.
    """

    boundary: tuple[Segment, ...]
    decorative_lines: tuple[Segment, ...]
    corner_arcs: tuple[Segment, ...]
    inset_panel: tuple[Segment, ...]
    aperture: Circle


def decorative_components(
    width: float,
    height: float,
    *,
    inset: float = 0.05,
    corner_fraction: float = 0.065,
    line_gap_fraction: float = 0.025,
    arc_segments: int = 12,
) -> tuple[list[Segment], list[Segment]]:
    """Return separate straight and arc commands for the corner-accent frame.

    The edge strokes stop before the four inward-bowed quarter arcs. The open
    distance between each arc and its neighboring straight stroke is intentional.
    Fractions are relative to the face or its shorter side, as appropriate.
    """
    if width <= 0 or height <= 0:
        raise ValueError("face width and height must be positive")
    if not 0 <= inset < 0.5:
        raise ValueError("frame inset must be in [0, 0.5)")
    if corner_fraction <= 0 or line_gap_fraction < 0:
        raise ValueError("corner size must be positive and line gap non-negative")

    x0, x1 = width * inset, width * (1 - inset)
    y0, y1 = height * inset, height * (1 - inset)
    radius = min(width, height) * corner_fraction
    gap = min(width, height) * line_gap_fraction
    straight_lines = [
        line(x0 + radius + gap, y0, x1 - radius - gap, y0),
        line(x0 + radius + gap, y1, x1 - radius - gap, y1),
        line(x0, y0 + radius + gap, x0, y1 - radius - gap),
        line(x1, y0 + radius + gap, x1, y1 - radius - gap),
    ]
    corner_arcs = []
    # Circle centers lie exactly on each decorative-frame corner; each arc bows
    # into the face interior and stays separated from the straight strokes.
    corner_arcs.extend(arc(x0, y0, radius, 0, 90, segments=arc_segments))
    corner_arcs.extend(arc(x1, y0, radius, 90, 90, segments=arc_segments))
    corner_arcs.extend(arc(x1, y1, radius, 180, 90, segments=arc_segments))
    corner_arcs.extend(arc(x0, y1, radius, 270, 90, segments=arc_segments))
    return straight_lines, corner_arcs


def decorative_frame(
    width: float,
    height: float,
    *,
    inset: float = 0.05,
    corner_fraction: float = 0.065,
    line_gap_fraction: float = 0.025,
    arc_segments: int = 12,
) -> list[Segment]:
    """Return both element types as one convenience collection."""
    straight_lines, corner_arcs = decorative_components(
        width, height, inset=inset, corner_fraction=corner_fraction,
        line_gap_fraction=line_gap_fraction, arc_segments=arc_segments,
    )
    return straight_lines + corner_arcs


def make_face_design(width: float, height: float) -> FaceDesign:
    """Return the shared outer edge, ornaments, inset panel, and aperture."""
    if width <= 0 or height <= 0:
        raise ValueError("face width and height must be positive")
    inset_x, inset_y = width * 0.1, height * 0.1
    inset_width, inset_height = width * 0.8, height * 0.8
    radius = min(inset_width, inset_height) * 0.1
    straight_lines, corner_arcs = decorative_components(width, height)
    return FaceDesign(
        boundary=tuple(rectangle(0, 0, width, height)),
        decorative_lines=tuple(straight_lines),
        corner_arcs=tuple(corner_arcs),
        inset_panel=tuple(rounded_rectangle(
            inset_x, inset_y, inset_width, inset_height, radius,
        )),
        aperture=circle(width / 2, height / 2, min(width, height) * 0.25),
    )
