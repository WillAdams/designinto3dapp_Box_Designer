# Box Designer

A Flet app for editing a millimeter box design, previewing its isometric wireframe and six faces, and exporting a labeled, dimensioned DXF.

The export uses ASCII DXF R12 (AC1009) for broad CAD compatibility, including LibreCAD. Its coordinates are in millimeters; because R12 does not store standard insertion-unit metadata, set the drawing units to millimeters in the CAD program if needed.

See [docs/literate_programming.md](docs/literate_programming.md) for the source architecture, drawing-command API, renderer flow, and module-by-module explanation.
