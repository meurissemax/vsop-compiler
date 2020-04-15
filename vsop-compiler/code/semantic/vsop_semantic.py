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

import sys

from semantic.symbol_tables import *


###########
# Classes #
###########

class Semantic:
    ###############
    # Constructor #
    ###############

    def __init__(self, filename, ast):
        # We save the VSOP source file name
        self.__filename = filename

        # We save the AST to annotate it later
        self.__ast = ast

        # Base symbol table that will contains all
        # the symbol tables of the classes
        self.__symbol_table = {}

        # We define the list of primitive types
        self.__primitive_types = ['unit', 'bool', 'int32', 'string']

    ##################
    # Error handling #
    ##################

    def __print_error(self, lineno, column, message):
        """
        Prints an error on stderr in the right format
        and exits the parser.
        """

        print('{}:{}:{}: semantic error: {}'.format(self.__filename, lineno, column, message), file=sys.stderr)
        sys.exit(1)

    ######################
    # Classes management #
    ######################

    def __add_object(self):
        object_class = ClassSymbolTable(None, None)

        object_class.methods['print'] = MethodSymbolTable(None, None, {'s': 'string'}, 'Object')
        object_class.methods['printBool'] = MethodSymbolTable(None, None, {'b': 'bool'}, 'Object')
        object_class.methods['printInt32'] = MethodSymbolTable(None, None, {'i': 'int32'}, 'Object')

        object_class.methods['inputLine'] = MethodSymbolTable(None, None, {}, 'string')
        object_class.methods['inputBool'] = MethodSymbolTable(None, None, {}, 'bool')
        object_class.methods['inputInt32'] = MethodSymbolTable(None, None, {}, 'int32')

        self.__symbol_table['Object'] = object_class

    def __check_classes(self):
        # Save each class declaration (and check if it already exist or not)
        for c in self.__ast.classes:
            if c.name == 'Object':
                self.__print_error(c.lineno, c.column, 'can not redefine class "Object"')
            elif c.name in self.__symbol_table:
                already = self.__symbol_table[c.name]
                
                self.__print_error(c.lineno, c.column, 'class "{}" already defined at {}:{}'.format(c.name, already.lineno, already.column))
            else:
                self.__symbol_table[c.name] = ClassSymbolTable(c.lineno, c.column)
                
        # Check the parent of each class
        for c in self.__ast.classes:
            if c.parent not in self.__symbol_table:
                self.__print_error(c.lineno, c.column, 'parent class "{}" does not exist'.format(c.parent))
            elif c.name == c.parent:
                self.__print_error(c.lineno, c.column, 'class "{}" cannot inherit by itself'.format(c.name))
            else:
                self.__symbol_table[c.name].parent = (c.parent, self.__symbol_table[c.parent])

        # Check possible cycles
        for key, value in self.__symbol_table.items():
            if key != 'Object':
                c = key
                parent = value.parent[0]

                while parent != 'Object':
                    c = parent
                    parent = self.__symbol_table[c].parent[0]

                    if parent == key:
                        self.__print_error(value.lineno, value.column, 'class "{}" can not be extend in a cycle'.format(key))

        # Check that a 'Main' class is provided
        if 'Main' not in self.__symbol_table:
            self.__print_error(1, 1, 'a class "Main" must be provided')

    #####################
    # Fields management #
    #####################

    def __check_fields(self):
        # We iterate over each class
        for c in self.__ast.classes:

            # For each class, we iterate over its fields
            for f in c.fields:

                # We check if field is named 'self'
                if f.name == 'self':
                    self.__print_error(f.lineno, f.column, 'a field can not be named "self"')

                # We check if field is already defined
                elif f.name in self.__symbol_table[c.name].fields:
                    already = self.__symbol_table[c.name].fields[f.name]

                    self.__print_error(f.lineno, f.column, 'field "{}" already defined at {}:{}'.format(f.name, already.lineno, already.column))

                # If the type of field is not primitive, we check that the class associated
                # to his type exist
                elif f.type not in self.__primitive_types and f.type not in self.__symbol_table:
                    self.__print_error(f.lineno, f.column, 'undefined type "{}" for field "{}"'.format(f.type, f.name))

                # Else we possibly add the field
                else:
                    # We check if the field override a parent field
                    parent = self.__symbol_table[c.name].parent

                    while parent != None:
                        parent_name = parent[0]

                        if f.name in self.__symbol_table[parent_name].fields:
                            already = self.__symbol_table[parent_name]

                            self.__print_error(f.lineno, f.column, 'field "{}" already defined in parent at {}:{} and can not be override'.format(f.name, already.lineno, already.column))
                        else:
                            parent = self.__symbol_table[parent_name].parent

                    # If not, we add the field
                    self.__symbol_table[c.name].fields[f.name] = FieldSymbolTable(f.lineno, f.column, f.type)

    #################
    # Check methods #
    #################

    def __check_methods(self):
        # We iterate over each class
        for c in self.__ast.classes:

            # For each class, we iterate over its methods
            for m in c.methods:

                # We check if method is already defined
                if m.name in self.__symbol_table[c.name].methods:
                    already = self.__symbol_table[c.name].methods[m.name]

                    self.__print_error(m.lineno, m.column, 'method "{}" already defined at {}:{}'.format(m.name, already.lineno, already.column))

                # Else we possibly add the method
                else:
                    # We check if multiple parameters have the same name
                    f_names = []

                    for f in m.formals:
                        f_names = f_names + [f.name]
                    
                    if len(set(f_names)) != len(f_names):
                        self.__print_error(m.lineno, m.column, 'multiple formals can not have the same name')

                    # We check type of formals and return value
                    for f in m.formals:
                        if f.type not in self.__primitive_types and f.type not in self.__symbol_table:
                            self.__print_error(f.lineno, f.column, 'undefined type "{}" for formal "{}"'.format(f.type, f.name))

                    if m.ret_type not in self.__primitive_types and m.ret_type not in self.__symbol_table:
                        self.__print_error(m.lineno, m.column, 'undefined return type "{}" for method "{}"'.format(m.ret_type, m.name))

                    # We check if the method is defined in a parent. If it is the cas, we check
                    # that the override is valid.
                    parent = self.__symbol_table[c.name].parent
                    
                    while parent != None:
                        parent_name = parent[0]

                        # If method overrides a parent's method
                        if m.name in self.__symbol_table[parent_name].methods:
                            # We get types of all formals
                            args_type = []

                            for f in m.formals:
                                args_type += [f.type]

                            # We get parent method
                            parent_method = self.__symbol_table[parent_name].methods[m.name]

                            # If formals'type are different
                            if args_type != list(parent_method.args.values()):
                                self.__print_error(m.lineno, m.column, 'formals of method "{}" must have the same type of formals of method "{}" in parent class at {}:{}'.format(m.name, m.name, parent_method.lineno, parent_method.column))

                            # If return types are different
                            if m.ret_type != parent_method.ret_type:
                                self.__print_error(m.lineno, m.column, 'return type of method "{}" must be the same as the return type of corresponding method in parent class at {}:{}'.format(m.name, parent_method.lineno, parent_method.column))
                        
                        parent = self.__symbol_table[parent_name].parent

                    # If no error occurs, we add the method
                    args = {}

                    for f in m.formals:
                        args[f.name] = f.type

                    self.__symbol_table[c.name].methods[m.name] = MethodSymbolTable(m.lineno, m.column, args, m.ret_type)

        # We check that the 'Main' class has a 'main() : int32' method
        if 'main' in self.__symbol_table['Main'].methods:
            main_method = self.__symbol_table['Main'].methods['main']

            if len(main_method.args) == 0:
                if main_method.ret_type != 'int32':
                    self.__print_error(main_method.lineno, main_method.column, 'the "main" method of class "Main" must have "int32" as return type')
            else:
                self.__print_error(main_method.lineno, main_method.column, 'the "main" method of class "Main" can not have any formal')
        else:
            main_class = self.__symbol_table['Main']

            self.__print_error(main_class.lineno, main_class.column, 'class "Main" must have a "main() : int32" method')

    #####################
    # Semantic analysis #
    #####################

    def annotate(self):
        ###########
        # Classes #
        ###########

        # Add 'Object' class to the symbol table
        self.__add_object()

        # Check classes of the program (cycle, name, ...)
        self.__check_classes()

        ##########
        # Fields #
        ##########

        # Get and check all fields of each class
        self.__check_fields()

        ###########
        # Methods #
        ###########

        # Get and check methods of each class
        self.__check_methods()

        #########
        # Debug #
        #########
        
        for key, value in self.__symbol_table.items():
            # Class
            print('Class "{}" with parent "{}".'.format(key, value.parent))

            # Field(s)
            for key_f, value_f in value.fields.items():
                print('\tField "{}" of type "{}"'.format(key_f, value_f.type))

            parent = value.parent

            while parent != None:
                parent_name = parent[0]

                for k_p, v_p in self.__symbol_table[parent_name].fields.items():
                    print('\tField "{}" of type "{}" from parent "{}"'.format(k_p, v_p.type, parent_name))

                parent = self.__symbol_table[parent_name].parent

            print('\n')

            # Method(s)
            for key_m, value_m in value.methods.items():
                print('\tMethod "{}" with args "{}" and return type "{}"'.format(key_m, value_m.args, value_m.ret_type))

            parent = value.parent

            while parent != None:
                parent_name = parent[0]

                for k_p, v_p in self.__symbol_table[parent_name].methods.items():
                    print('\tMethod "{}" with args "{}" and return type "{}" from parent "{}"'.format(k_p, v_p.args, v_p.ret_type, parent_name))

                parent = self.__symbol_table[parent_name].parent

            print('\n')
