#!/usr/bin/env python3
"""Copyright 2021 Michael Davidsaver See LICENSE
"""
"""Spelling correction for C/C++ code files
"""

import sys
import os
import re
import logging
import enum
import json
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from concurrent.futures import ProcessPoolExecutor, FIRST_EXCEPTION, wait

import hunspell

# separation of content to spell check
comment = re.compile(r'''
    /\*(.*?)\*/      # C comment
    |
    //(.*?)$     # C++ end of line
    |
    "((?:[^"\n]|\")*)" # String literal
''', re.MULTILINE|re.DOTALL|re.VERBOSE)

# extraction of words from content
textword = re.compile(r'\b[a-zA-Z][a-z\'-]*(?:-[a-zA-Z]*)?[a-z]\b')

# separators bounding a code term
codesep = r'[\s/,:;<>()\[\]+.-]'

# extraction of terms from code
codeword = re.compile(r'(?<='+codesep+') [a-zA-Z_][a-zA-Z0-9_]+ (?='+codesep+')', re.VERBOSE)

_log = logging.getLogger('cspell')

class Action(enum.Enum):
    Nothing = 0
    Diff = 1
    Edit = 2

def getargs():
    from argparse import ArgumentParser
    P = ArgumentParser()
    P.add_argument('-L', '--language', default='en_US',
                   help='Select base HunSpell dictionary')
    P.add_argument('-D', '--add-dict', action='append', dest='extra', default=[],
                   help='Additional HunSpell dictionary file')
    P.add_argument('-W', '--out-dict',
                   help='Write out HunSpell dictionary containing ignores from code')

    P.add_argument('-C', '--corrections', action='append', default=[],
                   help='Add corrections JSON file')
    P.add_argument('-F', '--out-corrections',
                   help='Write new candidate corrections')

    P.add_argument('-n', '--dry-run', dest='action', action='store_const', const=Action.Diff, default=Action.Nothing,
                   help='Show diff of each file instead of modifying')
    P.add_argument('-M', '--modify', dest='action', action='store_const', const=Action.Edit,
                   help='Apply changes to each file')

    P.add_argument('-d', '--debug', dest='level', action='store_const', const=logging.DEBUG, default=logging.INFO,
                   help='Make more noise')
    P.add_argument('-q', '--quiet', dest='level', action='store_const', const=logging.WARN,
                   help='Make less noise')

    P.add_argument('--ignore-ext', action='store_true',
                   help='Disable filtering by file extension')
    P.add_argument('-f', '--inputs', action='append', default=[],
                   help='Files containing file names, one per line')
    P.add_argument('files', nargs='*',
                   help='Input C code files')
    return P

def searchiter(R, text, start=0, end=-1):
    if end==-1:
        end = len(text)

    while start<end:
        M = R.search(text, start, end)
        if not M:
            break

        if M.start(0) > start:
            yield None, slice(start, M.start(0))

        start = M.end(0)
        yield M, slice(M.start(0), start)

    if start<end:
        yield None, slice(start, end)

def loadjson(FP):
    content = FP.read()
    def replace(M):
        # replace with equivalent whitespace
        return re.sub(rb'[^\n]', b' ', M.group(0))
    content = re.sub(rb'//.*', replace, content)
    return json.loads(content)

def lineof(S, Stok, Sword):
    start = S.rfind('\n', Stok.start, Sword.start) # implicitly skips newline, or becomes zero
    if start==-1:
        start = Stok.start
    else:
        start += 1

    stop = S.find('\n', Sword.stop, Stok.stop)
    if stop==-1:
        stop = Stok.stop

    return S[start:stop]

H=None
def buildH(args):
    # HunSpell can't be pickled for use with ProcessPoolExecutor
    # so we must build one in every worker process
    global H

    if H is None:
        if not os.path.isfile(args.language):
            dic = '/usr/share/hunspell/%s.dic'%args.language
            aff = '/usr/share/hunspell/%s.aff'%args.language

        else:
            dic = args.language
            aff = os.path.splitext(args.language)[0] + '.aff'

        H = hunspell.HunSpell(dic, aff)
        for D in args.extra:
            try:
                H.add_dic(D)
            except:
                _log.exception(D)
                sys.exit(1)

    return H

