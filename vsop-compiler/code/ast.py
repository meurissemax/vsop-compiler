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
	pass

class Program(Node):
	def __init__(self):
		self.classes = []

	def __str__(self):
		output = '['

		for c in self.classes:
			output += str(c) + ', '

		return output + ']'

	def add_class(self, c):
		self.classes.append(c)


class Class(Node):
	def __init__(self, name, parent = 'Object'):
		self.name = name
		self.parent = parent
		self.fields = []
		self.methods = []

	def __str__(self):
		output = 'Class(' + self.name + ', ' + self.parent + ', ['

		for f in self.fields:
			output += str(f) + ', '

		output += '], ['

		for m in self.method:
			output += str(m) + ', '

		return output + '])'

	def add_field(self, f):
		self.fields.append(f)

	def add_method(self, m):
		self.fields.append(m)


class Field(Node):
	def __init__(self, name, _type, init_expr = None):
		self.name = name
		self.type = _type
		self.init_expr = init_expr

	def __str__(self):
		output = 'Field(' + self.name + ', ' + self._type

		if init_expr is not None:
			output += ', ' + str(self.init_expr)

		return output + ')'


class Method(Node):
	def __init__(self, name, ret_type, block):
		self.name = name
		self.formals = []
		self.ret_type = ret_type
		self.block = block

	def __str__(self):
		output = 'Method(' + self.name + ', ['

		for f in formals:
			output += str(f) + ','

		return output + '], ' + self.ret_type + ', ' + str(self.block) + ')'

	def add_formal(f):
		self.formals.append(f)


class Formal(Node):
	def __init__(self, name, _type):
		self.name = name
		self.type = _type

	def __str__(self):
		return self.name + ' : ' self.type


class Block(Node):
	def __init__(self):
		self.expr_list = []

	def __str__(self):
		if len(self.expr_list) == 1:
			return str(expr_list[0])
		else:
			output = '['

			for e in expr_list:
				output += str(e) + ', '

			return output + ']'

	def add_expr(self, e):
		self.expr_list.append(e)


class Expr(Node):
	pass


class If(Expr):
	def __init__(self, cond_expr, then_expr, else_expr = None):
		self.cond_expr = cond_expr
		self.then_expr = then_expr
		self.else_expr = else_expr

	def __str__(self):
		output = 'If(' + str(self.cond_expr) + ', ' + str(self.then_expr)

		if self.else_expr is not None:
			output += ', ' + str(self.else_expr)

		return output + ')'


class While(Expr):
	def __init__(self, cond_expr, body_expr):
		self.cond_expr = cond_expr
		self.body_expr = body_expr

	def __str__(self):
		return 'While(' + str(self.cond_expr) + ', ' + str(self.body_expr) + ')'


class Let(Expr):
	def __init__(self, name, _type, init_expr = None, scope_expr):
		self.name = name
		self.type = _type
		self.init_expr = init_expr
		self.scope_expr = scope_expr

	def __str__(self):
		output = 'Let(' + self.name + ', ' + self.type

		if init_expr is not None:
			output += ', ' + str(init_expr)

		return output + ', ' + str(scope_expr) + ')'


class Assign(Expr):
	def __init__(self, name, expr):
		self.name = name
		self.expr = expr

	def __str__(self):
		return 'Assign(' + self.name + ', ' + str(self.expr) + ')'


class UnOp(Expr):
	def __init__(self, op, expr):
		self.op = op
		self.expr = expr

	def __str__(self):
		return 'UnOp(' + self.op + ', ' + str(self.expr) + ')'


class BinOp(Expr):
	def __init__(self, op, left_expr, right_expr):
		self.op = op
		self.left_expr = left_expr
		self.right_expr = right_expr

	def __str__():
		return 'BinOp(' + self.op + ', ' + str(self.left_expr) + ', ' + str(self.right_expr) + ')'


class Call(Expr):
	def __init__(self, obj_expr, method_name):
		self.obj_expr = obj_expr
		self.method_name = method_name
		self.expr_list = []

	def __str__(self):
		output = 'Call(' + self.obj_expr + ', ' + self.method_name + '['

		for e in expr_list:
			output += str(e) + ', '

		return output + '])'

	def add_expr(self, e):
		self.expr_list.append(e)


class New(Expr):
	def __init__(self, type_name):
		self.type_name

	def __str__(self):
		return 'New(' + self.type_name + ')'
