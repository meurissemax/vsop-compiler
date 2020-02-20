"""
INFO0085-1 - Compilers
Project 1 : Lexical analysis
University of Liege - Academic year 2019-2020

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
    """Print a message in the stderr."""
    print(*args, file=sys.stderr, **kwargs)
