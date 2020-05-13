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

from parser.ast import *
from semantic.tables import *


###########
# Classes #
###########

class Semantic:
    ###############
    # Constructor #
    ###############

    def __init__(self, filename, ast):
        # We save the VSOP source file name
        self.filename = filename

        # We save the AST to annotate it later
        self.ast = ast

        # Base symbol table that will contains all
        # the symbol tables of the classes
        self.st = {}

        # We define the list of primitive types
        self.primitive_types = ['unit', 'bool', 'int32', 'string']

    ##################
    # Error handling #
    ##################

    def print_error(self, lineno, column, message):
        """
        Prints an error on stderr in the right format
        and exits the parser.
        """

        print('{}:{}:{}: semantic error: {}'.format(self.filename, lineno, column, message), file=sys.stderr)
        sys.exit(1)

    ######################
    # Classes management #
    ######################

    def add_object(self):
        object_class = ClassSymbolTable(None, None, 'Object')

        object_class.methods['print'] = MethodSymbolTable(None, None, 'print', {'s': FieldSymbolTable(None, None, 's', 'string')}, 'Object')
        object_class.methods['printBool'] = MethodSymbolTable(None, None, 'printBool', {'b': FieldSymbolTable(None, None, 'b', 'bool')}, 'Object')
        object_class.methods['printInt32'] = MethodSymbolTable(None, None, 'printInt32', {'i': FieldSymbolTable(None, None, 'i', 'int32')}, 'Object')

        object_class.methods['inputLine'] = MethodSymbolTable(None, None, 'inputLine', {}, 'string')
        object_class.methods['inputBool'] = MethodSymbolTable(None, None, 'inputBool', {}, 'bool')
        object_class.methods['inputInt32'] = MethodSymbolTable(None, None, 'inputInt32', {}, 'int32')

        self.st['Object'] = object_class

    def check_classes(self):
        # Save each class declaration (and check if it already exist or not)
        for c in self.ast.classes:
            if c.name == 'Object':
                self.print_error(c.lineno, c.column, 'can not redefine class "Object"')
            elif c.name in self.st:
                already = self.st[c.name]

                self.print_error(c.lineno, c.column, 'class "{}" already defined at {}:{}'.format(c.name, already.lineno, already.column))
            else:
                self.st[c.name] = ClassSymbolTable(c.lineno, c.column, c.name)

        # Check the parent of each class
        for c in self.ast.classes:
            if c.parent not in self.st:
                self.print_error(c.lineno, c.column, 'parent class "{}" does not exist'.format(c.parent))
            elif c.name == c.parent:
                self.print_error(c.lineno, c.column, 'class "{}" cannot inherit by itself'.format(c.name))
            else:
                self.st[c.name].parent = (c.parent, self.st[c.parent])

        # Check possible cycles
        for key, value in self.st.items():
            if key != 'Object':
                c = key
                parent = value.parent[0]

                while parent != 'Object':
                    c = parent
                    parent = self.st[c].parent[0]

                    if parent == key:
                        self.print_error(value.lineno, value.column, 'class "{}" can not be extend in a cycle'.format(key))

        # Check that a 'Main' class is provided
        if 'Main' not in self.st:
            self.print_error(1, 1, 'a class "Main" must be provided')

    def get_ancestors(self, class_name):
        ancestors = []

        if class_name != 'Object':
            ancestors += [class_name]
            parent = self.st[class_name].parent

            while parent is not None:
                ancestors += [parent[0]]
                parent = self.st[parent[0]].parent

        return ancestors

    def get_common_ancestor(self, class_name_1, class_name_2):
        class_1_ancestors = self.get_ancestors(class_name_1)
        class_2_ancestors = self.get_ancestors(class_name_2)

        if class_name_1 in class_2_ancestors:
            return class_name_1
        elif class_name_2 in class_1_ancestors:
            return class_name_2
        else:
            return None

    def get_current_class(self, stack):
        # We iterate over each element of the stack
        for symbol_table in stack:

            # We only look for 'ClassSymbolTable'
            if symbol_table.__class__.__name__ == 'ClassSymbolTable':
                return symbol_table.name

        return None

    #####################
    # Fields management #
    #####################

    def check_fields(self):
        # We iterate over each class
        for c in self.ast.classes:

            # For each class, we iterate over its fields
            for f in c.fields:

                # We check if field is named 'self'
                if f.name == 'self':
                    self.print_error(f.lineno, f.column, 'a field can not be named "self"')

                # We check if field is already defined
                elif f.name in self.st[c.name].fields:
                    already = self.st[c.name].fields[f.name]

                    self.print_error(f.lineno, f.column, 'field "{}" already defined at {}:{}'.format(f.name, already.lineno, already.column))

                # If the type of field is not primitive, we check that the class associated
                # to his type exist
                elif f.type not in self.primitive_types and f.type not in self.st:
                    self.print_error(f.lineno, f.column, 'undefined type "{}" for field "{}"'.format(f.type, f.name))

                # Else we possibly add the field
                else:
                    # We check if the field override a parent field
                    parent = self.st[c.name].parent

                    while parent is not None:
                        parent_name = parent[0]

                        if f.name in self.st[parent_name].fields:
                            already = self.st[parent_name].fields[f.name]

                            self.print_error(f.lineno, f.column, 'field "{}" already defined in parent at {}:{} and can not be override'.format(f.name, already.lineno, already.column))
                        else:
                            parent = self.st[parent_name].parent

                    # If not, we add the field
                    self.st[c.name].fields[f.name] = FieldSymbolTable(f.lineno, f.column, f.name, f.type)

    def check_fields_initializer(self):
        # We iterate over each class
        for c in self.ast.classes:

            # For each class, we iterate over its fields
            for f in c.fields:

                # We check if the field has an initialize
                if f.init_expr is not None:

                    # We get the type of the initializing expression (with an empty stack because
                    # fields and methods of 'self' are not yet in the scope)
                    init_type = self.analyze_expr(f.init_expr, [])

                    # If the expected field type is a primitive type
                    if f.type in self.primitive_types:
                        if f.type != init_type:
                            self.print_error(f.init_expr.lineno, f.init_expr.column, 'type of the initial expression must be "{}"'.format(f.type))

                    # If the expected field type is a 'class' type
                    else:
                        if f.type != init_type:
                            init_ancestors = self.get_ancestors(init_type)

                            if f.type not in init_ancestors:
                                self.print_error(f.init_expr.lineno, f.init_expr.column, 'type of the initial expression is not conform with static type "{}"'.format(f.type))

                            # We update the type of the field (because we will use the dynamic type of the field to check 'Call')
                            self.st[c.name].fields[f.name].type = init_type

    def lookup_field(self, stack, field_name):
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

    def check_methods(self):
        # We iterate over each class
        for c in self.ast.classes:

            # For each class, we iterate over its methods
            for m in c.methods:

                # We check if method is already defined
                if m.name in self.st[c.name].methods:
                    already = self.st[c.name].methods[m.name]

                    self.print_error(m.lineno, m.column, 'method "{}" already defined at {}:{}'.format(m.name, already.lineno, already.column))

                # Else we possibly add the method
                else:
                    # We check if multiple parameters have the same name
                    f_names = []

                    for f in m.formals:
                        f_names = f_names + [f.name]

                    if len(set(f_names)) != len(f_names):
                        self.print_error(m.lineno, m.column, 'multiple formals can not have the same name')

                    # We check type of formals and return value
                    for f in m.formals:
                        if f.type not in self.primitive_types and f.type not in self.st:
                            self.print_error(f.lineno, f.column, 'undefined type "{}" for formal "{}"'.format(f.type, f.name))

                    if m.ret_type not in self.primitive_types and m.ret_type not in self.st:
                        self.print_error(m.lineno, m.column, 'undefined return type "{}" for method "{}"'.format(m.ret_type, m.name))

                    # We check if the method is defined in a parent. If it is the cas, we check
                    # that the override is valid.
                    parent = self.st[c.name].parent

                    while parent is not None:
                        parent_name = parent[0]

                        # If method overrides a parent's method
                        if m.name in self.st[parent_name].methods:
                            # We get types of all formals
                            args_type = []

                            for f in m.formals:
                                args_type += [f.type]

                            # We get parent method
                            parent_method = self.st[parent_name].methods[m.name]

                            # If formals'type are different
                            signature_args_type = []

                            for value in parent_method.args.values():
                                signature_args_type += [value.type]

                            if len(signature_args_type) != len(args_type):
                                self.print_error(m.lineno, m.column, 'formals of method "{}" must have the same type of formals of method "{}" in parent class at {}:{}'.format(m.name, m.name, parent_method.lineno, parent_method.column))

                            for i in range(0, len(signature_args_type)):
                                # If argument type is a primitive type
                                if signature_args_type[i] in self.primitive_types:
                                    if signature_args_type[i] != args_type[i]:
                                        self.print_error(m.lineno, m.column, 'formals of method "{}" must have the same type of formals of method "{}" in parent class at {}:{}'.format(m.name, m.name, parent_method.lineno, parent_method.column))

                                # If argument type is a 'class' type
                                else:
                                    if signature_args_type[i] != args_type[i]:
                                        arg_ancestors = self.get_ancestors(args_type[i])

                                        if signature_args_type[i] not in arg_ancestors:
                                            self.print_error(m.lineno, m.column, 'formals of method "{}" must have the same type of formals of method "{}" in parent class at {}:{}'.format(m.name, m.name, parent_method.lineno, parent_method.column))

                            # If return types are different
                            if m.ret_type != parent_method.ret_type:
                                self.print_error(m.lineno, m.column, 'return type of method "{}" must be the same as the return type of corresponding method in parent class at {}:{}'.format(m.name, parent_method.lineno, parent_method.column))

                        parent = self.st[parent_name].parent

                    # If no error occurs, we add the method
                    args = {}

                    for f in m.formals:
                        args[f.name] = FieldSymbolTable(f.lineno, f.column, f.name, f.type)

                    self.st[c.name].methods[m.name] = MethodSymbolTable(m.lineno, m.column, m.name, args, m.ret_type)

        # We check that the 'Main' class has a 'main() : int32' method
        if 'main' in self.st['Main'].methods:
            main_method = self.st['Main'].methods['main']

            if len(main_method.args) == 0:
                if main_method.ret_type != 'int32':
                    self.print_error(main_method.lineno, main_method.column, 'the "main" method of class "Main" must have "int32" as return type')
            else:
                self.print_error(main_method.lineno, main_method.column, 'the "main" method of class "Main" can not have any formal')
        else:
            main_class = self.st['Main']

            self.print_error(main_class.lineno, main_class.column, 'class "Main" must have a "main() : int32" method')

    def check_methods_body(self):
        # We iterate over each class
        for c in self.ast.classes:

            # For each class, we iterate over its methods
            for m in c.methods:

                # We get the return type of the method
                ret_type = m.ret_type

                # We get the type of the method's body
                stack = [self.st[c.name].methods[m.name], self.st[c.name]]
                block_type = self.analyze_expr(m.block, stack)

                # If the expected return type is a primitive type
                if ret_type in self.primitive_types:
                    if ret_type != block_type:
                        self.print_error(m.block.lineno, m.block.column, 'return type of the method "{}" is not conform with his signature ("{}" expected but "{}")'.format(m.name, ret_type, block_type))

                # If the expected return type is a 'class' type
                else:

                    # If the return type of the block is a primitive type
                    if block_type in self.primitive_types:
                        self.print_error(m.block.lineno, m.block.column, 'return type of the method "{}" is not conform with his signature ("{}" expected but "{}")'.format(m.name, ret_type, block_type))

                    # If the return type of the block is a 'class' type
                    elif ret_type != block_type:
                        block_type_ancestors = self.get_ancestors(block_type)

                        if ret_type not in block_type_ancestors:
                            self.print_error(m.block.lineno, m.block.column, 'return type of the method "{}" is not conform with his signature'.format(m.name))

    def lookup_method(self, stack, method_name):
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

    def analyze_expr(self, expr, stack):
        # We get the expression class (If, While, ...)
        expr_class = expr.__class__.__name__

        # We analyze the expression depending of his type (class)
        if expr_class == 'Block':
            for i in range(0, len(expr.expr_list) - 1):
                self.analyze_expr(expr.expr_list[i], stack)

            expr_type = self.analyze_expr(expr.expr_list[len(expr.expr_list) - 1], stack)
        else:
            method_name = 'analyze_expr_{}'.format(expr_class)
            expr_type = getattr(self, method_name)(expr, stack)

        # We set the expression type (we update the node in the AST)
        expr.set_expr_type(expr_type)

        # We return the type of the expression
        return expr_type

    def analyze_expr_If(self, expr, stack):
        # We get the type of the conditional expression
        cond_type = self.analyze_expr(expr.cond_expr, stack)

        # We check the type of the conditional expression
        if cond_type != 'bool':
            self.print_error(expr.cond_expr.lineno, expr.cond_expr.column, 'conditional expression must be of type "bool"')

        # We get the type of the 'then' branch
        then_type = self.analyze_expr(expr.then_expr, stack)
        ret_type = then_type

        # If there is a 'else' branch, we analyze it
        if expr.else_expr is not None:
            # We get the type of the 'else' branch
            else_type = self.analyze_expr(expr.else_expr, stack)

        # Else, by default the type of the branch 'else' is 'unit'
        else:
            else_type = 'unit'

        # If (at least) one branch has type unit
        if then_type == 'unit' or else_type == 'unit':
            ret_type = 'unit'

        # If (at least) one branch has a primitive type
        elif then_type in self.primitive_types or else_type in self.primitive_types:
            # We check if both primitive types are equal
            if then_type != else_type:
                self.print_error(expr.else_expr.lineno, expr.else_expr.column, '"else" branch must have the same type of "then" branch')

        # Else the type of the two branches are a 'class' type
        else:
            # If class types are different
            if then_type != else_type:
                # We get the common ancestor between the two classes (no verification
                # needed because every classes have at least a common ancestor : Object)
                ret_type = self.get_common_ancestor(then_type, else_type)

        # We return the type of the expression
        return ret_type

    def analyze_expr_While(self, expr, stack):
        # We get the type of the conditional expression
        cond_type = self.analyze_expr(expr.cond_expr, stack)

        # We check the type of the conditional expression
        if cond_type != 'bool':
            self.print_error(expr.cond_expr.lineno, expr.cond_expr.column, 'conditional expression must be of type "bool"')

        # We get the type of the body
        body_type = self.analyze_expr(expr.body_expr, stack)

        # We return the type of the expression
        return 'unit'

    def analyze_expr_Let(self, expr, stack):
        # Check the static type of 'let'
        if expr.type not in self.primitive_types:
            if expr.type not in self.st:
                self.print_error(expr.lineno, expr.column, 'undefined type "{}"'.format(expr.type))

        # Create the symbol table of the 'let'
        let_symbol_table = LetSymbolTable(expr.lineno, expr.column, expr.name, expr.type)

        # If the 'let' has an initializing expression
        if expr.init_expr is not None:
            init_type = self.analyze_expr(expr.init_expr, stack)

            # If the initial type is a primitive type
            if init_type in self.primitive_types:
                if expr.type != init_type:
                    self.print_error(expr.init_expr.lineno, expr.init_expr.column, 'type of initial expression must be "{}"'.format(expr.type))

            # If the initial type is a 'class' type
            else:
                if expr.type != init_type:
                    init_ancestors = self.get_ancestors(init_type)

                    if expr.type not in init_ancestors:
                        self.print_error(expr.init_expr.lineno, expr.init_expr.column, 'type of initial expression must be conform with type "{}"'.format(expr.type))

        # Get the expression of the body of the 'let'
        body_type = self.analyze_expr(expr.scope_expr, [let_symbol_table] + stack)

        # We return the type of the 'let'
        return body_type

    def analyze_expr_Assign(self, expr, stack):
        # We check if field is a 'self'
        if expr.name == 'self':
            self.print_error(expr.lineno, expr.column, 'can not assign a value to "self"')

        # We get the type of the field which is assigned a value
        field = self.lookup_field(stack, expr.name)

        # If the field does not exist in the scope, we print an error
        if field is None:
            self.print_error(expr.lineno, expr.column, 'no field named "{}" available in this scope'.format(expr.name))

        # We get the type of the expression we assign
        assign_type = self.analyze_expr(expr.expr, stack)

        # If one type is a primitive type
        if field.type in self.primitive_types or assign_type in self.primitive_types:

            # We check if types are conform
            if field.type != assign_type:
                self.print_error(expr.expr.lineno, expr.expr.column, 'non conform assigned type "{}" (must be of type "{}")'.format(assign_type, field.type))

        # If field type is a 'class' type
        else:
            # We get the ancestors of the assigned type
            assign_ancestors = self.get_ancestors(assign_type)

            # We check if the field is a parent of the assigned type
            if field.type != assign_type and field.type not in assign_ancestors:
                self.print_error(expr.expr.lineno, expr.expr.column, 'non conform assigned type "{}"'.format(assign_type))

        # We return the type of the expression
        return field.type

    def analyze_expr_UnOp(self, expr, stack):
        # We get the type of the expression
        expr_type = self.analyze_expr(expr.expr, stack)

        # We get the unary operator
        unop = expr.op

        # We initialize the return type
        ret_type = expr_type

        # If unary operator is 'not'
        if unop == 'not':
            if expr_type != 'bool':
                self.print_error(expr.expr.lineno, expr.expr.column, 'expression type must be "bool"')

        # If unary operator is '-'
        elif unop == '-':
            if expr_type != 'int32':
                self.print_error(expr.expr.lineno, expr.expr.column, 'expression type must be "int32"')

        # If unary operator is 'isnull'
        elif unop == 'isnull':
            if expr_type in self.primitive_types:
                self.print_error(expr.expr.lineno, expr.expr.column, '"isnull" operator can not be used on a primitive type')

            ret_type = 'bool'

        # If unary operator is unknown
        else:
            self.print_error(expr.lineno, expr.column, 'unknown unary operator')

        # We return the type of the expression
        return ret_type

    def analyze_expr_BinOp(self, expr, stack):
        # We get type of left and right expressions
        left_type = self.analyze_expr(expr.left_expr, stack)
        right_type = self.analyze_expr(expr.right_expr, stack)

        # We get the binary operator
        binop = expr.op

        # We initialize the return type
        ret_type = 'bool'

        # If binary operator is '='
        if binop == '=':
            # If a operand has a primitive type
            if left_type in self.primitive_types or right_type in self.primitive_types:
                if left_type not in self.primitive_types:
                    self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'invalid left expression type (non primitive type compared with a primitive type)')
                elif right_type not in self.primitive_types:
                    self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'invalid right expression type (non primitive type compared with a primitive type)')
                elif left_type != right_type:
                    self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'can not compare a value of type "{}" and a value of type "{}"'.format(left_type, right_type))

        # If binary operator is a logical operator
        elif binop == 'and':
            if left_type != 'bool':
                self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "bool"')

            if right_type != 'bool':
                self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "bool"')

        # If binary operator is a comparison operator
        elif binop in ['<', '<=']:
            if left_type != 'int32':
                self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "int32"')

            if right_type != 'int32':
                self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "int32"')

        # If binary operator is an arithmetic operator
        elif binop in ['+', '-', '*', '/', '^']:
            if left_type != 'int32':
                self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "int32"')

            if right_type != 'int32':
                self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "int32"')

            ret_type = 'int32'

        # If binary operator is unknown
        else:
            self.print_error(expr.lineno, expr.column, 'unknown binary operator')

        # We return the type of the expression
        return ret_type

    def analyze_expr_Call(self, expr, stack):
        # We get the type of the 'caller'
        obj_type = self.analyze_expr(expr.obj_expr, stack)

        # We check if the type of the 'caller' is 'None'
        if obj_type is None:
            self.print_error(expr.obj_expr.lineno, expr.obj_expr.column, 'can not use "self" in a field initializer')

        # We check if the object type is a primitive type
        if obj_type in self.primitive_types:
            self.print_error(expr.obj_expr.lineno, expr.obj_expr.column, 'the caller can not have a primitive type')

        # We check if the method is available in the scope of the caller
        method = self.lookup_method([self.st[obj_type]], expr.method_name)

        if method is None:
            self.print_error(expr.lineno, expr.column, 'no method called "{}" available in this scope'.format(expr.method_name))

        # We check if all argument's type are conform to the signature of the method
        args_type = []

        for e in expr.expr_list:
            arg_type = self.analyze_expr(e, stack)
            args_type += [arg_type]

        if len(method.args) != len(args_type):
            self.print_error(expr.lineno, expr.column, 'called method "{}" does not have the right signature'.format(expr.method_name))

        if len(method.args) != 0:
            signature_args_type = []

            for value in method.args.values():
                signature_args_type += [value.type]

            for i in range(0, len(signature_args_type)):
                # If the type of the argument is a primitive type
                if signature_args_type[i] in self.primitive_types:
                    if signature_args_type[i] != args_type[i]:
                        self.print_error(expr.expr_list[i].lineno, expr.expr_list[i].column, 'argument number {} does not have the right type'.format(i + 1))

                # If the type of the argument is a 'class' type
                else:
                    if signature_args_type[i] != args_type[i]:
                        arg_ancestors = self.get_ancestors(args_type[i])

                        if signature_args_type[i] not in arg_ancestors:
                            self.print_error(expr.expr_list[i].lineno, expr.expr_list[i].column, 'argument number {} does not have a conform type'.format(i + 1))

        # We return the type of the expression
        return method.ret_type

    def analyze_expr_New(self, expr, stack):
        # We check if the type of the new element exist
        if expr.type_name not in self.st:
            self.print_error(expr.lineno, expr.column, 'unknown type "{}"'.format(expr.type_name))

        # We return the type of the expression
        return expr.type_name

    def analyze_expr_Self(self, expr, stack):
        # We get and return the type of the 'self' element
        return self.get_current_class(stack)

    def analyze_expr_ObjectIdentifier(self, expr, stack):
        # We get the object identifier
        obj_id = expr.id

        # If the object identifier is 'self':
        if obj_id == 'self':
            current_class = self.get_current_class(stack)

            if current_class is None:
                self.print_error(expr.lineno, expr.column, '"self" not allowed in this context')

            return current_class

        # If the object identifier is not 'self'
        else:
            # We check if a field with this name exist in the current scope
            field = self.lookup_field(stack, obj_id)

            if field is None:
                self.print_error(expr.lineno, expr.column, 'no field called "{}" available in this context'.format(obj_id))

            return field.type

    def analyze_expr_Literal(self, expr, stack):
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
            self.print_error(expr.lineno, expr.column, 'unknown literal')

    def analyze_expr_Unit(self, expr, stack):
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
        self.add_object()

        # Check classes of the program (cycle, name, ...)
        self.check_classes()

        ##########
        # Fields #
        ##########

        # Get and check all fields of each class
        self.check_fields()

        ###########
        # Methods #
        ###########

        # Get and check methods of each class
        self.check_methods()

        ###############
        # Expressions #
        ###############

        # Analyze all fields'initializer
        self.check_fields_initializer()

        # Analyze all methods'block
        self.check_methods_body()

        ###############
        # Annoted AST #
        ###############

        return self.ast


