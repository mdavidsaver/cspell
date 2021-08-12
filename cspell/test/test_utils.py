"""Copyright 2021 Michael Davidsaver See LICENSE
"""

from io import BytesIO
import unittest

from .. import loadjson, lineof

class TestMisc(unittest.TestCase):
    def test_json(self):
        J = b"""
            {
                "key": "value", // comment
                "other": "blah" // second
            }
        """

        with BytesIO(J) as FP:
            D = loadjson(FP)

        self.assertDictEqual(D, 
        {
            "key": "value",
            "other": "blah",
        })

    def test_linof(self):
        T = """this
    is a
test
"""
        self.assertEqual(lineof(T, slice(5,13), slice(9, 13)), "    is a")
        self.assertEqual(lineof(T, slice(0,15), slice(9, 13)), "    is a")
