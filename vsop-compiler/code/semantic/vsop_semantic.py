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

class Semantic:
    def __init__(self, ast):
        self.ast = ast

    def annotate(self):
        return self.ast