def main(args=None):
    if args is None:
        args = getargs().parse_args()

    logging.basicConfig(level=args.level)

    H = buildH(args)

    correct = {}
    for cfile in args.corrections:
        with open(cfile, 'rb') as F:
            correct.update(loadjson(F))

    for filelist in args.inputs:
        basedir = os.path.dirname(filelist)
        with open(filelist, 'r') as F:
            args.files += [os.path.join(basedir, fname.strip()) for fname in F]

    if not args.ignore_ext:
        def iscsrc(fname):
            ext = os.path.splitext(fname)[1].lower()
            return ext in ('.c', '.h', '.hpp', '.cpp', '.hxx', '.cxx', '.h++', '.c++')
        args.files = list(filter(iscsrc, args.files))

    newcorrect = {}
    codewords = set()

    with ProcessPoolExecutor() as pool:
        jobs = pool.map(partial(procfile,
                                args=args, correct=correct),
                      args.files)
        for NC, NW in jobs:
            newcorrect.update(NC)
            codewords.update(NW)

    # late removal of code words using complete list
    for cword in codewords:
        newcorrect.pop(cword, None)

    # stablize ordering of outputs
    codewords = [cword for cword in codewords if not H.spell(cword)]
    codewords.sort()

    newcorrect = list(newcorrect.items())
    newcorrect.sort()

    if args.out_dict:
        with open(args.out_dict, 'w') as F:
            F.write('%d\n'%len(codewords))
            for cword in codewords:
                F.write('%s\n'%cword)

    if args.out_corrections:
        with open(args.out_corrections, 'w') as F:
            F.write('{')
            first=True
            for word, corr in newcorrect:
                if first:
                    F.write('\n')
                    first = False
                else:
                    F.write('  ,\n')

                F.write('  "%s": "%s"'%(word, corr.suggestions[0]))

                if len(corr.suggestions)>1:
                    F.write('\n  // %s\n'%(' '.join(['"%s"'%S for S in corr.suggestions[1:]])))
                for ctxt in corr.context:
                    F.write('  // ... %s\n'%ctxt)

            F.write('}\n')

@dataclass
class Correction:
    suggestions: [str]
    context: [str] =field(default_factory=list)

def procfile(fname, args=None, correct=None):
    H = buildH(args)

    try:
        with open(os.path.expanduser(fname), 'r') as F:
            input = F.read()
    except:
        _log.exception('Skipping: "%s"'%fname)
        return
    _log.info('Processing: "%s"'%fname)

    output = []
    newcorrect = {}
    codewords = set()

    pos = 0
    for M, span in searchiter(comment, input):

        if M is None:
            # code fragment
            codefrag = input[span]

            output.append(codefrag)
            _log.debug('CODE: %s', codefrag)
            for C, cspan in searchiter(codeword, input, span.start, span.stop):
                if C and C.group(0) not in codewords:
                    _log.debug('CODE WORD: %s', C.group(0))
                    codewords.add(C.group(0))

        else:
            # comment

            _log.debug('TEXT: %s "%s"', M.span(M.lastindex), M.group(M.lastindex))

            wstart, wend = M.span(M.lastindex)

            for W, wspan in searchiter(textword, input, span.start, span.stop):
                if not W: # non-word
                    _log.debug('SKIP: %s "%s"', wspan, input[wspan])
                    output.append(input[wspan])

                else:
                    word = W.group(0)
                    _log.debug('WORD: %s "%s"', wspan, word)

                    replace = correct.get(word)

                    if isinstance(replace, str):
                        _log.info('REPLACE "%s" -> "%s"', word, replace)
                        word = replace

                    elif word in codewords:
                        pass

                    elif not H.spell(word):
                        suggestions = H.suggest(word)
                        if suggestions is None or len(suggestions)==0:
                            pass # hunspell does this sometimes...

                        else:
                            if word not in newcorrect:
                                newcorrect[word] = Correction(suggestions)
                                _log.info('SPELL: %s "%s" -> %s', wspan, word, suggestions)

                            newcorrect[word].context.append(lineof(input, span, wspan).strip())

                    output.append(word)

    output = ''.join(output)
    if input!=output:
        if args.action==Action.Diff:
            import difflib
            for chunk in difflib.unified_diff(input.splitlines(), output.splitlines(), fname, fname):
                print(chunk)

        elif args.action==Action.Edit:
            with open(fname, 'w') as F:
                F.write(output)

        else:
            _log.info('Changes in: %s', fname)

    return newcorrect, codewords
