#!/usr/bin/env python3

"""
INFO0085-1 - Compilers
University of Liege
Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""

###########
# Imports #
###########

import os
import sys
import argparse

from lexer.vsop_lexer import Lexer
from parser.vsop_parser import Parser
from semantic.vsop_semantic import Semantic


########
# Main #
########

if __name__ == '__main__':
    #########################
    # Initialize arg parser #
    #########################

    # We instantiate the parser (for executable arguments)
    arg_parser = argparse.ArgumentParser(description='VSOPC is a compiler for the object-oriented language VSOP. By default, VSOPC generate a native executable.')

    # We add executable arguments
    arg_parser.add_argument('-ext', help='treat input source file as an extended VSOP file', action='store_true')

    group = arg_parser.add_mutually_exclusive_group()
    group.add_argument('-lex', help='dump tokens on stdout and stop', action='store_true')
    group.add_argument('-parse', help='dump parsed AST on stdout and stop', action='store_true')
    group.add_argument('-check', help='dump annotated AST on stdout and stop', action='store_true')
    group.add_argument('-llvm', help='dump LLVM IR on stdout and stop', action='store_true')

    arg_parser.add_argument('source', help='path to the VSOP source file', type=str)

    # We parse arguments
    args = arg_parser.parse_args()

    #######################
    # Argument management #
    #######################

    if args.source:
        # We get the VSOP source file path
        source = args.source

        # We check the extension of the file
        valid_ext = '.vsop'
        source_ext = source[-len(valid_ext):]

        if source_ext != valid_ext:
            print('main.py: error: extension of the input file must be "{}"'.format(valid_ext), file=sys.stderr)
            sys.exit(1)

        # We check if the VSOP file exist
        if not os.path.isfile(source):
            print('main.py: error: "{}" does not exist'.format(source), file=sys.stderr)
            sys.exit(1)

        # We instantiate lexer
        vsop_lexer = Lexer(source)

        # If there is the '-lex' arg
        if args.lex:
            vsop_lexer.dump_tokens()
            sys.exit(0)

        # If we get here, we parse the VSOP file (remark : lexing
        # is done implicitly in the parsing)
        vsop_parser = Parser(source, vsop_lexer)
        ast = vsop_parser.parse()

        # If there is the '-parse' arg
        if args.parse:
            print(ast)
            sys.exit(0)

        # If we get there, we annotate the AST
        vsop_semantic = Semantic(ast)
        a_ast = vsop_semantic.annotate()

        # If there is the '-check' arg
        if args.check:
            print(a_ast)
            sys.exit(0)

        # TO DO : '-llvm' and '-ext' arguments

        # If we get here, we generate a native executable
        print('TO DO : generate a native executable.')
