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

from vsop_lexer import Lexer
from vsop_parser import Parser


#####################
# General variables #
#####################

VALID_EXT = '.vsop'

LEXER_DEBUG = False

PARSER_PARSETAB = 'vsop_parsetab'
PARSER_DEBUG = False


########
# Main #
########

if __name__ == '__main__':
    ##############
    # Arg parser #
    ##############

    # We instantiate the parser (for executable arguments)
    arg_parser = argparse.ArgumentParser()

    # We add executable arguments
    arg_parser.add_argument('-lex', '--lex', help='path to the VSOP file to lex')
    arg_parser.add_argument('-parse', '--parse', help='path to the VSOP file to parse')

    # We get arguments' value
    args = arg_parser.parse_args()

    ############
    # -lex arg #
    ############

    if args.lex:
        # We check the '-lex' argument value
        utils.check_filename(args.lex, VALID_EXT)

        # We instantiate the lexer
        vsop_lexer = Lexer(args.lex, LEXER_DEBUG)
        vsop_lexer.build()

        # We lex the content of the file and print tokens
        vsop_lexer.lex()

    ##############
    # -parse arg #
    ##############

    if args.parse:
        # We check the '-parse' argument value
        utils.check_filename(args.parse, VALID_EXT)

        # We instantiate the lexer
        vsop_lexer = Lexer(args.parse, LEXER_DEBUG)
        vsop_lexer.build()

        # We instantiate the parser
        vsop_parser = Parser(args.parse, PARSER_DEBUG, vsop_lexer.lexer, vsop_lexer.tokens, PARSER_PARSETAB)
        vsop_parser.build()

        # We parse the content of the file
        vsop_parser.parse()

        # We print the asbtract syntax tree
        vsop_parser.print_ast()

    ##########
    # no arg #
    ##########

    if not args.lex and not args.parse:
        utils.print_error('Usage : vsopc [-lex|-parse] <SOURCE-FILE>')
