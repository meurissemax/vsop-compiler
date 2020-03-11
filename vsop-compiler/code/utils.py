"""
INFO0085-1 - Compilers
University of Liege
Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""

#############
# Libraries #
#############

from __future__ import print_function

import sys


#############
# Functions #
#############

def check_filename(filename, valid_ext):
    if filename is None:
        print_error('Invalid filename')

    ext = filename[-len(valid_ext):]

    if ext != valid_ext:
        print_error('Extension of the input file must be .vsop')

    return filename


def print_error(*args, **kwargs):
    """
    Print an error in stderr and stop the
    execution with an error code.
    """

    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)
