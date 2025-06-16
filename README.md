# 2D Templating

This project provides a small DSL and PySide6 GUI for drawing simple 2D microscopy templates.

## Features

- Define templates using a small DSL of `LINE`, `SPLINE`, and `ARC` commands.
  A template contains one or more **features**, each represented as a list of
  segments that implicitly form a closed shape. Each feature begins with
  `FEATURE x y` to specify the starting point.
- Render templates using a custom numpy-based renderer displayed in a PySide6 GUI.
- Curves (arcs and splines) are rendered using dedicated algorithms.
- Export the rendered scene to PNG or SVG.

## Example DSL

```
# Two closed features
FEATURE 0 0
LINE 50 0
LINE 50 50
LINE 0 50
END

FEATURE 100 75
ARC 75 75 25 0 180
SPLINE 100 75 110 85 100 95
END
```

## Running

Install dependencies and run `app.py`:

```
pip install -r requirements.txt
python app.py
```
