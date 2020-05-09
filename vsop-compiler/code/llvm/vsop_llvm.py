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

        # Current class and method
        self.__current_class = None
        self.__current_method = None

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
        # First, we add the 'Object' class to the symbol table
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

            while parent != None:
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
        self.builder = ir.IRBuilder(block)

        # We create basic block
        if_bb = init.append_basic_block('if')
        endif_bb = init.append_basic_block('endif')

        # We compare the element to 'null'
        cmp_val = self.builder.icmp_signed('!=', init.args[0], ir.Constant(struct.as_pointer(), None))
        self.builder.cbranch(cmp_val, if_bb, endif_bb)

        # We contruct the 'if' basic block
        self.builder.position_at_end(if_bb)

        bitcast = self.builder.bitcast(init.args[0], self.__symbol_table[parent]['struct'].as_pointer())
        self.builder.call(self.__symbol_table[parent]['init'], (bitcast,))

        gep = self.builder.gep(init.args[0], [t_int32(0), t_int32(0)], inbounds=True)
        self.builder.store(self.__symbol_table[name]['global_vtable'], gep)

        # Initialize fields' value
        number_fields = len(self.__symbol_table[name]['fields'])

        for i in range(number_fields - self.__get_number_fields(name), number_fields):
            f = list(self.__symbol_table[name]['fields'].values())[i]

            if f['init_expr'] is not None:
                init_val = self.__codegen(f['init_expr'])
            else:
                if f['type'] == 'int32':
                    init_val = ir.Constant(t_int32, 0)
                elif f['type'] == 'bool':
                    init_val = ir.Constant(t_bool, 0)
                elif f['type'] == 'string':
                    string = ''
                    init_val = ir.Constant(ir.ArrayType(ir.IntType(8), len(string)), bytearray(string.encode('utf8')))
                else:
                    init_val = ir.Constant(self.__symbol_table[f['type']]['struct'], None)

            gep = self.builder.gep(init.args[0], [t_int32(0), t_int32(i + 1)])
            self.builder.store(init_val, gep)

        self.builder.branch(endif_bb)

        # We construct the 'endif' basic block
        self.builder.position_at_end(endif_bb)
        self.builder.ret(init.args[0])

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
        self.builder = ir.IRBuilder(block)

        gep = self.builder.gep(ir.Constant(struct.as_pointer(), None), [t_int32(1)], name='size_as_ptr')
        ptrtoint = self.builder.ptrtoint(gep, t_int64, name='size_as_i64')

        ptr = self.builder.call(self.__imported_functions['malloc'], [ptrtoint])
        bitcast = self.builder.bitcast(ptr, struct.as_pointer())
        ret = self.builder.call(self.__symbol_table[name]['init'], [bitcast])

        self.builder.ret(ret)

        # We save the constructor
        self.__symbol_table[name]['new'] = constr

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

                # We update the current method
                self.__current_method = m.name

                # We analyze each method
                self.__codegen(m.block)

    ###################
    # Code generation #
    ###################

    def __codegen(self, node):
        # We get the method name corresponding to the node
        method = '_codegen_' + node.__class__.__name__

        # We return the value of the expression
        return getattr(self, method)(node)

    def _codegen_If(self, node):
        # We get the comparison value
        cond_val = self.__codegen(node.cond_expr)
        cmp_val = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(ir.DoubleType(), 0.0), 'notnull')

        # We create basic blocks to express the control flow
        then_bb = self.builder.append_basic_block('then')

        if node.else_expr is not None:
            else_bb = self.builder.append_basic_block('else')

        merge_bb = self.builder.append_basic_block('endif')

        # We branch to either then_bb or merge/else_bb depending on 'cmp_val'
        if node.else_expr is not None:
            self.builder.cbranch(cmp_val, then_bb, else_bb)
        else:
            self.builder.cbranch(cmp_val, then_bb, merge_bb)

        # We emit the 'then' part
        self.builder.position_at_start(then_bb)
        then_val = self.__codegen(node.then_expr)
        self.builder.branch(merge_bb)

        # The emission of 'then_val' could have generated a new basic block 
        # (and thus modified the current basic block). To properly set up
        # the PHI, we remember which block the 'then' part ends in.
        then_bb = self.builder.block

        # We emit the 'else' part
        if node.else_expr is not None:
            self.builder.position_at_start(else_bb)
            else_val = self.__codegen(node.else_expr)
            self.builder.branch(merge_bb)

            # Same remark as for 'then_val'
            else_bb = self.builder.block

        # We emit the 'merge' block
        self.builder.position_at_start(merge_bb)

        phi = self.builder.phi(ir.DoubleType(), 'ifval')
        phi.add_incoming(then_val, then_bb)

        if node.else_expr is not None:
            phi.add_incoming(else_val, else_bb)

        return phi

    def _codegen_While(self, node):
        # We create basic blocks
        cond_bb = self.builder.append_basic_block('cond')
        loop_bb = self.builder.append_basic_block('loop')
        end_bb = self.builder.append_basic_block('endwhile')

        # We enter the condition
        self.builder.branch(cond_bb)

        # We build the condition
        self.builder.position_at_end(cond_bb)
        cond_val = self.__codegen(node.cond_expr)
        self.builder.cbranch(cond_val, loop_bb, end_bb)

        # We build the loop
        self.builder.position_at_end(loop_bb)
        loop_val = self.__codegen(node.body_expr)
        self.builder.branch(cond_bb)

        # We return after the loop
        self.builder.position_at_end(end_bb)

        # We return a void type
        return t_void

    def _codegen_Let(self, node):
        pass

    def _codegen_Assign(self, node):
        pass

    def _codegen_UnOp(self, node):
        # We get the value of the expression
        expr_value = self.__codegen(node.expr)

        # We call the corresponding method
        if node.op == 'not':
            pass # TO DO
        elif node.op == '-':
            return self.builder.sub(ir.Constant(t_int32, 0), expr_value, 'subtmp')
        elif node.op == 'isnull':
            pass # TO DO

    def _codegen_BinOp(self, node):
        # We get left and right operands
        lhs = self.__codegen(node.left_expr)
        rhs = self.__codegen(node.right_expr)

        # We call the corresponding method
        if node.op == 'and':
            pass # TO DO
        elif node.op == '=':
            pass # TO DO
        elif node.op == '<':
            return self.builder.icmp_signed('<', lhs, rhs, 'lowtmp')
        elif node.op == '<=':
            return self.builder.icmp_signed('<=', lhs, rhs, 'loweqtmp')
        elif node.op == '+':
            return self.builder.add(lhs, rhs, 'addtmp')
        elif node.op == '-':
            return self.builder.sub(lhs, rhs, 'subtmp')
        elif node.op == '*':
            return self.builder.mul(lhs, rhs, 'multmp')
        elif node.op == '/':
            return self.builder.sdiv(lhs, rhs, 'divtmp')
        elif node.op == '^':
            pass # TO DO

    def _codegen_Call(self, node):
        pass

    def _codegen_New(self, node):
        pass

    def _codegen_Self(self, node):
        pass

    def _codegen_ObjectIdentifier(self, node):
        pass

    def _codegen_Literal(self, node):
        # If literal is a 'int32'
        if node.type == 'integer':
            return ir.Constant(t_int32, int(node.literal))

        # If literal is a 'bool'
        elif node.type == 'boolean':
            return ir.Constant(t_bool, (1 if node.literal == 'true' else 0))

        # If literal is a 'string'
        elif node.type == 'string':
            return ir.Constant(
                ir.ArrayType(t_string, len(node.literal)),
                bytearray((node.literal).encode('utf8'))
            )

    def _codegen_Unit(self, node):
        pass

    def _codegen_Block(self, node):
        # We get the current method
        m = self.__symbol_table[self.__current_class]['methods'][self.__current_method]['obj']

        # We append the block
        block = m.append_basic_block()

        # We update the builder
        self.builder = ir.IRBuilder(block)


        return ret

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
