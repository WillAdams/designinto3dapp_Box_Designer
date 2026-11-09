"""Dimension data and projection helpers for the box designer."""

from __future__ import annotations


def box_faces(width: float, depth: float, height: float) -> list[dict[str, float | str]]:
    """Return the six face names and their actual width/height in millimeters."""
    return [
        {"name": "TOP", "width": width, "height": depth},
        {"name": "BOTTOM", "width": width, "height": depth},
        {"name": "FRONT", "width": width, "height": height},
        {"name": "BACK", "width": width, "height": height},
        {"name": "LEFT", "width": depth, "height": height},
        {"name": "RIGHT", "width": depth, "height": height},
    ]


def isometric_box(
    width: float, depth: float, height: float, canvas_width: float, canvas_height: float
) -> tuple[list[tuple[float, float]], list[tuple[int, int]], dict[str, tuple[float, float]]]:
    """Project the eight box vertices into an isometric wireframe view."""
    x_vector = (width * 0.70710678, -width * 0.40824829)
    y_vector = (-depth * 0.70710678, -depth * 0.40824829)
    z_vector = (0.0, -height * 0.81649658)
    raw = []
    for z in range(2):
        for y in range(2):
            for x in range(2):
                raw.append((x * x_vector[0] + y * y_vector[0] + z * z_vector[0],
                            x * x_vector[1] + y * y_vector[1] + z * z_vector[1]))

    min_x = min(point[0] for point in raw)
    max_x = max(point[0] for point in raw)
    min_y = min(point[1] for point in raw)
    max_y = max(point[1] for point in raw)
    raw_width = max(max_x - min_x, 1.0)
    raw_height = max(max_y - min_y, 1.0)
    scale = min(max(canvas_width - 100, 1) / raw_width, max(canvas_height - 100, 1) / raw_height)
    x_offset = (canvas_width - raw_width * scale) / 2 - min_x * scale
    y_offset = (canvas_height - raw_height * scale) / 2 - min_y * scale
    points = [(x * scale + x_offset, y * scale + y_offset) for x, y in raw]

    # Vertex index is z * 4 + y * 2 + x.
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (4, 5), (4, 6), (5, 7), (6, 7),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    labels = {
        "X": ((points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2),
        "Y": ((points[0][0] + points[2][0]) / 2, (points[0][1] + points[2][1]) / 2),
        "Z": ((points[0][0] + points[4][0]) / 2, (points[0][1] + points[4][1]) / 2),
    }
    return points, edges, labels
