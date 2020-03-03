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

def print_error(*args, **kwargs):
    """
    Print an error in stderr and stop the
    execution with an error code.
    """

    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)
