#!/usr/bin/env python3

import os
from os.path import abspath, dirname
import sys
import subprocess

if __name__ == "__main__":
    root = abspath(dirname(__file__))
    os.chdir(root)

    # TODO: https://github.com/hgrecco/pint/issues/1969
    if sys.version_info < (3, 13):
        subprocess.check_call([sys.executable, "-m", "pytest", "-vv"])
