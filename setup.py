#!/usr/bin/env python

import re
import sys

from setuptools import setup, find_packages


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
    name='FiveRX Client',
    version='1.0',

    author='Felix Schwarz',
    author_email='info@schwarz.eu',
    license='proprietary',

    zip_safe=False,
    packages=find_packages(),
    namespace_packages = ['srw'],
    include_package_data=True,
    
    install_requires=requires_from_file('requirements.txt'),
    entry_points="""

    [console_scripts]
    fiverx-fetch-prescriptions = srw.fiverx_client.fetch_prescriptions:main
    srwlink-client = srw.fiverx_client.cli_client:client_main
    srwlink-extract-payload = srw.fiverx_client.extract_payload:extract_payload_main
    """,
)

