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

from lexer.lexer import Lexer, LexerExt
from parser.parser import Parser, ParserExt
from semantic.semantic import Semantic, SemanticExt
from llvm.llvm import LLVM, LLVMExt


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
        valid_ext = ['.vsop', '.vsopext']
        source_ext = os.path.splitext(source)[1]

        if source_ext not in valid_ext:
            print('main.py: error: extension of the input file must be "{}" or "{}"'.format(valid_ext[0], valid_ext[1]), file=sys.stderr)
            sys.exit(1)

        # We check if the VSOP file exist
        if not os.path.isfile(source):
            print('main.py: error: "{}" does not exist'.format(source), file=sys.stderr)
            sys.exit(1)

        # We tokenize the source file (remark : we do not save
        # the token list because lexing is done implicitly in
        # the parser after)
        if args.ext:
            vsop_lexer = LexerExt(source)
        else:
            vsop_lexer = Lexer(source)

        # If there is the '-lex' arg
        if args.lex:
            vsop_lexer.lex(dump=True)
            sys.exit(0)
        else:
            vsop_lexer.lex()

        # If we get there, we parse the VSOP file (remark : lexing
        # is done implicitly in the parsing so we reset the lexer
        # in order to not have conflict with previous information
        # of the last lexing)
        vsop_lexer.reset()

        if args.ext:
            vsop_parser = ParserExt(source, vsop_lexer)
        else:
            vsop_parser = Parser(source, vsop_lexer)

        ast = vsop_parser.parse()

        # If there is the '-parse' arg
        if args.parse:
            print(ast)
            sys.exit(0)

        # If we get there, we annotate the AST
        if args.ext:
            vsop_semantic = SemanticExt(source, ast)
        else:
            vsop_semantic = Semantic(source, ast)

        a_ast = vsop_semantic.annotate()

        # If there is the '-check' arg
        if args.check:
            print(a_ast)
            sys.exit(0)

        # If we get there, we generate the LLVM IR code
        if args.ext:
            vsop_llvm = LLVMExt(source, a_ast)
        else:
            vsop_llvm = LLVM(source, a_ast)

        llvm_ir = vsop_llvm.generate_ir()

        # If there is the '-llvm' arg
        if args.llvm:
            print(llvm_ir)
            sys.exit(0)

        # If we get there (no arg), we generate a native executable
        vsop_llvm.generate_exec(llvm_ir)
