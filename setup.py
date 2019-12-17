from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import os
from codecs import open
from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

#To prepare a new release
#python setup.py sdist upload

setup(name='altimetry',
    version='0.1.0',
    description='Libraries and command-line utilities for UAF airborne altimetry project',
    author='Anthony Arendt',
    author_email='arendta@uw.edu',
    license='MIT',
    url='https://github.com/aaarendt/ingestAltimetry',
    packages=find_packages(),
    long_description=long_description,
    scripts=['AltPy/altimetry.py', 'AltPy/main.py', 'AltPy/UpdateDb.py']
)