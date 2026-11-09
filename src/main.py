"""Flet interface for an editable, dimensioned box design."""

from __future__ import annotations

import logging

import flet as ft
from flet import canvas as fc

from box_geometry import box_faces
from box_hints import create_hints_panel
from box_preview import face_shapes, isometric_shapes
from drawing_palette import color_for_layer
from dxf_export import dxf_filename, make_dxf

LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)
log = logging.getLogger("app.main")


def main(page: ft.Page):
    page.title = "Box Designer"
    page.padding = 12
    page.spacing = 12

    dimensions = {"width": 600.0, "depth": 400.0, "height": 300.0}
    width_field = ft.TextField(label="Width (X) · mm", value="600", width=180,
                               keyboard_type=ft.KeyboardType.NUMBER)
    depth_field = ft.TextField(label="Depth (Y) · mm", value="400", width=180,
                               keyboard_type=ft.KeyboardType.NUMBER)
    height_field = ft.TextField(label="Height (Z) · mm", value="300", width=180,
                                keyboard_type=ft.KeyboardType.NUMBER)
    fields = {"width": width_field, "depth": depth_field, "height": height_field}
    status = ft.Text("All dimensions in millimeters.")
    file_picker = ft.FilePicker()

    face_canvases: list[fc.Canvas] = []
    face_cards = []
    for face in box_faces(**dimensions):
        face_canvas = fc.Canvas(
            width=140,
            height=130,
            shapes=face_shapes(float(face["width"]), float(face["height"])),
        )
        face_canvases.append(face_canvas)
        face_cards.append(ft.Card(
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text(str(face["name"]), color=color_for_layer("LABEL")), 
                    face_canvas,
                ],
            ),
        ))

    faces_grid = ft.GridView(
        expand=True,
        max_extent=280,
        spacing=8,
        run_spacing=8,
        controls=face_cards,
    )

    iso_size = {"width": 540.0, "height": 420.0}
    iso_canvas = fc.Canvas(
        expand=True,
        resize_interval=100,
        shapes=isometric_shapes(600, 400, 300, iso_size["width"], iso_size["height"]),
    )

    def draw_isometric(e: ft.CanvasResizeEvent):
        if e.width > 1 and e.height > 1:
            iso_size.update({"width": e.width, "height": e.height})
            iso_canvas.shapes = isometric_shapes(
                dimensions["width"], dimensions["depth"], dimensions["height"],
                e.width, e.height,
            )
            iso_canvas.update()

    iso_canvas.on_resize = draw_isometric

    def toggle_preview(which: str):
        nonlocal iso_collapsed, faces_collapsed
        if which == "iso":
            iso_collapsed = not iso_collapsed
        else:
            faces_collapsed = not faces_collapsed
        sync_previews()

    iso_collapsed = False
    faces_collapsed = False

    iso_header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Container(
                tooltip="Collapse isometric preview",
                on_click=lambda: toggle_preview("iso"),
                content=ft.Row(controls=[
                    ft.Icon(ft.Icons.VIEW_IN_AR), ft.Text("Isometric wireframe"),
                ]),
            ),
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, tooltip="Collapse isometric preview",
                          on_click=lambda: toggle_preview("iso")),
        ],
    )
    faces_header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Container(
                tooltip="Collapse face previews",
                on_click=lambda: toggle_preview("faces"),
                content=ft.Row(controls=[
                    ft.Icon(ft.Icons.GRID_VIEW), ft.Text("Face previews"),
                ]),
            ),
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, tooltip="Collapse face previews",
                          on_click=lambda: toggle_preview("faces")),
        ],
    )

    iso_panel = ft.Container(
        expand=1,
        content=ft.Column(expand=True, controls=[iso_header, iso_canvas]),
    )
    faces_panel = ft.Container(
        expand=1,
        content=ft.Column(expand=True, controls=[faces_header, faces_grid]),
    )
    workspace = ft.Row(
        expand=True,
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[iso_panel, faces_panel],
    )

    def collapsed_panel(icon: str, label: str, tooltip: str, which: str) -> ft.Container:
        return ft.Container(
            width=52,
            alignment=ft.Alignment.TOP_CENTER,
            tooltip=tooltip,
            on_click=lambda: restore_preview(which),
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[ft.Icon(icon), ft.Text(label, text_align=ft.TextAlign.CENTER)],
            ),
        )

    def restore_preview(which: str):
        nonlocal iso_collapsed, faces_collapsed
        if which == "iso":
            iso_collapsed = False
        else:
            faces_collapsed = False
        sync_previews()

    hints_panel = create_hints_panel(
        restore_isometric=lambda: restore_preview("iso"),
        restore_faces=lambda: restore_preview("faces"),
    )

    def sync_previews():
        controls = [
            collapsed_panel(
                ft.Icons.VIEW_IN_AR, "ISO", "Restore isometric preview", "iso",
            ) if iso_collapsed else iso_panel,
            collapsed_panel(
                ft.Icons.GRID_VIEW, "FACES", "Restore face previews", "faces",
            ) if faces_collapsed else faces_panel,
        ]
        if iso_collapsed and faces_collapsed:
            controls.insert(0, hints_panel)
        workspace.controls = controls
        workspace.update()

    def refresh_dimensions():
        try:
            values = {
                "width": float(width_field.value),
                "depth": float(depth_field.value),
                "height": float(height_field.value),
            }
            if any(value <= 0 or value > 1_000_000 for value in values.values()):
                raise ValueError
        except (TypeError, ValueError):
            status.value = "Enter positive dimensions up to 1,000,000 mm."
            status.update()
            return

        dimensions.update(values)
        for canvas, face in zip(face_canvases, box_faces(**dimensions)):
            canvas.shapes = face_shapes(float(face["width"]), float(face["height"]))
            canvas.update()
        status.value = "Preview updated · all dimensions in mm."
        status.update()
        log.debug("Updated design: %s", dimensions)
        # The isometric canvas also redraws on size changes; explicitly redraw for edits.
        iso_canvas.shapes = isometric_shapes(
            dimensions["width"], dimensions["depth"], dimensions["height"],
            iso_size["width"], iso_size["height"],
        )
        iso_canvas.update()

    for field in fields.values():
        field.on_change = refresh_dimensions

    tab_direction = {"value": 0}

    def track_tab_direction(e: ft.KeyboardEvent):
        tab_direction["value"] = (
            -1 if e.shift else 1
        ) if str(e.key).lower() == "tab" else 0

    page.on_keyboard_event = track_tab_direction

    def reset_tab_direction(e):
        tab_direction["value"] = 0

    def nudge(key: str, amount: float):
        field = fields[key]
        try:
            current = float(field.value)
        except (TypeError, ValueError):
            current = dimensions[key]
        field.value = f"{max(0.1, current + amount):g}"
        field.update()
        refresh_dimensions()

    nudge_buttons: dict[str, tuple[ft.IconButton, ft.IconButton]] = {}

    def dimension_input(key: str, field: ft.TextField) -> ft.Row:
        up_button = ft.IconButton(
            icon=ft.Icons.ARROW_DROP_UP,
            icon_size=18,
            width=32,
            height=25,
            padding=0,
            tooltip=f"Increase {key} by 1 mm",
            on_click=lambda: nudge(key, 1),
        )
        down_button = ft.IconButton(
            icon=ft.Icons.ARROW_DROP_DOWN,
            icon_size=18,
            width=32,
            height=25,
            padding=0,
            tooltip=f"Decrease {key} by 1 mm",
            on_click=lambda: nudge(key, -1),
        )
        nudge_buttons[key] = (up_button, down_button)
        return ft.Row(
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[field, ft.Column(
                tight=True,
                spacing=0,
                controls=[up_button, down_button],
            )],
        )

    dimension_rows = [dimension_input(key, field) for key, field in fields.items()]
    parameter_focus_order = []
    for key, field in fields.items():
        field.on_focus = reset_tab_direction
        parameter_focus_order.extend([field, *nudge_buttons[key]])
        for button in nudge_buttons[key]:
            button.on_focus = reset_tab_direction

    def make_parameter_tab_handler(index: int):
        async def move_parameter_focus(e):
            direction = tab_direction["value"]
            if direction:
                # Route every Tab/Shift+Tab transition through the declared
                # order; this also wraps from the last nudge to Width.
                tab_direction["value"] = 0
                next_index = (index + direction) % len(parameter_focus_order)
                await parameter_focus_order[next_index].focus()

        return move_parameter_focus

    for index, control in enumerate(parameter_focus_order):
        control.on_blur = make_parameter_tab_handler(index)

    async def download_dxf():
        try:
            contents = make_dxf(**dimensions)
            saved_path = await file_picker.save_file(
                dialog_title="Save box design DXF",
                file_name=dxf_filename(**dimensions),
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["dxf"],
                src_bytes=contents,
            )
            status.value = (
                "DXF exported · units are millimeters."
                if saved_path else "DXF export cancelled."
            )
        except Exception as error:
            log.exception("DXF export failed")
            status.value = f"Could not save the DXF: {error}"
        status.update()

    parameter_pane = ft.Container(
        width=240,
        content=ft.Column(
            expand=True,
            spacing=12,
            controls=[
                ft.Text("BOX PARAMETERS"),
                *dimension_rows,
                status,
                ft.Container(expand=True),
                ft.Button(
                    content="Download DXF",
                    icon=ft.Icons.FILE_DOWNLOAD,
                    on_click=download_dxf,
                ),
            ],
        ),
    )

    page.add(ft.Row(
        expand=True,
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[parameter_pane, workspace],
    ))


ft.run(main)
