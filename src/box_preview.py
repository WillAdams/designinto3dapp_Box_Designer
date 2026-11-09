"""Canvas drawing helpers for the box's face and isometric previews."""

from __future__ import annotations

from math import ceil, floor, log10

import flet as ft
from flet import canvas as fc

from box_geometry import isometric_box
from drawing_commands.circle import circle_points
from drawing_commands.line import Point, Segment
from drawing_palette import color_for_layer
from face_design import make_face_design


def _mm(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _stroke(color: str, width: float = 1.5) -> ft.Paint:
    return ft.Paint(color=color, stroke_width=width, style=ft.PaintingStyle.STROKE)


def _draw_segments(shapes: list, segments: tuple[Segment, ...] | list[Segment], project, paint):
    """Adapt renderer-independent segments to Flet canvas line controls."""
    for start, end in segments:
        projected_start, projected_end = project(start), project(end)
        shapes.append(fc.Line(
            x1=projected_start[0], y1=projected_start[1],
            x2=projected_end[0], y2=projected_end[1], paint=paint,
        ))


def face_shapes(face_width: float, face_height: float) -> list:
    canvas_width, canvas_height = 140, 130
    scale = min(106 / face_width, 68 / face_height)
    draw_width, draw_height = face_width * scale, face_height * scale
    left, top = (canvas_width - draw_width) / 2, 15 + (68 - draw_height) / 2
    design = make_face_design(face_width, face_height)
    outline_paint = _stroke(color_for_layer("RECTANGLE"))
    line_paint = _stroke(color_for_layer("LINE"), 1.2)
    arc_paint = _stroke(color_for_layer("ARC"), 1.2)
    panel_paint = _stroke(color_for_layer("ROUNDED_RECTANGLE"), 2)
    circle_paint = _stroke(color_for_layer("CIRCLE"), 2)
    dimension_paint = _stroke(color_for_layer("DIMENSION"))

    def map_point(point: Point) -> Point:
        return left + point[0] * scale, top + point[1] * scale

    shapes = []
    _draw_segments(shapes, design.boundary, map_point, outline_paint)
    _draw_segments(shapes, design.decorative_lines, map_point, line_paint)
    _draw_segments(shapes, design.corner_arcs, map_point, arc_paint)
    _draw_segments(shapes, design.inset_panel, map_point, panel_paint)
    aperture = design.aperture
    shapes.append(fc.Circle(
        x=left + aperture.center_x * scale,
        y=top + aperture.center_y * scale,
        radius=aperture.radius * scale,
        paint=circle_paint,
    ))
    shapes.extend([
        fc.Line(
            x1=left, y1=top + draw_height + 7,
            x2=left + draw_width, y2=top + draw_height + 7, paint=dimension_paint,
        ),
        fc.Text(
            x=canvas_width / 2,
            y=112,
            value=f"{_mm(face_width)} × {_mm(face_height)} mm",
            style=ft.TextStyle(size=11, color=color_for_layer("DIMENSION")),
            alignment=ft.Alignment.CENTER,
        ),
    ])
    return shapes


def _nice_step(span: float) -> float:
    target = max(span / 6, 0.001)
    power = 10 ** int(floor(log10(target)))
    scaled = target / power
    factor = 1 if scaled <= 1 else 2 if scaled <= 2 else 5 if scaled <= 5 else 10
    return factor * power


def _draw_face_design(
    shapes: list,
    face_width: float,
    face_height: float,
    project,
) -> None:
    """Project the shared face motif with its corresponding layer colors."""
    design = make_face_design(face_width, face_height)
    project_point = lambda point: project(*point)
    _draw_segments(
        shapes, design.decorative_lines, project_point,
        _stroke(color_for_layer("LINE"), 1.2),
    )
    _draw_segments(
        shapes, design.corner_arcs, project_point,
        _stroke(color_for_layer("ARC"), 1.2),
    )
    _draw_segments(
        shapes, design.inset_panel, project_point,
        _stroke(color_for_layer("ROUNDED_RECTANGLE"), 1.6),
    )
    circle_paint = _stroke(color_for_layer("CIRCLE"), 1.6)
    projected_circle = [
        project(*point) for point in circle_points(design.aperture, segments=40)
    ]
    for index, start in enumerate(projected_circle):
        end = projected_circle[(index + 1) % len(projected_circle)]
        shapes.append(fc.Line(
            x1=start[0], y1=start[1], x2=end[0], y2=end[1], paint=circle_paint,
        ))


def isometric_shapes(width: float, depth: float, height: float,
                     canvas_width: float, canvas_height: float) -> list:
    points, edges, _ = isometric_box(width, depth, height, canvas_width, canvas_height)
    grid_step = _nice_step(max(width, depth, height))
    x_min = -grid_step
    x_max = ceil(width / grid_step) * grid_step + grid_step
    y_min = -grid_step
    y_max = ceil(depth / grid_step) * grid_step + grid_step

    def initial_project(x_fraction: float, y_fraction: float, z_fraction: float = 0.0):
        origin, x_corner, y_corner, z_corner = points[0], points[1], points[2], points[4]
        return (
            origin[0] + x_fraction * (x_corner[0] - origin[0])
            + y_fraction * (y_corner[0] - origin[0])
            + z_fraction * (z_corner[0] - origin[0]),
            origin[1] + x_fraction * (x_corner[1] - origin[1])
            + y_fraction * (y_corner[1] - origin[1])
            + z_fraction * (z_corner[1] - origin[1]),
        )

    # Include the extended floor and its height ruler in the fit, not just the box.
    frame_points = list(points)
    for x_value in (x_min, x_max):
        for y_value in (y_min, y_max):
            frame_points.append(initial_project(x_value / width, y_value / depth))
    frame_points.append(initial_project(x_min / width, y_max / depth, 1))
    min_x = min(point[0] for point in frame_points)
    max_x = max(point[0] for point in frame_points)
    min_y = min(point[1] for point in frame_points)
    max_y = max(point[1] for point in frame_points)
    frame_width = max(max_x - min_x, 1)
    frame_height = max(max_y - min_y, 1)
    fit = min(1, max(canvas_width - 120, 1) / frame_width,
              max(canvas_height - 140, 1) / frame_height)
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
    points = [
        ((point[0] - center_x) * fit + canvas_width / 2,
         (point[1] - center_y) * fit + canvas_height / 2)
        for point in points
    ]
    p0, px, py, pz = points[0], points[1], points[2], points[4]

    def project(x_fraction: float, y_fraction: float, z_fraction: float = 0.0):
        return (
            p0[0] + x_fraction * (px[0] - p0[0])
            + y_fraction * (py[0] - p0[0]) + z_fraction * (pz[0] - p0[0]),
            p0[1] + x_fraction * (px[1] - p0[1])
            + y_fraction * (py[1] - p0[1]) + z_fraction * (pz[1] - p0[1]),
        )

    def positions(start: float, end: float) -> list[float]:
        count = max(1, round((end - start) / grid_step))
        values = [start + index * grid_step for index in range(count + 1)]
        values[-1] = end
        return values

    x_positions = positions(x_min, x_max)
    y_positions = positions(y_min, y_max)
    shapes = []
    grid_paint = _stroke(color_for_layer("GRID"), 0.8)

    # Ground-plane grid extends one grid pitch past every box edge.
    for y_value in y_positions:
        start = project(x_min / width, y_value / depth)
        end = project(x_max / width, y_value / depth)
        shapes.append(fc.Line(x1=start[0], y1=start[1], x2=end[0], y2=end[1], paint=grid_paint))
    for x_value in x_positions:
        start = project(x_value / width, y_min / depth)
        end = project(x_value / width, y_max / depth)
        shapes.append(fc.Line(x1=start[0], y1=start[1], x2=end[0], y2=end[1], paint=grid_paint))

    # Top (X×Y), left (Y×Z), and front (X×Z) are the three visible faces.
    _draw_face_design(
        shapes, width, depth,
        lambda u, v: project(u / width, v / depth, 1),
    )
    _draw_face_design(
        shapes, depth, height,
        lambda u, v: project(0, u / depth, v / height),
    )
    _draw_face_design(
        shapes, width, height,
        lambda u, v: project(u / width, 0, v / height),
    )

    # Box boundaries use the same layer color in both the view and the DXF.
    wire_paint = _stroke(color_for_layer("RECTANGLE"), 2)
    for start_index, end_index in edges:
        shapes.append(fc.Line(
            x1=points[start_index][0], y1=points[start_index][1],
            x2=points[end_index][0], y2=points[end_index][1], paint=wire_paint,
        ))

    # Height graduations sit on the grid's far-left vertical edge.
    tick_step = grid_step
    tick_count = max(1, ceil(height / tick_step))
    tick_paint = _stroke(color_for_layer("DIMENSION"), 1.2)
    ruler_bottom = project(x_min / width, y_max / depth, 0)
    ruler_top = project(x_min / width, y_max / depth, 1)
    shapes.append(fc.Line(
        x1=ruler_bottom[0], y1=ruler_bottom[1],
        x2=ruler_top[0], y2=ruler_top[1], paint=tick_paint,
    ))
    for index in range(tick_count + 1):
        fraction = min(index * tick_step / height, 1.0)
        point = project(x_min / width, y_max / depth, fraction)
        shapes.append(fc.Line(
            x1=point[0] - 10, y1=point[1], x2=point[0], y2=point[1], paint=tick_paint,
        ))

    ground_bottom = max(
        project(x / width, y / depth)[1]
        for x in (x_min, x_max)
        for y in (y_min, y_max)
    )
    grid_label = (
        f"GROUND GRID · {_mm(x_max - x_min)} × {_mm(y_max - y_min)} mm"
        f" · {_mm(grid_step)} mm pitch"
    )
    shapes.append(fc.Text(
        x=canvas_width / 2,
        y=min(canvas_height - 12, ground_bottom + 18),
        value=grid_label,
        style=ft.TextStyle(size=11, color=color_for_layer("LABEL")), 
        alignment=ft.Alignment.CENTER,
    ))
    return shapes
