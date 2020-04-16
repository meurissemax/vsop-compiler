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
    def __init__(self, lineno, column, name):
        # Save the position of the element associated
        # with the symbol table
        self.lineno = lineno
        self.column = column

        # Save the name of the element associated with the
        # symbol table
        self.name = name

    def lookup_field(self, field_name):
        return None

    def lookup_method(self, method_name):
        return None


class ClassSymbolTable(SymbolTable):
    def __init__(self, lineno, column, name):
        super().__init__(lineno, column, name)

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

    def lookup_field(self, field_name):
        if self.fields[field_name] is not None:
            return self.fields[field_name]
        else:
            if self.parent is not None:
                return self.parent.lookup_field(field_name)

        return None

    def lookup_method(self, method_name):
        if self.methods[method_name] is not None:
            return self.methods[method_name]
        else:
            if self.parent is not None:
                return self.parent.lookup_method(method_name)

        return None


class FieldSymbolTable(SymbolTable):
    def __init__(self, lineno, column, name, _type):
        super().__init__(lineno, column, name)

        # Save type of the field
        self.type = _type


class MethodSymbolTable(SymbolTable):
    def __init__(self, lineno, column, name, args, ret_type):
        super().__init__(lineno, column, name)

        # Save argument and return type
        self.args = args
        self.ret_type = ret_type

    def lookup_field(self, field_name):
        return self.args[field_name]


class LetSymbolTable(SymbolTable):
    def __init__(self, lineno, column, field_name, _type):
        super().__init__(lineno, column, 'let')

        # Save field and his type defined by the let
        self.field = {field_name: FieldSymbolTable(lineno, column, field_name, _type)}

    def lookup_field(self, field_name):
        return self.field[field_name]
