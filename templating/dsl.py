import re
from dataclasses import dataclass
from typing import List, Tuple, Union

@dataclass
class Line:
    x: float
    y: float


@dataclass
class Spline:
    points: List[Tuple[float, float]]


@dataclass
class Arc:
    cx: float
    cy: float
    radius: float
    start_angle: float
    end_angle: float


Segment = Union[Line, Spline, Arc]

@dataclass
class Feature:
    start: Tuple[float, float]
    segments: List[Segment]

def parse_line(line: str) -> Segment:
    line = line.strip()
    if not line:
        raise ValueError("Empty line")
    parts = re.split(r"\s+", line)
    kind = parts[0].upper()
    numbers = [float(p) for p in parts[1:]]
    if kind == "LINE":
        if len(numbers) != 2:
            raise ValueError("LINE expects 2 numbers")
        return Line(numbers[0], numbers[1])
    if kind == "SPLINE":
        if len(numbers) < 4 or len(numbers) % 2 != 0:
            raise ValueError("SPLINE expects an even number of coordinates >= 4")
        pts = [(numbers[i], numbers[i + 1]) for i in range(0, len(numbers), 2)]
        return Spline(pts)
    if kind == "ARC":
        if len(numbers) != 5:
            raise ValueError("ARC expects 5 numbers")
        return Arc(numbers[0], numbers[1], numbers[2], numbers[3], numbers[4])
    raise ValueError(f"Unknown shape '{kind}'")

def parse(text: str) -> List[Feature]:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip() and not ln.strip().startswith("#")]
    features: List[Feature] = []
    i = 0
    while i < len(lines):
        header = re.split(r"\s+", lines[i])
        if len(header) != 3 or header[0].upper() != "FEATURE":
            raise ValueError("FEATURE line must be 'FEATURE x y'")
        start = (float(header[1]), float(header[2]))
        i += 1
        segments: List[Segment] = []
        while i < len(lines) and lines[i].upper() != "END":
            segments.append(parse_line(lines[i]))
            i += 1
        if i >= len(lines) or lines[i].upper() != "END":
            raise ValueError("Unterminated FEATURE")
        features.append(Feature(start, segments))
        i += 1
    return features

