import unittest
from templating.dsl import parse, Line, Spline, Arc, Feature

class TestDSL(unittest.TestCase):
    def test_parse(self):
        text = (
            "FEATURE 1.0 1\n"
            "LINE 2 2\n"
            "END\n"
            "FEATURE 5.0 0\n"
            "ARC 0 0 5 0 90\n"
            "SPLINE 0 0 1 1 2 0\n"
            "END\n"
        )
        features = parse(text)
        self.assertEqual(len(features), 2)
        self.assertEqual(features[0], Feature((1.0, 1.0), [Line(2.0, 2.0)]))
        self.assertEqual(features[1].start, (5.0, 0.0))
        self.assertIsInstance(features[1].segments[0], Arc)
        self.assertEqual(
            features[1].segments[1],
            Spline([(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]),
        )

if __name__ == '__main__':
    unittest.main()
