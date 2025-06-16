import unittest
import numpy as np

from templating.renderer import Renderer
from templating.dsl import Arc, Feature, Line, Spline

class TestRenderer(unittest.TestCase):
    def test_render_basic_shapes(self):
        renderer = Renderer(32, 32)
        renderer.clear()
        features = [
            Feature((1.5, 1.5), [Line(10.2, 1.5), Line(10.2, 10.2), Line(1.5, 10.2)]),
            Feature((5.0, 5.0), [Spline([(8.0, 8.0), (5.0, 11.0)])]),
            Feature((30.0, 25.0), [Arc(25.0, 25.0, 5.0, 0.0, 90.0)]),
        ]
        renderer.draw_features(features)
        img = renderer.pixels
        # check canvas size
        self.assertEqual(img.shape, (32, 32, 3))
        # rectangle corners should be black
        self.assertTrue((img[2, 2] == [0, 0, 0]).all())
        self.assertTrue((img[10, 10] == [0, 0, 0]).any())
        # spline endpoints and arc start/end should have drawn pixels
        self.assertTrue((img[5, 5] == [0, 0, 0]).all())
        self.assertTrue((img[25, 30] == [0, 0, 0]).any())

if __name__ == "__main__":
    unittest.main()
