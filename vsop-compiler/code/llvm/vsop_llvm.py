"""
INFO0085-1 - Compilers
University of Liege
Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""


###########
# Classes #
###########

class LLVM:
    ###############
    # Constructor #
    ###############

    def __init__(self, a_ast):
        # We save the annotated AST to generate LLVM code
        self.__a_ast = a_ast

    ###################
    # Code generation #
    ###################

    def generate(self):
        return 'TO DO'

    def generate_exec(self, llvm_code):
        print('TO DO')
