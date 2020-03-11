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

import ast
import ply.yacc as yacc


###########
# Classes #
###########

class Parser:
    ###############
    # Constructor #
    ###############

    def __init__(self, filename):
        self.__filename = filename

    #################
    # Grammar rules #
    #################

    def p_program(p):
        'program : class'
        self.ast.add_class(p[1])

    def p_class(p):
        pass

    ############################
    # Build and use the parser #
    ############################

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    def export(self):
        return self.parser

    def parse(self, lexer):
        self.ast = Program()
        self.parser.parse(lexer=lexer)

        print(ast)
