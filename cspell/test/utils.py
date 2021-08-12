"""Copyright 2021 Michael Davidsaver See LICENSE
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from .. import main, getargs
from .. import loadjson

class TestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._temp = TemporaryDirectory()
        self.tempdir = Path(self._temp.name)

    def tearDown(self):
        self._temp.cleanup()
        super().tearDown()

    def writeFile(self, name, content):
        """Write file in temporary location and return full Path
        """
        fullname = self.tempdir / name
        if isinstance(content, bytes):
            fullname.write_bytes(content)
        else:
            fullname.write_text(content)
        return fullname

    def cspell(self, args=[], expect_exit=0):
        args = getargs().parse_args(args)
        try:
            main(args)
            code = 0
        except SystemExit as e:
            code = e.code
        self.assertEqual(code, expect_exit)

    def loadj(self, P):
        with P.open('rb') as F:
            return loadjson(F)

    def loaddic(self, P):
        lines = P.read_text().splitlines()
        nlines = int(lines[0])
        self.assertEqual(nlines, len(lines)-1)
        return lines[1:]

    def writedic(self, name, words):
        fullname = self.tempdir / name
        with fullname.open('w') as F:
            F.write('%d\n'%len(words))
            for W in words:
                F.write('%s\n'%W)
        return fullname
