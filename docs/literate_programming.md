# Box Designer: how the program works

This guide explains the Box Designer from its inputs to its previews and DXF export. It is written to make the code easy to follow and extend. The application source is under `src/`; each module has one main responsibility.

## 1. What the app does

The app accepts positive box dimensions in millimeters:

- **X** is width.
- **Y** is depth.
- **Z** is height.

The screen has a parameter pane, an isometric wireframe preview, and a six-face preview. The parameter pane includes one-millimeter up/down nudges and a DXF download button. Either preview can be collapsed to an icon strip and restored later.

Each face has an outer boundary, a rounded rectangular panel inset by 10% of the face width and height, and a centered circle whose diameter is half the smaller face dimension. A separate decorative frame sits farther out: its straight strokes and inward-facing corner arcs are deliberately separated by small gaps.

The DXF contains all six labeled, dimensioned faces in a sheet layout. It uses millimeters and places the drawing's lower-left coordinate at `(0, 0)`.

## 2. How the parts fit together

The app keeps the shape geometry independent of Flet and DXF formatting. Geometry commands return plain points, segments, or a circle record. The preview and export modules translate that shared geometry into their own output formats.

```text
main.py (fields, events, layout, download)
  ├── box_geometry.py (face sizes and isometric box vertices)
  ├── face_design.py (combines reusable commands into a face)
  │     └── drawing_commands/ (lines, rectangles, rounded rectangles, circles, arcs)
  ├── box_preview.py (Flet canvas shapes, grid, and colors)
  └── dxf_export.py (DXF entities, layers, dimensions, and file name)

Drawing color names:
  drawing_layers.py (DXF layer names and ACI values)
       └── drawing_palette.py (Flet color for each layer name)
```

A shape command should not import Flet or write DXF. That separation lets the same face design be drawn in multiple ways and makes the geometry modules usable on their own.

## 3. Source files

| File | What it is responsible for | Flet dependency? |
|---|---|---:|
| [`src/main.py`](../src/main.py) | Builds the page, fields, preview panels, event handlers, and download action | Yes |
| [`src/box_hints.py`](../src/box_hints.py) | Builds the parameter guide shown when both previews are collapsed | Yes |
| [`src/box_geometry.py`](../src/box_geometry.py) | Describes face dimensions and projects the box's eight corners | No |
| [`src/face_design.py`](../src/face_design.py) | Combines shape commands into one standard face design | No |
| [`src/drawing_commands/__init__.py`](../src/drawing_commands/__init__.py) | Re-exports the public drawing commands | No |
| [`src/drawing_commands/line.py`](../src/drawing_commands/line.py) | Defines points, line segments, and polylines | No |
| [`src/drawing_commands/rectangle.py`](../src/drawing_commands/rectangle.py) | Returns the four edges of a rectangle | No |
| [`src/drawing_commands/rounded_rectangle.py`](../src/drawing_commands/rounded_rectangle.py) | Returns a rounded rectangle as straight segments | No |
| [`src/drawing_commands/circle.py`](../src/drawing_commands/circle.py) | Defines a circle and can sample its perimeter points | No |
| [`src/drawing_commands/arc.py`](../src/drawing_commands/arc.py) | Approximates an arc with straight segments | No |
| [`src/drawing_layers.py`](../src/drawing_layers.py) | Lists DXF layer names, AutoCAD Color Index values, and purposes | No |
| [`src/drawing_palette.py`](../src/drawing_palette.py) | Maps each layer name to a Flet color | Yes |
| [`src/box_preview.py`](../src/box_preview.py) | Draws the face cards and isometric canvas | Yes |
| [`src/dxf_export.py`](../src/dxf_export.py) | Creates the layered ASCII DXF and dimension-bearing filename | No |

## 4. Geometry commands

All coordinates in the face design are in millimeters, with the face's lower-left corner at `(0, 0)`. The commands return geometry rather than drawing it.

### 4.1 Line and polyline — `drawing_commands/line.py`

`Point` is a pair `(x, y)`. `Segment` is a pair of points. `line(x1, y1, x2, y2)` returns one segment. `polyline(points, closed=False)` joins consecutive points and optionally adds the closing segment.

```python
from drawing_commands.line import line, polyline

edge = line(0, 0, 120, 0)
outline = polyline([(0, 0), (120, 0), (120, 60), (0, 60)], closed=True)
```

### 4.2 Rectangle — `drawing_commands/rectangle.py`

