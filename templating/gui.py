from typing import Iterable, Optional, Sequence, List, Tuple

import numpy as np
from PySide6 import QtWidgets, QtGui, QtCore

from .dsl import Arc, Feature, Line, Spline, parse, serialize
from .renderer import Renderer


class Canvas(QtWidgets.QLabel):
    def __init__(
        self,
        width: int = 400,
        height: int = 400,
        parent: Optional[QtWidgets.QWidget] = None,
        on_change=None,
    ) -> None:
        super().__init__(parent)
        self.renderer = Renderer(width, height)
        self.setFixedSize(width, height)
        self.update_pixmap()
        self.features: List[Feature] = []
        self.draw_mode: Optional[str] = None
        self.temp_points: List[Tuple[float, float]] = []
        self.on_change = on_change

    def _numpy_to_qimage(self, arr: np.ndarray) -> QtGui.QImage:
        height, width, _ = arr.shape
        qimg = QtGui.QImage(arr.data, width, height, arr.strides[0], QtGui.QImage.Format_RGB888)
        return qimg.copy()

    def update_pixmap(self) -> None:
        img = self._numpy_to_qimage(self.renderer.pixels)
        self.setPixmap(QtGui.QPixmap.fromImage(img))

    def draw_features(self, features: Iterable[Feature]) -> None:
        self.renderer.clear()
        self.renderer.draw_features(features)
        self.update_pixmap()

    def set_mode(self, mode: Optional[str]) -> None:
        self.draw_mode = mode
        self.temp_points.clear()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if not self.draw_mode:
            return
        pos = (event.position().x(), event.position().y())
        self.temp_points.append(pos)
        if self.draw_mode == "line" and len(self.temp_points) == 2:
            start, end = self.temp_points
            feat = Feature(start, [Line(end[0], end[1])])
            self.features.append(feat)
            self.draw_features(self.features)
            self.temp_points.clear()
            if self.on_change:
                self.on_change(self.features)
        elif self.draw_mode == "arc" and len(self.temp_points) == 3:
            center, start_pt, end_pt = self.temp_points
            from math import atan2, degrees, hypot

            radius = hypot(start_pt[0] - center[0], start_pt[1] - center[1])
            start_a = degrees(atan2(start_pt[1] - center[1], start_pt[0] - center[0]))
            end_a = degrees(atan2(end_pt[1] - center[1], end_pt[0] - center[0]))
            feat = Feature(start_pt, [Arc(center[0], center[1], radius, start_a, end_a)])
            self.features.append(feat)
            self.draw_features(self.features)
            self.temp_points.clear()
            if self.on_change:
                self.on_change(self.features)
        elif self.draw_mode == "spline":
            # points are collected until a double click finishes the spline
            pass

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.draw_mode == "spline":
            pos = (event.position().x(), event.position().y())
            self.temp_points.append(pos)
            if len(self.temp_points) >= 3:
                start = self.temp_points[0]
                pts = self.temp_points[1:]
                feat = Feature(start, [Spline(pts)])
                self.features.append(feat)
                self.draw_features(self.features)
                if self.on_change:
                    self.on_change(self.features)
            self.temp_points.clear()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Template Editor")
        self.text = QtWidgets.QPlainTextEdit()
        self.canvas = Canvas(on_change=self._on_canvas_change)

        save_png = QtWidgets.QPushButton("Save PNG")
        save_svg = QtWidgets.QPushButton("Save SVG")
        redraw = QtWidgets.QPushButton("Redraw")
        line_btn = QtWidgets.QPushButton("Line")
        arc_btn = QtWidgets.QPushButton("Arc")
        spline_btn = QtWidgets.QPushButton("Spline")
        clear_btn = QtWidgets.QPushButton("Clear")

        save_png.clicked.connect(self.export_png)
        save_svg.clicked.connect(self.export_svg)
        redraw.clicked.connect(self.update_view)
        line_btn.clicked.connect(lambda: self.canvas.set_mode("line"))
        arc_btn.clicked.connect(lambda: self.canvas.set_mode("arc"))
        spline_btn.clicked.connect(lambda: self.canvas.set_mode("spline"))
        clear_btn.clicked.connect(self._clear_canvas)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(redraw)
        button_layout.addWidget(line_btn)
        button_layout.addWidget(arc_btn)
        button_layout.addWidget(spline_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(save_png)
        button_layout.addWidget(save_svg)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text)
        layout.addLayout(button_layout)
        layout.addWidget(self.canvas)

        central = QtWidgets.QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def _on_canvas_change(self, features: Sequence[Feature]) -> None:
        self.text.setPlainText(serialize(features))

    def _clear_canvas(self) -> None:
        self.canvas.features = []
        self.canvas.draw_features([])
        self.text.clear()

    def update_view(self) -> None:
        text = self.text.toPlainText()
        features = parse(text)
        self.canvas.draw_features(features)

    def _current_qimage(self) -> QtGui.QImage:
        return self.canvas._numpy_to_qimage(self.canvas.renderer.pixels)

    def export_png(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export PNG", filter="PNG Files (*.png)")
        if path:
            self._current_qimage().save(path, "PNG")

    def export_svg(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export SVG", filter="SVG Files (*.svg)")
        if path:
            svg_lines = ["<svg xmlns='http://www.w3.org/2000/svg'>"]
            text = self.text.toPlainText()
            features = parse(text)
            for feature in features:
                current_x, current_y = feature.start
                for shape in feature.segments:
                    if isinstance(shape, Line):
                        svg_lines.append(
                            f"<line x1='{current_x}' y1='{current_y}' x2='{shape.x}' y2='{shape.y}' stroke='black' />"
                        )
                        current_x, current_y = shape.x, shape.y
                    elif isinstance(shape, Spline):
                        pts = [(current_x, current_y)] + shape.points
                        if len(pts) == 3:
                            (_, _), (cx, cy), (x1, y1) = pts
                            svg_lines.append(
                                f"<path d='M{current_x},{current_y} Q{cx},{cy} {x1},{y1}' fill='none' stroke='black' />"
                            )
                        elif len(pts) >= 4:
                            (_, _), (c1x, c1y), (c2x, c2y), (x1, y1) = pts[:4]
                            svg_lines.append(
                                f"<path d='M{current_x},{current_y} C{c1x},{c1y} {c2x},{c2y} {x1},{y1}' fill='none' stroke='black' />"
                            )
                        current_x, current_y = shape.points[-1]
                    elif isinstance(shape, Arc):
                        from math import cos, sin, radians

                        x1 = shape.cx + shape.radius * cos(radians(shape.start_angle))
                        y1 = shape.cy + shape.radius * sin(radians(shape.start_angle))
                        x2 = shape.cx + shape.radius * cos(radians(shape.end_angle))
                        y2 = shape.cy + shape.radius * sin(radians(shape.end_angle))
                        large = int(abs(shape.end_angle - shape.start_angle) > 180)
                        sweep = int(shape.end_angle > shape.start_angle)
                        svg_lines.append(
                            f"<path d='M{x1},{y1} A{shape.radius},{shape.radius} 0 {large} {sweep} {x2},{y2}' fill='none' stroke='black' />"
                        )
                        current_x, current_y = x2, y2
                svg_lines.append(
                    f"<line x1='{current_x}' y1='{current_y}' x2='{feature.start[0]}' y2='{feature.start[1]}' stroke='black' />"
                )
            svg_lines.append("</svg>")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(svg_lines))

