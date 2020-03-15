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
    """
    Check that the filename 'filename' ends
    with the extension 'valid_ext'.
    """

    # If there is no filename
    if filename is None:
        print_error('Invalid filename')

    # We get the extension
    ext = filename[-len(valid_ext):]

    # We compare the extension
    if ext != valid_ext:
        print_error('Extension of the input file must be {}'.format(valid_ext))


def print_error(*args, **kwargs):
    """
    Print an error in stderr and stop the
    execution with an error code.
    """

    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)
