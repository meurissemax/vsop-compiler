#!/usr/bin/env python3

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

import utils
import argparse

from lexer import Lexer


#####################
# General variables #
#####################

VALID_EXT = '.vsop'


########
# Main #
########

if __name__ == '__main__':
    # We instantiate the parser (for executable arguments)
    parser = argparse.ArgumentParser()

    # We add executable arguments
    parser.add_argument('-lex', '--lex', help='path to the VSOP file to lex')

    # We get arguments' value
    args = parser.parse_args()

    # If there is '-lex' argument value
    if args.lex:
        # We get the '-lex' argument value
        filename = args.lex

        # We check the filename extension
        ext = filename[-len(VALID_EXT):]

        if ext == VALID_EXT:
            # We instantiate and build the lexer
            lexer = Lexer(filename)
            lexer.build()

            # We lex the content of the file
            lexer.lex()
        else:
            utils.print_error('Extension of the input file must be .vsop')
    else:
        utils.print_error('Usage : vsopc -lex <SOURCE-FILE>')