`rectangle(x, y, width, height)` returns four independent edges, starting at the lower-left and going around the perimeter. Width and height must be positive.

### 4.3 Rounded rectangle — `drawing_commands/rounded_rectangle.py`

`rounded_rectangle(x, y, width, height, radius, segments_per_corner=6)` returns the perimeter in order as straight segments and sampled quarter-circle corners. The radius is limited to half the shorter side. A radius of zero returns four square-cornered edges. Width and height must be positive, and the radius cannot be negative.

### 4.4 Circle — `drawing_commands/circle.py`

`circle(center_x, center_y, radius)` returns an immutable `Circle` record. The radius must be positive. `circle_points(shape, segments=40)` returns points around its perimeter without repeating the first point. Use the circle record when the output format supports native circles; sample the points when the circle must be transformed or projected.

### 4.5 Arc — `drawing_commands/arc.py`

`arc(center_x, center_y, radius, start_degrees, sweep_degrees, segments=12)` returns straight chord segments approximating a circular arc. Zero degrees points along +X, positive sweeps go counterclockwise, and negative sweeps go clockwise. Radius and segment count must be positive. Because the command returns segments, both the preview and DXF represent its curve as short straight pieces; the DXF does not use a native `ARC` entity for these accents.

### 4.6 Public command imports

`drawing_commands/__init__.py` exposes the common command names so callers can import from the package when convenient. Individual modules remain available for direct imports, as shown above.

## 5. The standard face design

[`src/face_design.py`](../src/face_design.py) combines the commands into a renderer-independent `FaceDesign` record. Its fields are kept separate so renderers can put each kind of element on its own layer:

- `boundary`: the four outer face edges;
- `decorative_lines`: four straight decorative strokes;
- `corner_arcs`: the four inward-bowing corner accents;
- `inset_panel`: the 10%-inset rounded rectangle;
- `aperture`: the centered circle.

`make_face_design(width, height)` is the standard face constructor. It uses a rounded-panel corner radius equal to 10% of the smaller panel dimension. The aperture radius is 25% of the smaller face dimension, so its diameter is half that dimension.

`decorative_components(...)` returns the straight strokes and arcs separately. The strokes stop short of the arcs, leaving a visible gap. `decorative_frame(...)` is a convenience function that returns both groups together. The decorative frame is inset by 5% by default; `corner_fraction`, `line_gap_fraction`, and `arc_segments` control corner size, separation, and curve smoothness.

Example:

```python
from face_design import make_face_design

face = make_face_design(600, 400)  # millimeter coordinates, lower-left at (0, 0)
```

The returned value contains no UI controls, paint settings, or DXF records.

## 6. Layers and colors

[`src/drawing_layers.py`](../src/drawing_layers.py) defines the semantic DXF layers and their AutoCAD Color Index (ACI) values. [`src/drawing_palette.py`](../src/drawing_palette.py) maps those same layer names to Flet `ft.Colors` values for the previews and checks that the two tables contain the same names.

| Layer | DXF ACI | Preview color | Used for |
|---|---:|---|---|
| `RECTANGLE` | 8 | `GREY_300` | Outer face boundaries and all box wireframe edges |
| `LINE` | 2 | `AMBER_300` | Straight decorative strokes |
| `ROUNDED_RECTANGLE` | 5 | `LIGHT_BLUE_300` | Inset rounded panels |
| `CIRCLE` | 3 | `LIGHT_GREEN_300` | Face circles |
| `ARC` | 6 | `PINK_300` | Detached corner accents |
| `DIMENSION` | 4 | `CYAN_300` | DXF dimension marks and text; preview face measurements and height ticks |
| `LABEL` | 7 | `GREY_100` | Face names and the isometric grid caption |
| `GRID` | 9 | `BLUE_GREY_300` | Isometric reference grid only; grid lines are not exported |

Every DXF entity has a layer name, and the DXF LAYER table stores the corresponding ACI value. The previews select colors by the same semantic layer name. ACI values and Flet colors are each renderer's color representation; exact displayed shades can vary between CAD programs and their themes.

## 7. The Flet previews — `box_preview.py`

`box_preview.py` is the Flet rendering adapter. It maps points to canvas positions and turns shared segments into `ft.canvas.Line` controls.

