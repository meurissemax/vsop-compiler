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

class Node:
    # Parent class of all AST elements. Since Python does not
    # support abstract classes natively, this class is not
    # really useful.

    # For the sake of code clarity, we decided to keep it.

    pass


class Program(Node):
    def __init__(self):
        self.classes = []

    def __str__(self):
        output = '['

        for i, c in enumerate(self.classes):
            if i == 0:
                output += str(c)
            else:
                output += ', \n' + str(c)

        return output + ']'

    def add_class(self, c):
        self.classes = [c] + self.classes


class Class(Node):
    def __init__(self, lineno, column, name, parent='Object'):
        self.lineno = lineno
        self.column = column

        self.name = name
        self.parent = parent
        self.fields = []
        self.methods = []

    def __str__(self):
        output = 'Class(' + self.name + ', ' + self.parent + ', ['

        for i, f in enumerate(self.fields):
            if i == 0:
                output += '\n\t' + str(f)
            else:
                output += ', \n\t' + str(f)

        output += '], ['

        for i, m in enumerate(self.methods):
            if i == 0:
                output += '\n\t' + str(m)
            else:
                output += ', \n\t' + str(m)

        return output + '])'

    def add_field(self, f):
        self.fields.append(f)

    def add_method(self, m):
        self.methods.append(m)


class Field(Node):
    def __init__(self, lineno, column, name, _type, init_expr):
        self.lineno = lineno
        self.column = column

        self.name = name
        self.type = _type
        self.init_expr = init_expr

    def __str__(self):
        output = 'Field(' + self.name + ', ' + self.type

        if self.init_expr is not None:
            output += ', ' + str(self.init_expr)

        return output + ')'


class Method(Node):
    def __init__(self, lineno, column, name, ret_type, block):
        self.lineno = lineno
        self.column = column

        self.name = name
        self.formals = []
        self.ret_type = ret_type
        self.block = block

    def __str__(self):
        output = 'Method(' + self.name + ', ['

        for i, f in enumerate(self.formals):
            if i == 0:
                output += str(f)
            else:
                output += ', ' + str(f)

        return output + '], ' + self.ret_type + ', ' + str(self.block) + ')'

    def add_formal(self, f):
        self.formals.append(f)


class Formal(Node):
    def __init__(self, lineno, column, name, _type):
        self.lineno = lineno
        self.column = column

        self.name = name
        self.type = _type

    def __str__(self):
        return self.name + ' : ' + self.type


class Block(Node):
    def __init__(self):
        self.expr_list = []

    def __str__(self):
        if len(self.expr_list) == 1:
            return str(self.expr_list[0])
        else:
            output = '['

            for i, e in enumerate(self.expr_list):
                if i == 0:
                    output += str(e)
                else:
                    output += ', ' + str(e)

            return output + ']'

    def add_expr(self, e):
        self.expr_list.append(e)


class Expr(Node):
    # Parent class of all expression elements. Since Python
    # does not support abstract classes natively, this class
    # is not really useful.

    # For the sake of code clarity, we decided to keep it.

    pass


class If(Expr):
    def __init__(self, lineno, column, cond_expr, then_expr, else_expr):
        self.lineno = lineno
        self.column = column

        self.cond_expr = cond_expr
        self.then_expr = then_expr
        self.else_expr = else_expr

    def __str__(self):
        output = 'If(' + str(self.cond_expr) + ', ' + str(self.then_expr)

        if self.else_expr is not None:
            output += ', ' + str(self.else_expr)

        return output + ')'


class While(Expr):
    def __init__(self, lineno, column, cond_expr, body_expr):
        self.lineno = lineno
        self.column = column

        self.cond_expr = cond_expr
        self.body_expr = body_expr

    def __str__(self):
        return 'While(' + str(self.cond_expr) + ', ' + str(self.body_expr) + ')'


class Let(Expr):
    def __init__(self, lineno, column, name, _type, init_expr, scope_expr):
        self.lineno = lineno
        self.column = column

        self.name = name
        self.type = _type
        self.init_expr = init_expr
        self.scope_expr = scope_expr

    def __str__(self):
        output = 'Let(' + self.name + ', ' + self.type

        if self.init_expr is not None:
            output += ', ' + str(self.init_expr)

        return output + ', ' + str(self.scope_expr) + ')'


class Assign(Expr):
    def __init__(self, lineno, column, name, expr):
        self.lineno = lineno
        self.column = column

        self.name = name
        self.expr = expr

    def __str__(self):
        return 'Assign(' + self.name + ', ' + str(self.expr) + ')'


class UnOp(Expr):
    def __init__(self, lineno, column, op, expr):
        self.lineno = lineno
        self.column = column

        self.op = op
        self.expr = expr

    def __str__(self):
        return 'UnOp(' + self.op + ', ' + str(self.expr) + ')'


class BinOp(Expr):
    def __init__(self, lineno, column, op, left_expr, right_expr):
        self.lineno = lineno
        self.column = column

        self.op = op
        self.left_expr = left_expr
        self.right_expr = right_expr

    def __str__(self):
        return 'BinOp(' + self.op + ', ' + str(self.left_expr) + ', ' + str(self.right_expr) + ')'


class Call(Expr):
    def __init__(self, lineno, column, obj_expr, method_name):
        self.lineno = lineno
        self.column = column

        self.obj_expr = obj_expr
        self.method_name = method_name
        self.expr_list = []

    def __str__(self):
        output = 'Call(' + str(self.obj_expr) + ', ' + self.method_name + ', ['

        for i, e in enumerate(self.expr_list):
            if i == 0:
                output += str(e)
            else:
                output += ', ' + str(e)

        return output + '])'

    def add_expr(self, e):
        self.expr_list.append(e)


class New(Expr):
    def __init__(self, lineno, column, type_name):
        self.lineno = lineno
        self.column = column

        self.type_name = type_name

    def __str__(self):
        return 'New(' + self.type_name + ')'
