#!/usr/bin/env python3

import re
import sys

from setuptools import setup


requires = []
if sys.version_info < (2, 7):
    requires.append('argparse')

def requires_from_file(filename):
    requirements = []
    with open(filename, 'r') as requirements_fp:
        for line in requirements_fp.readlines():
            match = re.search('^\s*([a-zA-Z][^#]+?)(\s*#.+)?\n$', line)
            if match:
                requirements.append(match.group(1))
    return requirements


setup(
    install_requires=requires_from_file('requirements.txt'),
)