class SemanticExt(Semantic):
    ###############
    # Constructor #
    ###############

    def __init__(self, filename, ast):
        # We call the constructor of the parent class
        super().__init__(filename, ast)

    ##########################
    # Expressions management #
    ##########################

    # Overriden methods

    def analyze_expr_BinOp(self, expr, stack):
        # We get type of left and right expressions
        left_type = self.analyze_expr(expr.left_expr, stack)
        right_type = self.analyze_expr(expr.right_expr, stack)

        # We get the binary operator
        binop = expr.op

        # We initialize the return type
        ret_type = 'bool'

        # If binary operator is '='
        if binop == '=':
            # If a operand has a primitive type
            if left_type in self.primitive_types or right_type in self.primitive_types:
                if left_type not in self.primitive_types:
                    self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'invalid left expression type (non primitive type compared with a primitive type)')
                elif right_type not in self.primitive_types:
                    self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'invalid right expression type (non primitive type compared with a primitive type)')
                elif left_type != right_type:
                    self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'can not compare a value of type "{}" and a value of type "{}"'.format(left_type, right_type))

        # If binary operator is a logical operator
        elif binop in ['and', 'or']:
            if left_type != 'bool':
                self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "bool"')

            if right_type != 'bool':
                self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "bool"')

        # If binary operator is a comparison operator
        elif binop in ['<', '<=', '>', '>=']:
            if left_type != 'int32':
                self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "int32"')

            if right_type != 'int32':
                self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "int32"')

        # If binary operator is an arithmetic operator
        elif binop in ['+', '-', '*', '/', '^']:
            if left_type != 'int32':
                self.print_error(expr.left_expr.lineno, expr.left_expr.column, 'left expression must be of type "int32"')

            if right_type != 'int32':
                self.print_error(expr.right_expr.lineno, expr.right_expr.column, 'right expression must be of type "int32"')

            ret_type = 'int32'

        # If binary operator is unknown
        else:
            self.print_error(expr.lineno, expr.column, 'unknown binary operator')

        # We return the type of the expression
        return ret_type
