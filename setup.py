#!/usr/bin/env python3

from setuptools import setup

setup(
    name='cspell',
    version='0.0.1a1',
    description='Context aware spelling check for C/C++ source code files.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mdavidsaver/cspell',
    author='Michael Davidsaver',
    author_email='mdavidsaver@gmail.com',
    license='GPLv3',
    python_requires='>=3.7',

    install_requires = [
        'hunspell',
    ],

    packages=[
        'cspell',
        'cspell.test',
    ],

    entry_points = {
        'console_scripts': ['cspell=cspell:main'],
    },
)
