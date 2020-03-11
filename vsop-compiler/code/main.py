#!/usr/bin/env python3

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

import utils
import argparse

from lexer import Lexer
from parser import Parser


#####################
# General variables #
#####################

VALID_EXT = '.vsop'


########
# Main #
########

if __name__ == '__main__':
    # We instantiate the parser (for executable arguments)
    arg_parser = argparse.ArgumentParser()

    # We add executable arguments
    arg_parser.add_argument('-lex', '--lex', help='path to the VSOP file to lex')
    arg_parser.add_argument('-parse', '--parse', help='path to the VSOP file to parse')

    # We get arguments' value
    args = arg_parser.parse_args()

    # If there is '-lex' argument value
    if args.lex:
        # We get the '-lex' argument value
        filename = utils.check_filename(args.lex, VALID_EXT)

        # We instantiate and build the lexer
        lexer = Lexer(filename)
        lexer.build()

        # We lex the content of the file
        lexer.lex()

    # If there is '-parse' argument value
    if args.parse:
        # We get the '-parse' argument value
        filename = utils.check_filename(args.parse, VALID_EXT)

        # We instantiate and build the lexer
        lexer = Lexer(filename)
        lexer.build()

        # We instantiate and build the parser
        parser = Parser(filename, lexer.tokens)
        parser.build()

        # We parse the content of the file
        parser.parse(lexer.lexer)

    # If there is neither '-lex' or '-parse' argument value
    if not args.lex and not args.parse:
        utils.print_error('Usage : vsopc [-lex|-parse] <SOURCE-FILE>')
