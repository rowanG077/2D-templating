import numpy as np
from typing import Iterable, Sequence, Tuple

from math import cos, sin, radians

from .dsl import Arc, Feature, Line, Segment, Spline


class Renderer:
    """Simple software renderer that draws into a numpy array."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.pixels = np.zeros((height, width, 3), dtype=np.uint8)
        self.clear()

    def clear(self, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        self.pixels[:] = color

    def _set_pixel(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        ix = int(round(x))
        iy = int(round(y))
        if 0 <= ix < self.width and 0 <= iy < self.height:
            self.pixels[iy, ix] = color

    def draw_line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        ix1 = int(round(x1))
        iy1 = int(round(y1))
        ix2 = int(round(x2))
        iy2 = int(round(y2))
        dx = abs(ix2 - ix1)
        dy = -abs(iy2 - iy1)
        sx = 1 if ix1 < ix2 else -1
        sy = 1 if iy1 < iy2 else -1
        err = dx + dy
        while True:
            self._set_pixel(ix1, iy1, color)
            if ix1 == ix2 and iy1 == iy2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                ix1 += sx
            if e2 <= dx:
                err += dx
                iy1 += sy

    def draw_arc(
        self,
        cx: float,
        cy: float,
        r: float,
        start: float,
        end: float,
        color: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        from math import cos, sin, radians

        step = 1.0  # step angle in degrees
        if end < start:
            step = -step
        angle = start
        while (angle <= end and step > 0) or (angle >= end and step < 0):
            rad = radians(angle)
            x = cx + r * cos(rad)
            y = cy + r * sin(rad)
            self._set_pixel(x, y, color)
            angle += step

    def _bezier_point(self, pts: Sequence[Tuple[float, float]], t: float) -> Tuple[float, float]:
        x_pts = [p[0] for p in pts]
        y_pts = [p[1] for p in pts]
        n = len(pts) - 1
        for r in range(1, n + 1):
            for i in range(n - r + 1):
                x_pts[i] = (1 - t) * x_pts[i] + t * x_pts[i + 1]
                y_pts[i] = (1 - t) * y_pts[i] + t * y_pts[i + 1]
        return x_pts[0], y_pts[0]

    def draw_spline(
        self, points: Sequence[Tuple[float, float]], color: Tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        if len(points) < 3:
            return
        steps = max(20, int(sum(np.hypot(np.diff([p[0] for p in points]), np.diff([p[1] for p in points])))))
        for i in range(steps + 1):
            t = i / steps
            x, y = self._bezier_point(points, t)
            self._set_pixel(x, y, color)

    def draw_features(self, features: Iterable[Feature]) -> np.ndarray:
        for feature in features:
            start_x, start_y = feature.start
            current_x, current_y = start_x, start_y
            for segment in feature.segments:
                if isinstance(segment, Line):
                    self.draw_line(current_x, current_y, segment.x, segment.y)
                    current_x, current_y = segment.x, segment.y
                elif isinstance(segment, Spline):
                    pts = [(current_x, current_y)] + list(segment.points)
                    self.draw_spline(pts)
                    current_x, current_y = segment.points[-1]
                elif isinstance(segment, Arc):
                    self.draw_arc(
                        segment.cx,
                        segment.cy,
                        segment.radius,
                        segment.start_angle,
                        segment.end_angle,
                    )
                    current_x = segment.cx + segment.radius * cos(radians(segment.end_angle))
                    current_y = segment.cy + segment.radius * sin(radians(segment.end_angle))
            # close shape
            self.draw_line(current_x, current_y, start_x, start_y)
        return self.pixels
