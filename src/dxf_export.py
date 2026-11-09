"""Small self-contained ASCII DXF R12 exporter for the six box faces."""

from __future__ import annotations

from box_geometry import box_faces
from drawing_commands.line import Segment
from drawing_layers import LAYERS
from face_design import make_face_design


def _num(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".") or "0"


def dxf_filename(width: float, depth: float, height: float) -> str:
    """Build a filesystem-safe export name that records all box dimensions."""
    def part(value: float) -> str:
        return _num(value).replace(".", "p")

    return f"box-X{part(width)}-Y{part(depth)}-Z{part(height)}mm.dxf"


def _line(
    entities: list[str], x1: float, y1: float, x2: float, y2: float,
    layer: str = "LINE",
) -> None:
    entities.extend([
        "0", "LINE", "8", layer, "10", _num(x1), "20", _num(y1), "30", "0",
        "11", _num(x2), "21", _num(y2), "31", "0",
    ])


def _write_segments(
    entities: list[str], segments: tuple[Segment, ...] | list[Segment],
    layer: str, offset_x: float = 0, offset_y: float = 0,
) -> None:
    """Translate shared segment geometry into DXF LINE entities on one layer."""
    for start, end in segments:
        _line(
            entities,
            offset_x + start[0], offset_y + start[1],
            offset_x + end[0], offset_y + end[1], layer,
        )


def _text(
    entities: list[str], text: str, x: float, y: float, size: float = 8,
    layer: str = "LABEL",
) -> None:
    entities.extend([
        "0", "TEXT", "8", layer, "10", _num(x), "20", _num(y), "30", "0",
        "40", _num(size), "1", text,
    ])


def _dimension_x(entities: list[str], x: float, y: float, width: float, value: float) -> None:
    dim_y = y - 22
    _line(entities, x, y - 3, x, dim_y - 3, "DIMENSION")
    _line(entities, x + width, y - 3, x + width, dim_y - 3, "DIMENSION")
    _line(entities, x, dim_y, x + width, dim_y, "DIMENSION")
    _line(entities, x - 3, dim_y - 3, x + 3, dim_y + 3, "DIMENSION")
    _line(entities, x + width - 3, dim_y - 3, x + width + 3, dim_y + 3, "DIMENSION")
    _text(entities, f"{_num(value)} mm", x + width / 2 - 16,
          dim_y + 4, 7, "DIMENSION")


def _dimension_y(entities: list[str], x: float, y: float, height: float, value: float) -> None:
    dim_x = x - 22
    _line(entities, x - 3, y, dim_x - 3, y, "DIMENSION")
    _line(entities, x - 3, y + height, dim_x - 3, y + height, "DIMENSION")
    _line(entities, dim_x, y, dim_x, y + height, "DIMENSION")
    _line(entities, dim_x - 3, y - 3, dim_x + 3, y + 3, "DIMENSION")
    _line(entities, dim_x - 3, y + height - 3,
          dim_x + 3, y + height + 3, "DIMENSION")
    _text(entities, f"{_num(height)} mm", dim_x - 3,
          y + height / 2, 7, "DIMENSION")


def _move_lower_left_to_origin(entities: list[str]) -> tuple[float, float]:
    """Translate entity coordinates so the drawing's lower-left is (0, 0)."""
    x_codes = {"10", "11"}
    y_codes = {"20", "21"}
    xs: list[float] = []
    ys: list[float] = []
    for index in range(0, len(entities), 2):
        code, value = entities[index], entities[index + 1]
        if code in x_codes:
            xs.append(float(value))
        elif code in y_codes:
            ys.append(float(value))

    min_x, min_y = min(xs, default=0), min(ys, default=0)
    max_x, max_y = max(xs, default=0), max(ys, default=0)
    for index in range(0, len(entities), 2):
        code = entities[index]
        if code in x_codes:
            entities[index + 1] = _num(float(entities[index + 1]) - min_x)
        elif code in y_codes:
            entities[index + 1] = _num(float(entities[index + 1]) - min_y)
    return max_x - min_x, max_y - min_y


