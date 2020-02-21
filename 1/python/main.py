#!/usr/bin/python3

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

import argparse
import utils

from lexer import Lexer


#####################
# General variables #
#####################

VALID_EXT = '.vsop'


########
# Main #
########

if __name__ == '__main__':
    # Instantiate the parser (for executable arguments)
    parser = argparse.ArgumentParser()

    # Add executable arguments
    parser.add_argument('-lex', '--lex', help='path to the VSOP file to lex')

    # Get arguments' value
    args = parser.parse_args()

    # Get the '-lex' argument value
    if args.lex:
        filename = args.lex

        # Check the filename extension
        ext = filename[-len(VALID_EXT):]

        if ext == VALID_EXT:
            # Get the file content
            with open(filename, 'r', encoding='ascii') as f:
                data = f.read()
                data = data.replace('\t', '    ')

            # Instantiate the lexer
            lexer = Lexer(filename, data)
            lexer.build()

            # Lex the content of the file
            lexer.lex()
        else:
            utils.print_error('Extension of the input file must be .vsop')
    else:
        utils.print_error('Usage : vsopc -lex <SOURCE-FILE>')
