"""Copyright 2021 Michael Davidsaver See LICENSE
"""

from .utils import TestCase

class TestCollect(TestCase):
    maxDiff = None

    def test_c(self):
        code = self.writeFile('test.c', r'''
                              /** Copyright 2021 Michael Davidsaver
                               *  Who cann't spelll rite
                               */
                              #include <stdio.h>
                              void myfunc(int thearg) {
                                  // myfunc() is a functon on thearg and retval
                                  int retval = thearg;
                                  if(thearg==42)
                                      printf("thearg is amagic value\n");
                                  /* another commment */
                                  return retval;
                              }
''')

        cdict = self.tempdir / 'code.dic'
        corrections = self.tempdir / 'correct.json'

        udict = self.writedic('user.dic', ['Davidsaver'])

        self.cspell(['-L', 'en_US', '-D', str(udict), '-W', str(cdict), '-F', str(corrections), str(code)])

        codewords = self.loaddic(cdict)
        self.assertListEqual(codewords, [
            'myfunc',
            'printf',
            'retval',
            'thearg'
        ])

        corr = self.loadj(corrections)
        self.assertSetEqual(set(corr.keys()), {
            'amagic',
            "cann't",
            'commment',
            'functon',
            'spelll',
        })

        self.assertEqual(corrections.read_text(), 
r"""{
  "amagic": "magic"
  // "a magic"
  // ... "thearg is amagic value\n"
  ,
  "cann't": "can't"
  // "cannot"
  // ... *  Who cann't spelll rite
  ,
  "commment": "comment"
  // "commitment" "commencement" "commandment" "commence"
  // ... /* another commment */
  ,
  "functon": "function"
  // "functor" "futon"
  // ... // myfunc() is a functon on thearg and retval
  ,
  "spelll": "spell"
  // "spells" "spell l"
  // ... *  Who cann't spelll rite
}
""")

    def test_cxx(self):
        code = self.writeFile('test.cpp', r'''
                              /** Copyright 2021 Michael Davidsaver
                               *  Who cann't spelll rite
                               */
                              #include <cstdio>
                              class mykls { void myfunc(int); };
                              // mykls::myfunc() is my name
                              void mykls::myfunc(int thearg) {
                                  // myfunc() is a methd of mykls on thearg and retval
                                  int retval = thearg;
                                  if(thearg==42)
                                      printf("thearg is amagic value\n");
                                  /* another commment */
                                  printf("another message\n");
                                  return retval;
                              }
''')

        cdict = self.tempdir / 'code.dic'
        corrections = self.tempdir / 'correct.json'

        udict = self.writedic('user.dic', ['Davidsaver'])

        self.cspell(['-L', 'en_US', '-D', str(udict), '-W', str(cdict), '-F', str(corrections), str(code)])

        codewords = self.loaddic(cdict)
        self.assertListEqual(codewords, [
            'cstdio',
            'myfunc',
            'mykls',
            'printf',
            'retval',
            'thearg'
        ])

        corr = self.loadj(corrections)
        self.assertSetEqual(set(corr.keys()), {
            'amagic',
            "cann't",
            'commment',
            'methd',
            'spelll',
        })

        self.assertEqual(corrections.read_text(), 
r"""{
  "amagic": "magic"
  // "a magic"
  // ... "thearg is amagic value\n"
  ,
  "cann't": "can't"
  // "cannot"
  // ... *  Who cann't spelll rite
  ,
  "commment": "comment"
  // "commitment" "commencement" "commandment" "commence"
  // ... /* another commment */
  ,
  "methd": "meths"
  // "meth" "method" "meted" "meth d"
  // ... // myfunc() is a methd of mykls on thearg and retval
  ,
  "spelll": "spell"
  // "spells" "spell l"
  // ... *  Who cann't spelll rite
}
""")