def _linetype_table() -> list[str]:
    """Define the standard continuous line type used by every layer."""
    return [
        "0", "TABLE", "2", "LTYPE", "70", "1",
        "0", "LTYPE", "2", "CONTINUOUS", "70", "0",
        "3", "Solid line", "72", "65", "73", "0", "40", "0",
        "0", "ENDTAB",
    ]


def _layer_table() -> list[str]:
    """Define layer 0 and the app's semantic layers with their ACI colors."""
    table = [
        "0", "TABLE", "2", "LAYER", "70", str(len(LAYERS) + 1),
        "0", "LAYER", "2", "0", "70", "0", "62", "7", "6", "CONTINUOUS",
    ]
    for layer in LAYERS:
        table.extend([
            "0", "LAYER", "2", layer.name, "70", "0",
            "62", str(layer.aci_color), "6", "CONTINUOUS",
        ])
    table.extend(["0", "ENDTAB"])
    return table


def _style_table() -> list[str]:
    """Define the basic text style referenced by legacy CAD readers."""
    return [
        "0", "TABLE", "2", "STYLE", "70", "1",
        "0", "STYLE", "2", "STANDARD", "70", "0",
        "40", "0", "41", "1", "50", "0", "71", "0", "42", "2.5",
        "3", "txt", "4", "",
        "0", "ENDTAB",
    ]


def _tables_section() -> list[str]:
    """Assemble the R12 tables needed by this drawing."""
    return [
        "0", "SECTION", "2", "TABLES",
        *_linetype_table(),
        *_layer_table(),
        *_style_table(),
        "0", "ENDSEC",
    ]


def make_dxf(width: float, depth: float, height: float) -> bytes:
    """Create a LibreCAD-friendly R12 ASCII DXF with six labeled box faces.

    Geometry coordinates and dimension labels are in millimeters. DXF R12 has
    no standard insertion-units header variable, so CAD software may treat the
    numeric coordinates as unitless until the drawing units are set to mm.
    """
    faces = box_faces(width, depth, height)
    cell_width = max(float(face["width"]) for face in faces) + 90
    cell_height = max(float(face["height"]) for face in faces) + 115
    entities: list[str] = []

    for index, face in enumerate(faces):
        face_width = float(face["width"])
        face_height = float(face["height"])
        column, row = index % 3, index // 3
        x = column * cell_width + 42
        y = -row * cell_height + 44
        _text(entities, str(face["name"]), column * cell_width + 8,
              -row * cell_height + cell_height - 25, 10, "LABEL")

        design = make_face_design(face_width, face_height)
        _write_segments(entities, design.boundary, "RECTANGLE", x, y)
        _write_segments(entities, design.decorative_lines, "LINE", x, y)
        _write_segments(entities, design.corner_arcs, "ARC", x, y)
        _write_segments(entities, design.inset_panel, "ROUNDED_RECTANGLE", x, y)

        # The DXF backend keeps circles native instead of polygonizing them.
        aperture = design.aperture
        entities.extend([
            "0", "CIRCLE", "8", "CIRCLE", "10", _num(x + aperture.center_x),
            "20", _num(y + aperture.center_y), "30", "0", "40", _num(aperture.radius),
        ])
        _dimension_x(entities, x, y, face_width, face_width)
        _dimension_y(entities, x, y, face_height, face_height)

    drawing_width, drawing_height = _move_lower_left_to_origin(entities)
    header = [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1009",
        "9", "$INSBASE", "10", "0", "20", "0", "30", "0",
        "9", "$EXTMIN", "10", "0", "20", "0", "30", "0",
        "9", "$EXTMAX", "10", _num(drawing_width),
        "20", _num(drawing_height), "30", "0",
        "0", "ENDSEC",
    ]
    blocks = ["0", "SECTION", "2", "BLOCKS", "0", "ENDSEC"]
    footer = ["0", "ENDSEC", "0", "EOF"]
    lines = header + _tables_section() + blocks + [
        "0", "SECTION", "2", "ENTITIES", *entities,
    ] + footer
    # CRLF is the conventional line ending for legacy ASCII DXF files.
    return ("\r\n".join(lines) + "\r\n").encode("ascii")