- `face_shapes(width, height)` draws the face boundary, decorative lines, corner arcs, inset panel, circle, and measurement caption for a face card. Each element uses its layer's preview color.
- `_draw_face_design(...)` maps the same face motif onto a selected isometric face. It samples the circle perimeter because a circle on an angled plane projects as an ellipse.
- `isometric_shapes(...)` draws the reference grid, visible face designs, twelve box edges, height ruler and tick marks, and grid caption. Grid pitch is selected from a readable sequence of 1/2/5 times powers of ten. The grid extends at least one pitch beyond each box edge; its far edges are rounded outward to grid lines. Height ticks use the same pitch and sit along the left edge of the ground grid.

The top, front, and left face designs are projected into the isometric view. The 2D pane shows all six faces. All twelve wireframe box edges currently use the `RECTANGLE` layer and its color; the preview does not draw hidden edges in a separate style.

## 8. DXF output — `dxf_export.py`

`make_dxf(width, depth, height)` builds an ASCII **AutoCAD R12 (AC1009)** DXF without a CAD package. R12 is an older, widely supported DXF version and is a compatibility-oriented choice for LibreCAD and other CAD readers. The file uses the basic `LINE`, `CIRCLE`, and `TEXT` entities that this version supports, along with conventional `LTYPE`, `LAYER`, and `STYLE` tables and an empty `BLOCKS` section.

The exporter asks `box_faces()` for the six face dimensions and `make_face_design()` for each face's shared geometry, then arranges those faces in three columns and two rows. Face labels and dimension lines/text are included. Boundary, straight decorative strokes, corner arcs, rounded panels, circles, dimensions, and labels are assigned to their matching layers. The rounded-panel corners and decorative arcs are represented by short `LINE` entities on their respective layers; circles are native DXF `CIRCLE` entities.

The drawing's numeric coordinates and dimension labels are millimeters. **R12 has no standard insertion-units header variable**, so the file cannot reliably tell every CAD program that its unit is millimeters. LibreCAD may treat the coordinates as unitless until the drawing unit is set to mm. The geometry remains at millimeter scale, and its dimension captions include “mm”.

`_move_lower_left_to_origin()` translates entity coordinates so the lowest X and Y values become zero; the header's base point and minimum extents are also set to `(0, 0)`. `dxf_filename(width, depth, height)` includes all three dimensions, for example `box-X600-Y400-Z300mm.dxf`; decimal points are written as `p` to keep the name portable. The file uses CRLF line endings, conventional for legacy ASCII DXF.

The DXF contains the six face drawings, not the isometric grid or isometric wireframe. `GRID` is still defined in the layer table so the layer palette remains complete, but no grid entities are written.

## 9. The page and event flow — `main.py`

`main(page)` builds the three dimension fields, their one-millimeter up/down nudge buttons, the two preview panels, and the DXF download button. Keyboard focus follows each parameter row in order: field, increase button, decrease button, then the next dimension. Tab from the final nudge returns to the Width field; Shift+Tab from Width returns to the final nudge. Typed dimensions must be positive and no greater than 1,000,000 mm; nudging will not reduce a value below 0.1 mm.

When a field changes, `refresh_dimensions()` validates and saves the values, rebuilds all six face cards, and redraws the isometric preview. Clicking either preview's title icon or text label, or its chevron, collapses that panel. Each collapsed preview becomes a full-height vertical bar with its icon at the top and a short `ISO` or `FACES` label; clicking anywhere on the bar restores the matching preview. If both are collapsed, `box_hints.py` displays a scrollable guide first, followed on its right by both preview bars. The guide explains X, Y, Z, the face design, and the millimeter units, and has buttons to restore either preview. `download_dxf()` creates the DXF from the current dimensions and asks Flet's `FilePicker` to save it under the dimension-bearing filename.

Logging is configured in `main.py`; application loggers use the `app.*` namespace.

## 10. How to add or change an element

To add a reusable shape:

1. Put its geometry command in a focused file under `src/drawing_commands/`.
2. Validate its inputs and return plain geometry; do not import Flet or emit DXF there.
3. Export it from `drawing_commands/__init__.py` if it should be part of the package's public command set.
4. Add it to `FaceDesign` or another geometry-composition function if it belongs in the box design.
5. Give it a semantic layer in `drawing_layers.py` and a Flet color in `drawing_palette.py` if it is a separately colored element.
6. Teach `box_preview.py` and `dxf_export.py` how to render it, using the same layer name in both adapters.
7. Update this guide with the command's parameters, units, coordinate convention, and output geometry.

This keeps the shape reusable, the color assignment consistent, and the rendering-specific code at the edges of the program.
