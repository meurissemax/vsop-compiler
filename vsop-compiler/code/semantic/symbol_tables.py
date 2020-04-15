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

class SymbolTable:
    def __init__(self, lineno, column):
        # Save the position of the element associated
        # with the symbol table
        self.lineno = lineno
        self.column = column

class ClassSymbolTable(SymbolTable):
    def __init__(self, lineno, column):
        super().__init__(lineno, column)

        # For each parent (by default, only one), his name
        # is associated with his symbol table in a tuple.
        self.parent = None

        # List of fields and methods of the symbol table
        # For each field, his name is associated with his
        # type.
        # For each method, his name is associated with his
        # symbol table.
        self.fields = {}
        self.methods = {}

class FieldSymbolTable(SymbolTable):
    def __init__(self, lineno, column, _type):
        super().__init__(lineno, column)

        # Save type of the field
        self.type = _type

class MethodSymbolTable(SymbolTable):
    def __init__(self, lineno, column, args, ret_type):
        super().__init__(lineno, column)

        # Save argument and return type
        self.args = args
        self.ret_type = ret_type
