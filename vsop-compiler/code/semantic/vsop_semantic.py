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

        object_class.method['print'] = MethodSymbolTable(None, None, {'s': 'string'}, 'Object')
        object_class.method['printBool'] = MethodSymbolTable(None, None, {'b': 'bool'}, 'Object')
        object_class.method['printInt32'] = MethodSymbolTable(None, None, {'i': 'int32'}, 'Object')

        object_class.method['inputLine'] = MethodSymbolTable(None, None, {}, 'string')
        object_class.method['inputBool'] = MethodSymbolTable(None, None, {}, 'bool')
        object_class.method['inputInt32'] = MethodSymbolTable(None, None, {}, 'int32')

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
    # Semantic analysis #
    #####################

    def annotate(self):
        #################
        # Check classes #
        #################

        # Add 'Object' class to the symbol table
        self.__add_object()

        # Check classes of the program (cycle, name, ...)
        self.__check_classes()

        #########
        # Debug #
        #########
        
        for key, value in self.__symbol_table.items():
            print('Class "{}" with parent "{}".'.format(key, value.parent))
