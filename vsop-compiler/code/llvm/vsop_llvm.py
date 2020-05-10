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

import os

import llvmlite.ir as ir
import llvmlite.binding as llvm

from collections import OrderedDict


####################
# Type definitions #
####################

# VSOP basic types
t_int32 = ir.IntType(32)
t_bool = ir.IntType(1)
t_string = ir.IntType(8).as_pointer()
t_unit = ir.VoidType()

# Additional types
t_int8 = ir.IntType(8)
t_int64 = ir.IntType(64)
t_double = ir.DoubleType()
t_void = ir.VoidType()


###########
# Classes #
###########

class LLVM:
    ###############
    # Constructor #
    ###############

    def __init__(self, filename, a_ast):
        # We save the VSOP source file name
        self.__filename = filename

        # We save the annotated AST to generate LLVM IR code
        self.__a_ast = a_ast

        # We create the LLVM IR module (a single module per VSOP source file)
        self.__module = ir.Module(name=__file__)

        # Current IR builder
        self.__builder = None

        # Dictionary that associates each class to its symbol table
        self.__symbol_table = {}

        # Dictionary to store imported functions
        self.__imported_functions = {}

        # A counter to manage global strings
        self.__count_string = 0

        # Current class name during analyzing phase
        self.__current_class = None

    #############
    # Utilities #
    #############

    def __get_type(self, t):
        if t == 'int32':
            return t_int32
        elif t == 'bool':
            return t_bool
        elif t == 'string':
            return t_string
        else:
            return self.__symbol_table[t]['struct'].as_pointer()

    def __concatenate_dict(self, d1, d2):
        # We create a new dictionary based on 'd1'
        d = OrderedDict(d1)

        # We add all elements of 'd2'
        for key, value in d2.items():
            d[key] = value

        # We return the new dictionary
        return d

    def __get_number_fields(self, name):
        # We iterate over each class
        for c in self.__a_ast.classes:

            # We check the name of the class
            if c.name == name:

                # We return the number of fields
                return len(c.fields)

    def __get_position(self, d, name):
        # We iterate over the element of the dictionary
        for i, k in enumerate(d.keys()):

            # We check if we found the element
            if k == name:
                return i

    def __lookup(self, stack, name):
        # We iterate over each element
        for d in stack:

            # We check if the value exist
            if d.get(name) is not None:
                return d[name]

        # Else we return a 'None'
        return None

    def __process_string(self, s):
        # We remove first and last character (because
        # it is '"')
        s = s[1:-1]

        # We change all the \xXX sequence
        charbuf = []
        i = 0

        while i < len(s):
            if s[i] == '\\':
                char_hex = '0{}'.format(s[i + 1:i + 4])
                charbuf += [chr(int(char_hex, 16))]

                i += 4
            else:
                charbuf += [s[i]]

                i += 1

        # We add a terminaison character
        charbuf += [chr(0)]

        # We return the processed string
        return ''.join(charbuf)

    ##################
    # Initialization #
    ##################

    def __initialize(self):
        # We import additional functions from C
        self.__import_functions()

        # We initialize the symbol table
        self.__initialize_st()

        # We initialize constructor (methods 'new' and 'init')
        # of each class
        self.__initialize_constr()

        # We add primitives types to the symbol table
        self.__initialize_primitives()

    def __import_functions(self):
        # We create the 'malloc' function
        module = ir.Module(name='malloc')

        malloc_t = ir.FunctionType(t_int8.as_pointer(), (t_int64,))
        malloc_f = ir.Function(module, malloc_t, name='malloc')

        self.__imported_functions['malloc'] = malloc_f

        # We create the 'pow' function
        pow_t = ir.FunctionType(t_double, (t_double, t_double))
        pow_f = ir.Function(self.__module, pow_t, name='pow')

        self.__imported_functions['pow'] = pow_f

        # We create the 'strcmp' function
        strcmp_t = ir.FunctionType(t_int32, (t_string, t_string))
        strcmp_f = ir.Function(self.__module, strcmp_t, name='strcmp')

        self.__imported_functions['strcmp'] = strcmp_f

    def __initialize_st(self):
        # We add the 'Object' class to the symbol table
        self.__initialize_object()

        # We iterate over each class
        for c in self.__a_ast.classes:

            # We create the dictionary for the fields
            d_fields = OrderedDict()

            for f in c.fields:
                d_field = {
                    'type': f.type,
                    'init_expr': f.init_expr
                }

                d_fields[f.name] = d_field

            # We create the dictionart for the methods
            d_methods = OrderedDict()

            for m in c.methods:
                # We get the list of formals
                d_args = {}

                for f in m.formals:
                    d_args[f.name] = f.type

                # We fill the dictionary
                d_body = {}

                d_body['args'] = d_args
                d_body['ret'] = m.ret_type
                d_body['obj_type'] = None
                d_body['obj'] = None

                # We add the method
                d_methods[m.name] = d_body

            # We create the dictionary for the class
            d_class = {
                'struct': ir.global_context.get_identified_type('struct.{}'.format(c.name)),
                'struct_vtable': ir.global_context.get_identified_type('struct.{}VTable'.format(c.name)),
                'global_vtable': None,
                'new': None,
                'init': None,
                'fields': d_fields,
                'methods': d_methods,
                'parent': c.parent
            }

            # We add the class to the symbol table
            self.__symbol_table[c.name] = d_class

        # We iterate over each class
        for c in self.__a_ast.classes:

            # We iterate over each methods of the class
            for key, value in self.__symbol_table[c.name]['methods'].items():

                # We create the method type object
                args_list = [self.__symbol_table[c.name]['struct'].as_pointer()]

                for t in value['args'].values():
                    args_list += [self.__get_type(t)]

                obj_type = ir.FunctionType(self.__get_type(value['ret']), (args_list))

                # We set the name of the method
                if c.name == 'Main' and key == 'main':
                    obj_name = 'main'
                else:
                    obj_name = '{}_method_{}'.format(c.name, key)

                # We create the method
                obj = ir.Function(self.__module, obj_type, name=obj_name)

                # We update the dictionary
                self.__symbol_table[c.name]['methods'][key]['obj_type'] = obj_type
                self.__symbol_table[c.name]['methods'][key]['obj'] = obj

        # We iterate over each class
        for c in self.__a_ast.classes:

            # We get and concatenate all fields and methods of the parent(s)
            d_fields = OrderedDict()
            d_methods = OrderedDict()

            parent = self.__symbol_table[c.name]['parent']

            while parent is not None:
                d_fields = self.__concatenate_dict(self.__symbol_table[parent]['fields'], d_fields)
                d_methods = self.__concatenate_dict(self.__symbol_table[parent]['methods'], d_methods)

                parent = self.__symbol_table[parent]['parent']

            self.__symbol_table[c.name]['fields'] = self.__concatenate_dict(d_fields, self.__symbol_table[c.name]['fields'])
            self.__symbol_table[c.name]['methods'] = self.__concatenate_dict(d_methods, self.__symbol_table[c.name]['methods'])

        # We iterate over each class
        for c in self.__a_ast.classes:

            # We initialize the method type list
            obj_type_l = []

            # We iterate over each methods of the class
            for key, value in self.__symbol_table[c.name]['methods'].items():
                obj_type_l += [self.__symbol_table[c.name]['methods'][key]['obj_type'].as_pointer()]

            # We set the 'struct' of the class
            fields_type_list = []

            for key, value in self.__symbol_table[c.name]['fields'].items():
                fields_type_list += [self.__get_type(value['type'])]

            body_list = [self.__symbol_table[c.name]['struct_vtable'].as_pointer()] + fields_type_list
            self.__symbol_table[c.name]['struct'].set_body(*body_list)

            # We set the 'struct_vtable' of the class
            self.__symbol_table[c.name]['struct_vtable'].set_body(*obj_type_l)

        # We iterate over each class
        for c in self.__a_ast.classes:

            # We get useful element
            d_class = self.__symbol_table[c.name]

            # We set the global VTable
            const = ir.Constant(d_class['struct_vtable'], [value['obj'] for value in d_class['methods'].values()])

            d_class['global_vtable'] = ir.GlobalVariable(self.__module, const.type, name='{}_vtable'.format(c.name))
            d_class['global_vtable'].initializer = const
            d_class['global_vtable'].global_constant = True

    def __initialize_object(self):
        # Opaque context reference to group modules into logical groups
        context = ir.Context()

        # New module for 'Object'
        module = ir.Module(name='Object')

        # The two structures defined in object.ll
        struct = context.get_identified_type('struct.Object')
        struct_vtable = context.get_identified_type('struct.ObjectVTable')

        # Create the body of the Object structure (contains a pointer to the VTable)
        struct.set_body(*[struct_vtable.as_pointer()])

        # Set the method types
        m_print_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(), t_string))
        m_print_bool_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(), t_bool))
        m_print_int32_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(), t_int32))

        m_input_line_type = ir.FunctionType(t_string, (struct.as_pointer(),))
        m_input_bool_type = ir.FunctionType(t_bool, (struct.as_pointer(),))
        m_input_int32_type = ir.FunctionType(t_int32, (struct.as_pointer(),))

        # Declare the methods
        m_print = ir.Function(module, m_print_type, 'Object_print')
        m_print_bool = ir.Function(module, m_print_bool_type, 'Object_printBool')
        m_print_int32 = ir.Function(module, m_print_int32_type, 'Object_printInt32')

        m_input_line = ir.Function(module, m_input_line_type, 'Object_inputLine')
        m_input_bool = ir.Function(module, m_input_bool_type, 'Object_inputBool')
        m_input_int32 = ir.Function(module, m_input_int32_type, 'Object_inputInt32')

        # Create the body of the VTable structure
        struct_vtable.set_body(*[
            m_print_type.as_pointer(),
            m_print_bool_type.as_pointer(),
            m_print_int32_type.as_pointer(),
            m_input_line_type.as_pointer(),
            m_input_bool_type.as_pointer(),
            m_input_int32_type.as_pointer()
        ])

        # We create the constructor
        init_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(), ))
        init = ir.Function(module, init_type, name='Object_init')

        constr_type = ir.FunctionType(struct.as_pointer(), ())
        constr = ir.Function(module, constr_type, name='Object_new')

        # We create the dictionary with each method
        d_methods = OrderedDict()

        d_methods['print'] = {'args': {'s': 'string'}, 'ret': 'Object', 'obj_type': m_print_type, 'obj': m_print}
        d_methods['printBool'] = {'args': {'b': 'bool'}, 'ret': 'Object', 'obj_type': m_print_bool_type, 'obj': m_print_bool}
        d_methods['printInt32'] = {'args': {'i': 'int32'}, 'ret': 'Object', 'obj_type': m_print_int32_type, 'obj': m_print_int32}
        d_methods['inputLine'] = {'args': {}, 'ret': 'string', 'obj_type': m_input_line_type, 'obj': m_input_line}
        d_methods['inputBool'] = {'args': {}, 'ret': 'bool', 'obj_type': m_input_bool_type, 'obj': m_input_bool}
        d_methods['inputInt32'] = {'args': {}, 'ret': 'int32', 'obj_type': m_input_int32_type, 'obj': m_input_int32}

        # We create the dictionary for the 'Object' element
        d_object = {
            'struct': struct,
            'struct_vtable': struct_vtable,
            'global_vtable': ir.GlobalVariable(module, struct_vtable, name='Object_vtable'),
            'new': constr,
            'init': init,
            'fields': OrderedDict(),
            'methods': d_methods,
            'parent': None
        }

        d_object['global_vtable'].global_constant = True

        # We add the 'Object' class to the symbol table
        self.__symbol_table['Object'] = d_object

    def __initialize_constr(self):
        # For each element in the symbol table, create
        # methods 'init' and 'new' (except for 'Object')
        for c in self.__symbol_table:
            if c != 'Object':
                self.__initialize_init(c)
                self.__initialize_new(c)

    def __initialize_init(self, name):
        # We get useful elements
        struct = self.__symbol_table[name]['struct']
        parent = self.__symbol_table[name]['parent']

        # We create the type of the init
        init_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(),))

        # We create the init
        init = ir.Function(self.__module, init_type, name='{}_init'.format(name))

        # We create the body of the init
        block = init.append_basic_block()
        self.__builder = ir.IRBuilder(block)

        # We create basic block
        if_bb = init.append_basic_block('if')
        endif_bb = init.append_basic_block('endif')

        # We compare the element to 'null'
        cmp_val = self.__builder.icmp_signed('!=', init.args[0], ir.Constant(struct.as_pointer(), None))
        self.__builder.cbranch(cmp_val, if_bb, endif_bb)

        # We contruct the 'if' basic block
        self.__builder.position_at_end(if_bb)

        bitcast = self.__builder.bitcast(init.args[0], self.__symbol_table[parent]['struct'].as_pointer())
        self.__builder.call(self.__symbol_table[parent]['init'], (bitcast,))

        gep = self.__builder.gep(init.args[0], [t_int32(0), t_int32(0)], inbounds=True)
        self.__builder.store(self.__symbol_table[name]['global_vtable'], gep)

        # Initialize fields' value
        number_fields = len(self.__symbol_table[name]['fields'])

        for i in range(number_fields - self.__get_number_fields(name), number_fields):
            f = list(self.__symbol_table[name]['fields'].values())[i]

            if f['init_expr'] is not None:
                init_val = self.__codegen(f['init_expr'], [])
            else:
                if f['type'] == 'int32':
                    init_val = ir.Constant(t_int32, 0)
                elif f['type'] == 'bool':
                    init_val = ir.Constant(t_bool, 0)
                elif f['type'] == 'string':
                    string = ''
                    string_val = ir.Constant(ir.ArrayType(ir.IntType(8), len(string)), bytearray(string.encode('utf8')))

                    global_val = ir.GlobalVariable(self.__module, string_val.type, name='string_{}'.format(self.__count_string))
                    global_val.linkage = ''
                    global_val.global_constant = True
                    global_val.initializer = string_val

                    init_val = self.__builder.gep(global_val, [t_int32(0), t_int32(0)], inbounds=True)

                    self.__count_string += 1
                else:
                    init_val = ir.Constant(self.__symbol_table[f['type']]['struct'].as_pointer(), None)

            gep = self.__builder.gep(init.args[0], [t_int32(0), t_int32(i + 1)])
            self.__builder.store(init_val, gep)

        self.__builder.branch(endif_bb)

        # We construct the 'endif' basic block
        self.__builder.position_at_end(endif_bb)
        self.__builder.ret(init.args[0])

        # We save the init
        self.__symbol_table[name]['init'] = init

    def __initialize_new(self, name):
        # We get useful elements
        struct = self.__symbol_table[name]['struct']

        # We create the type of the constructor
        constr_type = ir.FunctionType(struct.as_pointer(), ())

        # We create the constructor
        constr = ir.Function(self.__module, constr_type, name='{}_new'.format(name))

        # We create the body of the constructor
        block = constr.append_basic_block()
        self.__builder = ir.IRBuilder(block)

        gep = self.__builder.gep(ir.Constant(struct.as_pointer(), None), [t_int32(1)], name='size_as_ptr')
        ptrtoint = self.__builder.ptrtoint(gep, t_int64, name='size_as_i64')

        ptr = self.__builder.call(self.__imported_functions['malloc'], [ptrtoint])
        bitcast = self.__builder.bitcast(ptr, struct.as_pointer())
        ret = self.__builder.call(self.__symbol_table[name]['init'], [bitcast])

        self.__builder.ret(ret)

        # We save the constructor
        self.__symbol_table[name]['new'] = constr

    def __initialize_primitives(self):
        # We add primitives types to the symbol table
        self.__symbol_table['int32'] = {'struct': t_int32}
        self.__symbol_table['bool'] = {'struct': t_bool}
        self.__symbol_table['string'] = {'struct': t_string}
        self.__symbol_table['unit'] = {'struct': t_unit}

    ###########
    # Analyze #
    ###########

    def __analyze(self):
        # We analyze each method
        self.__analyze_methods()

    def __analyze_methods(self):
        # We iterate over each class
        for c in self.__a_ast.classes:

            # We update the current class
            self.__current_class = c.name

            # We iterate over each method
            for m in c.methods:

                # We get useful information
                d_method = self.__symbol_table[c.name]['methods'][m.name]

                # We create a block
                block = d_method['obj'].append_basic_block()

                # We set the builder
                self.__builder = ir.IRBuilder(block)

                # We create a dictionary for the arguments
                d_args = {}

                # We check if we are in the main method of the program
                if c.name == 'Main' and m.name == 'main':
                    # We allocate space for self
                    alloca = self.__builder.alloca(self.__symbol_table[c.name]['struct'].as_pointer())

                    # We get the 'new' function
                    f_new = self.__symbol_table[c.name]['new']

                    # Call the function
                    value = self.__builder.call(f_new, ())

                    # Store the value
                    self.__builder.store(value, alloca)

                    # We add the element to the dictionary
                    d_args['self'] = alloca
                else:
                    # We get the args
                    args = d_method['obj'].args

                    # The first argument is the object itself
                    alloca = self.__builder.alloca(args[0].type)
                    self.__builder.store(args[0], alloca)
                    d_args['self'] = alloca

                    # We iterate over each formals
                    for i, f in enumerate(d_method['args'].values()):

                        # We allocate space
                        alloca = self.__builder.alloca(args[i + 1].type)

                        # We store the value
                        self.__builder.store(args[i + 1], alloca)

                        # We add the formal to the dictionnary
                        d_args[f] = alloca

                # We analyze the body of the method
                value = self.__codegen(m.block, [d_args])

                # We return the value
                if value == t_void:
                    self.__builder.ret_void()
                else:
                    self.__builder.ret(value)

    ###################
    # Code generation #
    ###################

    def __codegen(self, node, stack):
        # We get the method name corresponding to the node
        method = '_codegen_' + node.__class__.__name__

        # We return the value of the expression
        return getattr(self, method)(node, stack)

    def _codegen_If(self, node, stack):
        # We get the comparison value
        cond_val = self.__codegen(node.cond_expr, stack)
        cmp_val = self.__builder.fcmp_ordered('!=', cond_val, ir.Constant(ir.DoubleType(), 0.0), 'notnull')

        # We create basic blocks to express the control flow
        then_bb = self.__builder.append_basic_block('then')

        if node.else_expr is not None:
            else_bb = self.__builder.append_basic_block('else')

        merge_bb = self.__builder.append_basic_block('endif')

        # We branch to either then_bb or merge/else_bb depending on 'cmp_val'
        if node.else_expr is not None:
            self.__builder.cbranch(cmp_val, then_bb, else_bb)
        else:
            self.__builder.cbranch(cmp_val, then_bb, merge_bb)

        # We emit the 'then' part
        self.__builder.position_at_start(then_bb)
        then_val = self.__codegen(node.then_expr, stack)
        self.__builder.branch(merge_bb)

        # The emission of 'then_val' could have generated a new basic block
        # (and thus modified the current basic block). To properly set up
        # the PHI, we remember which block the 'then' part ends in.
        then_bb = self.__builder.block

        # We emit the 'else' part
        if node.else_expr is not None:
            self.__builder.position_at_start(else_bb)
            else_val = self.__codegen(node.else_expr, stack)
            self.__builder.branch(merge_bb)

            # Same remark as for 'then_val'
            else_bb = self.__builder.block

        # We emit the 'merge' block
        self.__builder.position_at_start(merge_bb)

        phi = self.__builder.phi(ir.DoubleType(), 'ifval')
        phi.add_incoming(then_val, then_bb)

        if node.else_expr is not None:
            phi.add_incoming(else_val, else_bb)

        return phi

    def _codegen_While(self, node, stack):
        # We create basic blocks
        cond_bb = self.__builder.append_basic_block('cond')
        loop_bb = self.__builder.append_basic_block('loop')
        end_bb = self.__builder.append_basic_block('endwhile')

        # We enter the condition
        self.__builder.branch(cond_bb)

        # We build the condition
        self.__builder.position_at_end(cond_bb)
        cond_val = self.__codegen(node.cond_expr, stack)
        self.__builder.cbranch(cond_val, loop_bb, end_bb)

        # We build the loop
        self.__builder.position_at_end(loop_bb)
        loop_val = self.__codegen(node.body_expr, stack)
        self.__builder.branch(cond_bb)

        # We return after the loop
        self.__builder.position_at_end(end_bb)

        # We return a void type
        return t_void

    def _codegen_Let(self, node, stack):
        # We get the type of the assignee
        assignee_type = self.__symbol_table[node.type]['struct']

        # We allocate space for the argument
        arg_ptr = self.__builder.alloca(assignee_type)

        # If the element is initialized
        if node.init_expr is not None:

            # We get the value of the initialize
            value = self.__codegen(node.init_expr, stack)

            # We cast and store the value
            cast = self.__builder.bitcast(value, assignee_type)
            self.__builder.store(cast, arg_ptr)

        # If the element is not initialized
        else:

            # We create a null value
            value = ir.Constant(assignee_type, None)
            self.__builder.store(value, arg_ptr)

        # Create a new symbol table (dictionary) for the 'let'
        d_let = {node.name: arg_ptr}

        # Return the value of the block
        return self.__codegen(node.scope_expr, [d_let] + stack)

    def _codegen_Assign(self, node, stack):
        # We get the type of the assignee
        assignee_type = self.__symbol_table[node.expr_type]['struct']

        # We get the value assigned
        value = self.__codegen(node.expr, stack)

        # We get the pointer to the assignee
        assignee_ptr = self.__lookup(stack, node.name)

        # If the pointer exists, it means that the assignee
        # is an argument of a function
        if assignee_ptr is not None:

            # We cast the value
            cast = self.__builder.bitcast(value, assignee_type)

            # We store the new value
            self.__builder.store(cast, assignee_ptr)

        # If it is not an argument of a function, it means
        # that it is a field of an object
        else:

            # We get the pointer to the element itself
            ptr_self = self.__builder.load(self.__lookup(stack, 'self'))

            # We get field information
            d_field = self.__symbol_table[self.__current_class]['fields'][node.name]

            # We get the field offset
            field_offset = self.__get_position(self.__symbol_table[self.__current_class]['fields'], node.name)
            field_offset += 1

            # We get the pointer to the field
            ptr_field = self.__builder.gep(ptr_self, [t_int32(0), t_int32(field_offset)], inbounds=True)

            # We cast the value
            cast = self.__builder.bitcast(value, self.__get_type(d_field['type']))

            # We store the new value
            self.__builder.store(cast, ptr_field)

        # We return the value
        return value

    def _codegen_UnOp(self, node, stack):
        # We get the value of the expression
        expr_value = self.__codegen(node.expr, stack)

        # We call the corresponding method
        if node.op == 'not':
            if expr_value == t_bool(1):
                return t_bool(0)
            else:
                return t_bool(1)
        elif node.op == '-':
            return self.__builder.sub(t_int32(0), expr_value, 'subtmp')
        elif node.op == 'isnull':
            return self.__builder.icmp_signed('!=', expr_value, ir.Constant(self.__get_type(node.expr.expr_type).as_pointer(), None))

    def _codegen_BinOp(self, node, stack):
        # We get left and right operands
        lhs = self.__codegen(node.left_expr, stack)
        rhs = self.__codegen(node.right_expr, stack)

        # We call the corresponding method
        if node.op == 'and':
            if lhs == t_bool(1):
                if rhs == t_bool(1):
                    return t_bool(1)

            return t_bool(0)
        elif node.op == '=':
            expr_type = node.left_expr.type

            if expr_type in ['int32', 'bool']:
                return self.__builder.icmp_signed('==', lhs, rhs)
            elif expr_type == 'string':
                call = self.__builder.call(self.__imported_functions['strcmp'], [lhs, rhs])

                return self.__builder.icmp_signed('==', call, t_int32(0))
            elif expr_type == 'unit':
                return t_bool(1)
            else:
                obj_type = self.__symbol_table['Object']['struct']

                lhs_addr = self.__builder.bitcast(lhs, obj_type)
                rhs_addr = self.__builder.bitcast(rhs, obj_type)

                return self.__builder.icmp_signed('==', lhs_addr, rhs_addr)
        elif node.op == '<':
            return self.__builder.icmp_signed('<', lhs, rhs, 'lowtmp')
        elif node.op == '<=':
            return self.__builder.icmp_signed('<=', lhs, rhs, 'loweqtmp')
        elif node.op == '+':
            return self.__builder.add(lhs, rhs, 'addtmp')
        elif node.op == '-':
            return self.__builder.sub(lhs, rhs, 'subtmp')
        elif node.op == '*':
            return self.__builder.mul(lhs, rhs, 'multmp')
        elif node.op == '/':
            return self.__builder.sdiv(lhs, rhs, 'divtmp')
        elif node.op == '^':
            # We cast the operands to 'double' (in order to call the
            # 'pow' function)
            lhs_double = self.__builder.uitofp(lhs, t_double)
            rhs_double = self.__builder.uitofp(rhs, t_double)

            # Call the 'pow' function
            call = self.__builder.call(self.__imported_functions['pow'], (lhs_double, rhs_double))

            # Return the result (converted to int)
            return self.__builder.fptoui(call, t_int32)

    def _codegen_Call(self, node, stack):
        # We get the pointer to the caller
        ptr_caller = self.__codegen(node.obj_expr, stack)

        # We get the type (class name) of the caller
        ptr_type = node.obj_expr.expr_type

        # We get useful information
        d_class = self.__symbol_table[ptr_type]
        d_method = d_class['methods'][node.method_name]

        # We get the position of the method in the VTable
        method_offset = self.__get_position(self.__symbol_table[ptr_type]['methods'], node.method_name)

        # We get the VTable
        gep_vtable = self.__builder.gep(ptr_caller, [t_int32(0), t_int32(0)], inbounds=True)
        vtable = self.__builder.load(gep_vtable)

        # We get the method
        gep_method = self.__builder.gep(vtable, [t_int32(0), t_int32(method_offset)], inbounds=True)
        method = self.__builder.load(gep_method)

        # We cast the element, if necessary
        if d_method['obj'].args[0] != d_class['struct']:
            ptr_caller = self.__builder.bitcast(ptr_caller, d_method['obj_type'].args[0])

        # We get the argument list
        args_list = [ptr_caller]

        # We iterate over each argument
        for i, arg in enumerate(node.expr_list):

            # We get the value of the argument
            arg_value = self.__codegen(arg, stack)

            # We cast the argument
            arg_value = self.__builder.bitcast(arg_value, d_method['obj_type'].args[i + 1])

            # We add the argument to the list
            args_list += [arg_value]

        # We call the method
        return self.__builder.call(method, args_list)

    def _codegen_New(self, node, stack):
        # We get the 'new' function of the element
        f_new = self.__symbol_table[node.type_name]['new']

        # We call the 'new' function and return the element
        return self.__builder.call(f_new, ())

    def _codegen_Self(self, node, stack):
        # The only case where the class 'Self' is used is
        # in the 'Call' node. So we have to return a pointer
        # to the element itself (element which call the
        # method)
        return self.__builder.load(self.__lookup(stack, 'self'))

    def _codegen_ObjectIdentifier(self, node, stack):
        # We get the element
        e = self.__lookup(stack, node.id)

        # If the element exists, it means that it is an
        # argument of the function
        if e is not None:

            # We store the value
            value = self.__builder.load(e)

        # If the element does not exist, it means that it
        # is a field of the object
        else:

            # We get the pointer to the element itself
            ptr_self = self.__builder.load(self.__lookup(stack, 'self'))

            # We get the position of the field in the object structure
            offset = self.__get_position(self.__symbol_table[self.__current_class]['fields'], node.id)

            # Because the first element of the structure is the VTable
            offset += 1

            # We get the pointer to the field
            ptr_field = self.__builder.gep(ptr_self, [t_int32(0), t_int32(offset)], inbounds=True)

            # We store the value
            value = self.__builder.load(ptr_field)

        return value

    def _codegen_Literal(self, node, stack):
        # If literal is a 'int32'
        if node.type == 'integer':
            return t_int32(node.literal)

        # If literal is a 'bool'
        elif node.type == 'boolean':
            return t_bool(1 if node.literal == 'true' else 0)

        # If literal is a 'string'
        elif node.type == 'string':
            string = self.__process_string(node.literal)

            string_val = ir.Constant(ir.ArrayType(ir.IntType(8), len(string)), bytearray(string.encode('utf8')))

            global_val = ir.GlobalVariable(self.__module, string_val.type, name='string_{}'.format(self.__count_string))
            global_val.linkage = ''
            global_val.global_constant = True
            global_val.initializer = string_val

            self.__count_string += 1

            return self.__builder.gep(global_val, [t_int32(0), t_int32(0)], inbounds=True)

    def _codegen_Unit(self, node, stack):
        return t_unit

    def _codegen_Block(self, node, stack):
        # We iterate over each expression
        for e in node.expr_list:
            value = self.__codegen(e, stack)

        # We return the value of the block (i.e. the value
        # of the last expression of the block)
        return value

    ####################
    # Public functions #
    ####################

    def generate_ir(self):
        # We check all classes and methods and initialize the
        # symbol table as well as the 'init' and 'new' methods
        self.__initialize()

        # We analyze each expression in order to generate
        # LLVM IR code
        self.__analyze()

        # We get the LLVM IR code
        llvm_ir = str(self.__module)

        # We remove the first two lines
        llvm_ir = llvm_ir.split('\n', 2)[2]

        # We append the LLVM IR code of the 'Object' class
        with open('llvm/object/object.ll', 'r') as object_file:
            llvm_ir = object_file.read() + llvm_ir

        # We return the complete LLVM IR code
        return llvm_ir

    def generate_exec(self, llvm_ir):
        # Get the base name of the source file
        basename = os.path.splitext(self.__filename)[0]

        # Export the LLVM IR code in a '.ll' file
        ll_name = '{}.ll'.format(basename)

        with open(ll_name, 'w') as ll_file:
            ll_file.write(llvm_ir)

        # Transform the LLVM code to assembly
        command = 'llc-9 {}'.format(ll_name)
        os.system(command)

        # Compile assembly file to create an executable
        command = 'clang {}.s -o {} -lm'.format(basename, basename)
        os.system(command)
