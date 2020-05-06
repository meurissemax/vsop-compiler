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

from parser.vsop_ast import *
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
        object_class = ClassSymbolTable(None, None, 'Object')

        object_class.methods['print'] = MethodSymbolTable(None, None, 'print', {'s': FieldSymbolTable(None, None, 's', 'string')}, 'Object')
        object_class.methods['printBool'] = MethodSymbolTable(None, None, 'printBool', {'b': FieldSymbolTable(None, None, 'b', 'bool')}, 'Object')
        object_class.methods['printInt32'] = MethodSymbolTable(None, None, 'printInt32', {'i': FieldSymbolTable(None, None, 'b', 'int32')}, 'Object')

        object_class.methods['inputLine'] = MethodSymbolTable(None, None, 'inputLine', {}, 'string')
        object_class.methods['inputBool'] = MethodSymbolTable(None, None, 'inputBool', {}, 'bool')
        object_class.methods['inputInt32'] = MethodSymbolTable(None, None, 'inputInt32', {}, 'int32')

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
                self.__symbol_table[c.name] = ClassSymbolTable(c.lineno, c.column, c.name)

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

    def __get_ancestors(self, class_name):
        ancestors = []

        if class_name != 'Object':
            ancestors += [class_name]
            parent = self.__symbol_table[class_name].parent

            while parent is not None:
                ancestors += [parent[0]]
                parent = self.__symbol_table[parent[0]].parent

        return ancestors

    def __get_common_ancestor(self, class_name_1, class_name_2):
        class_1_ancestors = self.__get_ancestors(class_name_1)
        class_2_ancestors = self.__get_ancestors(class_name_2)

        if class_name_1 in class_2_ancestors:
            return class_name_1
        elif class_name_2 in class_1_ancestors:
            return class_name_2
        else:
            return None

    def __get_current_class(self, stack):
        # We iterate over each element of the stack
        for symbol_table in stack:

            # We only look for 'ClassSymbolTable'
            if symbol_table.__class__.__name__ == 'ClassSymbolTable':
                return symbol_table.name

        return None

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

                    while parent is not None:
                        parent_name = parent[0]

                        if f.name in self.__symbol_table[parent_name].fields:
                            already = self.__symbol_table[parent_name].fields[f.name]

                            self.__print_error(f.lineno, f.column, 'field "{}" already defined in parent at {}:{} and can not be override'.format(f.name, already.lineno, already.column))
                        else:
                            parent = self.__symbol_table[parent_name].parent

                    # If not, we add the field
                    self.__symbol_table[c.name].fields[f.name] = FieldSymbolTable(f.lineno, f.column, f.name, f.type)

    def __check_fields_initializer(self):
        # We iterate over each class
        for c in self.__ast.classes:

            # For each class, we iterate over its fields
            for f in c.fields:

                # We check if the field has an initialize
                if f.init_expr is not None:

                    # We get the type of the initializing expression (with an empty stack because
                    # fields and methods of 'self' are not yet in the scope)
                    init_type = self.__analyze_expr(f.init_expr, [])

                    # If the expected field type is a primitive type
                    if f.type in self.__primitive_types:
                        if f.type != init_type:
                            self.__print_error(f.init_expr.lineno, f.init_expr.column, 'type of the initial expression must be "{}"'.format(f.type))

                    # If the expected field type is a 'class' type
                    else:
                        if f.type != init_type:
                            init_ancestors = self.__get_ancestors(init_type)

                            if f.type not in init_ancestors:
                                self.__print_error(f.init_expr.lineno, f.init_expr.column, 'type of the initial expression is not conform with static type "{}"'.format(f.type))

                            # We update the type of the field (because we will use the dynamic type of the field to check 'Call')
                            self.__symbol_table[c.name].fields[f.name].type = init_type

    def __lookup_field(self, stack, field_name):
        # We iterate over each symbol table on the stack
        for symbol_table in stack:

            # We search for the field in each symbol table
            field = symbol_table.lookup_field(field_name)

            if field is not None:
                return field

        return None

    ######################
    # Methods management #
    ######################

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

                    while parent is not None:
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
                            signature_args_type = []

                            for value in parent_method.args.values():
                                signature_args_type += [value.type]

                            if len(signature_args_type) != len(args_type):
                                self.__print_error(m.lineno, m.column, 'formals of method "{}" must have the same type of formals of method "{}" in parent class at {}:{}'.format(m.name, m.name, parent_method.lineno, parent_method.column))

                            for i in range(0, len(signature_args_type)):
                                # If argument type is a primitive type
                                if signature_args_type[i] in self.__primitive_types:
                                    if signature_args_type[i] != args_type[i]:
                                        self.__print_error(m.lineno, m.column, 'formals of method "{}" must have the same type of formals of method "{}" in parent class at {}:{}'.format(m.name, m.name, parent_method.lineno, parent_method.column))

                                # If argument type is a 'class' type
                                else:
                                    if signature_args_type[i] != args_type[i]:
                                        arg_ancestors = self.__get_ancestors(args_type[i])

                                        if signature_args_type[i] not in arg_ancestors:
                                            self.__print_error(m.lineno, m.column, 'formals of method "{}" must have the same type of formals of method "{}" in parent class at {}:{}'.format(m.name, m.name, parent_method.lineno, parent_method.column))

                            # If return types are different
                            if m.ret_type != parent_method.ret_type:
                                self.__print_error(m.lineno, m.column, 'return type of method "{}" must be the same as the return type of corresponding method in parent class at {}:{}'.format(m.name, parent_method.lineno, parent_method.column))

                        parent = self.__symbol_table[parent_name].parent

                    # If no error occurs, we add the method
                    args = {}

                    for f in m.formals:
                        args[f.name] = FieldSymbolTable(f.lineno, f.column, f.name, f.type)

                    self.__symbol_table[c.name].methods[m.name] = MethodSymbolTable(m.lineno, m.column, m.name, args, m.ret_type)

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

    def __check_methods_body(self):
        # We iterate over each class
        for c in self.__ast.classes:

            # For each class, we iterate over its methods
            for m in c.methods:

                # We get the return type of the method
                ret_type = m.ret_type

                # We get the type of the method's body
                stack = [self.__symbol_table[c.name].methods[m.name], self.__symbol_table[c.name]]
                block_type = self.__analyze_expr(m.block, stack)

                # If the expected return type is a primitive type
                if ret_type in self.__primitive_types:
                    if ret_type != block_type:
                        self.__print_error(m.block.lineno, m.block.column, 'return type of the method "{}" is not conform with his signature ("{}" expected but "{}")'.format(m.name, ret_type, block_type))

                # If the expected return type is a 'class' type
                else:
                    if ret_type != block_type:
                        block_type_ancestors = self.__get_ancestors(block_type)

                        if ret_type not in block_type_ancestors:
                            self.__print_error(m.block.lineno, m.block.column, 'return type of the method "{}" is not conform with his signature'.format(m.name))

    def __lookup_method(self, stack, method_name):
        # We iterate over each symbol table on the stack
        for symbol_table in stack:

            # We search for the method in each symbol table
            method = symbol_table.lookup_method(method_name)

            if method is not None:
                return method

        return method

    ##########################
    # Expressions management #
    ##########################

    def __analyze_expr(self, expr, stack):
        # We get the expression class (If, While, ...)
        expr_class = expr.__class__.__name__

        # We analyze the expression depending of his type (class)
        if expr_class == 'Block':
            for i in range(0, len(expr.expr_list) - 1):
                self.__analyze_expr(expr.expr_list[i], stack)

            expr_type = self.__analyze_expr(expr.expr_list[len(expr.expr_list) - 1], stack)
        elif expr_class == 'If':
            expr_type = self.__analyze_expr_if(expr, stack)
        elif expr_class == 'While':
            expr_type = self.__analyze_expr_while(expr, stack)
        elif expr_class == 'Let':
            expr_type = self.__analyze_expr_let(expr, stack)
        elif expr_class == 'Assign':
            expr_type = self.__analyze_expr_assign(expr, stack)
        elif expr_class == 'UnOp':
            expr_type = self.__analyze_expr_unop(expr, stack)
        elif expr_class == 'BinOp':
            expr_type = self.__analyze_expr_binop(expr, stack)
        elif expr_class == 'Call':
            expr_type = self.__analyze_expr_call(expr, stack)
        elif expr_class == 'New':
            expr_type = self.__analyze_expr_new(expr, stack)
        elif expr_class == 'Self':
            expr_type = self.__analyze_expr_self(expr, stack)
        elif expr_class == 'ObjectIdentifier':
            expr_type = self.__analyze_expr_obj_id(expr, stack)
        elif expr_class == 'Literal':
            expr_type = self.__analyze_expr_literal(expr, stack)
        elif expr_class == 'Unit':
            expr_type = self.__analyze_expr_unit(expr, stack)
        else:
            self.__print_error(expr.lineno, expr.column, 'unknown expression')

        # We set the expression type (we update the node in the AST)
        expr.set_expr_type(expr_type)

        # We return the type of the expression
        return expr_type

    def __analyze_expr_if(self, expr, stack):
        # We get the type of the conditional expression
        cond_type = self.__analyze_expr(expr.cond_expr, stack)

        # We check the type of the conditional expression
        if cond_type != 'bool':
            self.__print_error(expr.cond_expr.lineno, expr.cond_expr.column, 'conditional expression must be of type "bool"')

        # We get the type of the 'then' branch
        then_type = self.__analyze_expr(expr.then_expr, stack)
        ret_type = then_type

        # If there is a 'else' branch, we analyze it
        if expr.else_expr is not None:
            # We get the type of the 'else' branch
            else_type = self.__analyze_expr(expr.else_expr, stack)

        # Else, by default the type of the branch 'else' is 'unit'
        else:
            else_type = 'unit'

        # If (at least) one branch has type unit
        if then_type == 'unit' or else_type == 'unit':
            ret_type = 'unit'

        # If (at least) one branch has a primitive type
        elif then_type in self.__primitive_types or else_type in self.__primitive_types:
            # We check if both primitive types are equal
            if then_type != else_type:
                self.__print_error(expr.else_expr.lineno, expr.else_expr.column, '"else" branch must have the same type of "then" branch')

        # Else the type of the two branches are a 'class' type
        else:
            # If class types are different
            if then_type != else_type:
                # We get the common ancestor between the two classes (no verification
                # needed because every classes have at least a common ancestor : Object)
                ret_type = self.__get_common_ancestor(then_type, else_type)

        # We return the type of the expression
        return ret_type

    def __analyze_expr_while(self, expr, stack):
        # We get the type of the conditional expression
        cond_type = self.__analyze_expr(expr.cond_expr, stack)

        # We check the type of the conditional expression
        if cond_type != 'bool':
            self.__print_error(expr.cond_expr.lineno, expr.cond_expr.column, 'conditional expression must be of type "bool"')

        # We get the type of the body
        body_type = self.__analyze_expr(expr.body_expr, stack)

        # We return the type of the expression
        return 'unit'

    def __analyze_expr_let(self, expr, stack):
        # Check the static type of 'let'
        if expr.type not in self.__primitive_types:
            if expr.type not in self.__symbol_table:
                self.__print_error(expr.lineno, expr.column, 'undefined type "{}"'.format(expr.type))

        # Create the symbol table of the 'let'
        let_symbol_table = LetSymbolTable(expr.lineno, expr.column, expr.name, expr.type)

        # If the 'let' has an initializing expression
        if expr.init_expr is not None:
            init_type = self.__analyze_expr(expr.init_expr, stack)

            # If the initial type is a primitive type
            if init_type in self.__primitive_types:
                if expr.type != init_type:
                    self.__print_error(expr.init_expr.lineno, expr.init_expr.column, 'type of initial expression must be "{}"'.format(expr.type))

            # If the initial type is a 'class' type
            else:
                if expr.type != init_type:
                    init_ancestors = self.__get_ancestors(init_type)

                    if expr.type not in init_ancestors:
                        self.__print_error(expr.init_expr.lineno, expr.init_expr.column, 'type of initial expression must be conform with type "{}"'.format(expr.type))

        # Get the expression of the body of the 'let'
        body_type = self.__analyze_expr(expr.scope_expr, [let_symbol_table] + stack)

        # We return the type of the 'let'
        return body_type

    def __analyze_expr_assign(self, expr, stack):
        # We check if field is a 'self'
        if expr.name == 'self':
            self.__print_error(expr.lineno, expr.column, 'can not assign a value to "self"')

        # We get the type of the field which is assigned a value
        field = self.__lookup_field(stack, expr.name)

        # If the field does not exist in the scope, we print an error
        if field is None:
            self.__print_error(expr.lineno, expr.column, 'no field named "{}" available in this scope'.format(expr.name))

        # We get the type of the expression we assign
        assign_type = self.__analyze_expr(expr.expr, stack)

        # If one type is a primitive type
        if field.type in self.__primitive_types or assign_type in self.__primitive_types:

            # We check if types are conform
            if field.type != assign_type:
                self.__print_error(expr.expr.lineno, expr.expr.column, 'non conform assigned type "{}" (must be of type "{}")'.format(assign_type, field.type))

        # If field type is a 'class' type
        else:
            # We get the ancestors of the assigned type
            assign_ancestors = self.__get_ancestors(assign_type)

            # We check if the field is a parent of the assigned type
            if field.type != assign_type and field.type not in assign_ancestors:
                self.__print_error(expr.expr.lineno, expr.expr.column, 'non conform assigned type "{}"'.format(assign_type))

        # We return the type of the expression
        return assign_type

    def __analyze_expr_unop(self, expr, stack):
        # We get the type of the expression
        expr_type = self.__analyze_expr(expr.expr, stack)

        # We get the unary operator
        unop = expr.op

        # We initialize the return type
        ret_type = expr_type

        # If unary operator is 'not'
        if unop == 'not':
            if expr_type != 'bool':
                self.__print_error(expr.expr.lineno, expr.expr.column, 'expression type must be "bool"')

        # If unary operator is '-'
        elif unop == '-':
            if expr_type != 'int32':
                self.__print_error(expr.expr.lineno, expr.expr.column, 'expression type must be "int32"')

        # If unary operator is 'isnull'
        elif unop == 'isnull':
            if expr_type in self.__primitive_types:
                self.__print_error(expr.expr.lineno, expr.expr.column, '"isnull" operator can not be used on a primitive type')

            ret_type = 'bool'

        # If unary operator is unknown
        else:
            self.__print_error(expr.lineno, expr.column, 'unknown unary operator')

        # We return the type of the expression
        return ret_type

    def __analyze_expr_binop(self, expr, stack):
        # We get type of left and right expressions
        left_type = self.__analyze_expr(expr.left_expr, stack)
        right_type = self.__analyze_expr(expr.right_expr, stack)

        # We get the binary operator
        binop = expr.op

        # We initialize the return type
        ret_type = 'bool'

        # If binary operator is '='
        if binop == '=':
            # If a operand has a primitive type
            if left_type in self.__primitive_types or right_type in self.__primitive_types:
                if left_type not in self.__primitive_types:
                    self.__print_error(expr.left_expr.lineno, expr.left_expr.column, 'invalid left expression type (non primitive type compared with a primitive type)')
                elif right_type not in self.__primitive_types:
                    self.__print_error(expr.right_expr.lineno, expr.right_expr.column, 'invalid right expression type (non primitive type compared with a primitive type)')
                elif left_type != right_type:
                    self.__print_error(expr.right_expr.lineno, expr.right_expr.column, 'can not compare a value of type "{}" and a value of type "{}"'.format(left_type, right_type))

        # If binary operator is a logical operator
        elif binop == 'and':
            if left_type != 'bool':
                self.__print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "bool"')

            if right_type != 'bool':
                self.__print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "bool"')

        # If binary operator is a comparison operator
        elif binop in ['<', '<=']:
            if left_type != 'int32':
                self.__print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "int32"')

            if right_type != 'int32':
                self.__print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "int32"')

        # If binary operator is an arithmetic operator
        elif binop in ['+', '-', '*', '/', '^']:
            if left_type != 'int32':
                self.__print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "int32"')

            if right_type != 'int32':
                self.__print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "int32"')

            ret_type = 'int32'

        # If binary operator is unknown
        else:
            self.__print_error(expr.lineno, expr.column, 'unknown binary operator')

        # We return the type of the expression
        return ret_type

    def __analyze_expr_call(self, expr, stack):
        # We get the type of the 'caller'
        obj_type = self.__analyze_expr(expr.obj_expr, stack)

        # We check if the type of the 'caller' is 'None'
        if obj_type is None:
            self.__print_error(expr.obj_expr.lineno, expr.obj_expr.column, 'can not use "self" in a field initializer')

        # We check if the object type is a primitive type
        if obj_type in self.__primitive_types:
            self.__print_error(expr.obj_expr.lineno, expr.obj_expr.column, 'the caller can not have a primitive type')

        # We check if the method is available in the scope of the caller
        method = self.__lookup_method([self.__symbol_table[obj_type]], expr.method_name)

        if method is None:
            self.__print_error(expr.lineno, expr.column, 'no method called "{}" available in this scope'.format(expr.method_name))

        # We check if all argument's type are conform to the signature of the method
        args_type = []

        for e in expr.expr_list:
            arg_type = self.__analyze_expr(e, stack)
            args_type += [arg_type]

        if len(method.args) != len(args_type):
            self.__print_error(expr.lineno, expr.column, 'called method "{}" does not have the right signature'.format(expr.method_name))

        if len(method.args) != 0:
            signature_args_type = []

            for value in method.args.values():
                signature_args_type += [value.type]

            for i in range(0, len(signature_args_type)):
                # If the type of the argument is a primitive type
                if signature_args_type[i] in self.__primitive_types:
                    if signature_args_type[i] != args_type[i]:
                        self.__print_error(expr.expr_list[i].lineno, expr.expr_list[i].column, 'argument number {} does not have the right type'.format(i + 1))

                # If the type of the argument is a 'class' type
                else:
                    if signature_args_type[i] != args_type[i]:
                        arg_ancestors = self.__get_ancestors(args_type[i])

                        if signature_args_type[i] not in arg_ancestors:
                            self.__print_error(expr.expr_list[i].lineno, expr.expr_list[i].column, 'argument number {} does not have a conform type'.format(i + 1))

        # We return the type of the expression
        return method.ret_type

    def __analyze_expr_new(self, expr, stack):
        # We check if the type of the new element exist
        if expr.type_name not in self.__symbol_table:
            self.__print_error(expr.lineno, expr.column, 'unknown type "{}"'.format(expr.type_name))

        # We return the type of the expression
        return expr.type_name

    def __analyze_expr_self(self, expr, stack):
        # We get and return the type of the 'self' element
        return self.__get_current_class(stack)

    def __analyze_expr_obj_id(self, expr, stack):
        # We get the object identifier
        obj_id = expr.id

        # If the object identifier is 'self':
        if obj_id == 'self':
            current_class = self.__get_current_class(stack)

            if current_class is None:
                self.__print_error(expr.lineno, expr.column, '"self" not allowed in this contexte')

            return current_class

        # If the object identifier is not 'self'
        else:
            # We check if a field with this name exist in the current scope
            field = self.__lookup_field(stack, obj_id)

            if field is None:
                self.__print_error(expr.lineno, expr.column, 'no field called "{}" available in this context'.format(obj_id))

            return field.type

    def __analyze_expr_literal(self, expr, stack):
        literal_type = expr.type

        # If literal is a 'integer-literal'
        if literal_type == 'integer':
            return 'int32'

        # If literal is a 'string-literal'
        elif literal_type == 'string':
            return 'string'

        # If literal is a 'boolean' literal
        elif literal_type == 'boolean':
            return 'bool'

        # If literal is unknown
        else:
            self.__print_error(expr.lineno, expr.column, 'unknown literal')

    def __analyze_expr_unit(self, expr, stack):
        # We return the type of the expression
        return 'unit'

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

        ###############
        # Expressions #
        ###############

        # Analyze all fields'initializer
        self.__check_fields_initializer()

        # Analyze all methods'block
        self.__check_methods_body()

        ###############
        # Annoted AST #
        ###############

        return self.__ast
