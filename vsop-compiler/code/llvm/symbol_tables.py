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
    def __init__(self, name):
        # Save the name of the element associated with the
        # symbol table
        self.name = name


class ClassSymbolTable(SymbolTable):
    def __init__(self, name, parent, struct):
        super().__init__(name)

        # Symbol table of the parent's class
        self.parent = parent

        # Structures defininf the class
        self.struct = struct
        self.struct_vtable = None

        # List of fields and methods of the symbol table
        # For each field, his name is associated with his
        # type.
        # For each method, his name is associated with his
        # symbol table.
        self.fields = {}
        self.methods = {}


class FieldSymbolTable(SymbolTable):
    def __init__(self, name, _type):
        super().__init__(name)

        # Type of the field
        self.type = _type

        # Value of the field
        self.value = None


class MethodSymbolTable(SymbolTable):
    def __init__(self, name, function_type, function):
        super().__init__(name)

        # Save 'FunctionType' object of the method
        self.function_type = function_type

        # Save 'Function' object of the method
        self.function = function


class LetSymbolTable(SymbolTable):
    def __init__(self, field_name, _type):
        super().__init__('let')

        # Save field and his type defined by the let
        self.field = {field_name: FieldSymbolTable(lineno, column, field_name, _type)}
