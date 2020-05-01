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
import copy

import llvmlite.ir as ir
import llvmlite.binding as llvm


####################
# Type definitions #
####################

int32 = ir.IntType(32)
int8 = ir.IntType(8)
boolean = ir.IntType(1)


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
        self.module = ir.Module(name=__file__)

        # Current IR builder
        self.builder = None

        # Base symbol table that will contains all
        # the symbol tables of the classes
        self.__symbol_table = {}

    #############################################
    # LLVM IR code generation (node of the AST) #
    #############################################

    def __codegen(self, node, stack):
        # We get the method name corresponding to the node
        method = '_codegen_' + node.__class__.__name__

        # We return the LLVM IR code
        return getattr(self, method)(node)

    def __codegen_If(self, node, stack):
        # May not be entirely correct, to check.
        if_expr = self._codegen(node.cond_expr, symbolTable)

        # No else
        if node.else_expr == None:
            with self.builder.if_then(if_expr):
                return self._codegen(node.then_expr)

        else:
            with self.builder.if_else as (then, otherwise):
                with then:
                    bl_then = self.builder.basic_block
                    val_then = self._codegen(node.then_expr, symbolTable)
                with otherwise:
                    bl_other = self.builder.basic_block
                    val_other = self._codegen(node.else_expr, symbolTable)
            val = self.builder.phi() # What's the type of the If ?
            pass

    def __codegen_While(self, node, stack):
        # Create the different blocks
        bl_cond = self.builder.append_basic_block("cond")
        bl_loop = self.builder.append_basic_block("loop")
        bl_end = self.builder.append_basic_block("end")

        # Evaluate the condition
        self.builder.branch(bl_cond)
        self.builder.position_at_end(bl_cond)
        cond_expr = self._codegen(node.cond_expr, symbolTable)

        # Conditional jump to the loop of to the end
        self.builder.cbranch(cond_expr, bl_loop, bl_end)

        # Creation of the loop
        self.builder.position_at_end(bl_loop)
        loop_expr = self._codegen(node, symbolTable)
        self.builder.branch(bl_cond)

        # End of the loop
        self.builder.position_at_end(bl_end)
        return self.builder.ret_void()

    def __codegen_Let(self, node, stack):
        symbolTable = copy.deepcopy(symbTable)

        # Should we add a block ?

        if node.init_expr is not None:
            init_value = self.builder._codegen(node.init_expr, symbolTable)
            symbolTable[node.name] = init_value
        # Default initialization
        else:
            if node._type == 'int32':
                symbolTable[node.name] = 0
            elif node._type == 'bool':
                symbolTable[node.name] = 'false'
            elif node._type == 'string':
                symbolTable[node.name] = ''
            else:
                symbolTable[node.name] = 'null'
        
        # Create a block for the body
        bl_body = self.builder.append_basic_block("body")
        self.builder.branch(bl_body)
        self.builder.position_at_end(bl_body)

        return self.builder._codegen(node.scope_expr, symbolTable)

    def __codegen_Assign(self, node, stack):
        symbTable[node.name] = self._codegen(node.expr)
        return symbTable[node.name]
        # When is it called again ? 

    def __codegen_UnOp(self, node, stack):
        pass

    def __codegen_BinOp(self, node, stack):
        lhs = self._codegen(node.left_expr)
        rhs = self._codegen(node.right_expr)
        
        if node.op == "PLUS":
            return self.builder.add(lhs, rhs, 'addtmp')
        elif node.op == "MINUS":
            return self.builder.sub(lhs, rhs, 'subtmp')
        elif node.op == "TIMES":
            return self.builder.mul(lhs, rhs, 'multmp')
        elif node.op == "DIV":
            return self.builder.sdiv(lhs, rhs, 'divtmp')
        elif node.op == "POW":
            return self.__codegen_pow(lhs, rhs) # TODO
        elif node.op == "AND":
            return self.__codegen_and(lhs, rhs)
        elif node.op == "EQUAL":
            return self.__codegen_equal(lhs, rhs)
        elif node.op == "LOWER":
            return self.builder.icmp_signed("<", lhs, rhs, 'lowtmp')
        elif node.op == "LOWER_EQUAL":
            return self.builder.icmp_signed("<=", lhs, rhs, 'loweqtmp')
        else:
            raise CodegenError('Unknown binary operator', node.op)

    def __codegen_Call(self, node, stack):
        pass

    def __codegen_New(self, node, stack):
        pass

    def __codegen_Self(self, node, stack):
        pass

    def __codegen_ObjectIdentifier(self, node, stack):
        pass

    def __codegen_Literal(self, node, stack):
        if node._type == 'bool':
            return ir.IntType()(1 if node.literal == 'true' else 0)
        if node._type == 'int32':
            return self.int32(node.literal)
        if node._type == 'string':
            return ir.Constant(ir.ArrayType(ir.IntType(8), len(node.literal)),
                            bytearray((node.literal).encode("utf8")))
        if node._type == 'unit':
            return ir.VoidType()

    def __codegen_Unit(self, node, stack):
        pass

    def __codegen_Block(self, node, stack):
        block = self.builder.append_basic_block("in")
        end = self.builder.append_basic_block("end")
        # Copy the parent's symbol table but don't modify it since we are in a block,
        # so all variables are local
        sTable = copy.deepcopy(symbTable)

        for expression in range(node.expr_list)-1:
            self._codegen(node.expr_list[expression], sTable)

        value = self._codegen(node.expr_list[-1], sTable)

        self.builder.branch(end)
        self.builder.position_at_end(end)

        return value

    #################################################
    # LLVM IR code generation (additional elements) #
    #################################################

    def __codegen_pow(self, lhs, rhs):
        # Not sure whether or not this is correct
        if rhs == 0:
            return self.builder.add(1, 0, 'powtmp')
        elif rhs == 1:
            return self.builder.mul(lhs, 1, 'powtmp')
        else:
            return self.builder.mul(self.builder.mul(lhs, 1, 'powtmp'), self._codegen_POW(lhs, rhs-1))

    def __codegen_and(self, lhs, rhs):
        # Not sure whether or not this is correct
        if lhs == True:
            return self.builder.icmp_signed("==", rhs, 1, 'andtmp')
        else:
            return self.builder.icmp_signed("==", lhs, 1, 'andtmp')

    def __codegen_equal(self, lhs, rhs):
        pass

    ################
    # Object class #
    ################

    def __object_ir(self):
        # Opaque context reference to group modules into logical groups
        context = ir.Context()

        # Module of object.ll
        mod = ir.Module(name='object')

        # The two structures defined in object.ll
        struct_object = context.get_identified_type('struct.Object')
        struct_object_vtable = context.get_identified_type('struct.ObjectVTable')

        # Create the body of the Object structure (contains a pointer to the VTable)
        struct_object.set_body(struct_object_vtable.as_pointer())

        # Set the methods types
        obj_print_type = ir.FunctionType(struct_object.as_pointer(), (struct_object.as_pointer(), int8.as_pointer()))
        obj_print_bool_type = ir.FunctionType(struct_object.as_pointer(), (struct_object.as_pointer(), boolean))
        obj_print_int32_type = ir.FunctionType(struct_object.as_pointer(), (struct_object.as_pointer(), int32))

        obj_input_line_type = ir.FunctionType(int8.as_pointer(), (struct_object.as_pointer()))
        obj_input_bool_type = ir.FunctionType(boolean, (struct_object.as_pointer()))
        obj_input_int32_type = ir.FunctionType(int32, (struct_object.as_pointer()))

        # Declare the methods
        obj_print = ir.Function(mod, obj_print_type, 'object_print')
        obj_print_bool = ir.Function(mod, obj_print_bool_type, 'object_printBool')
        obj_print_int32 = ir.Function(mod, obj_print_int32_type, 'object_printInt32')

        obj_input_line = ir.Function(mod, obj_input_line_type, 'object_inputLine')
        obj_input_bool = ir.Function(mod, obj_input_bool_type, 'object_inputBool')
        obj_input_int32 = ir.Function(mod, obj_input_int32_type, 'object_inputInt32')

        # Create the body of the VTable structure. Contains the previously defined functions in it.
        struct_object_vtable.set_body(
            obj_print.as_pointer(),
            obj_print_bool.as_pointer(),
            obj_print_int32.as_pointer(), 
            obj_input_line.as_pointer(),
            obj_input_bool.as_pointer(),
            obj_input_int32.as_pointer()
        )

        # Finally, set the Object's shared vtable instance
        pass

    ####################
    # Public functions #
    ####################

    def generate_ir(self):
        # Generate LLVM IR code

        # TO DO
        # -----
        # 1) Check all methods of all classes and create vtable
        #    (structure in order to use it, but no value yet)
        #
        # 2) Generate code of each expression (field initializer
        #    and method body)

        # Return LLVM IR code generated
        return str(self.module)

    def generate_exec(self, llvm_ir):
        # Initialize code generation
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        # Create a target machine
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()

        # Create a LLVM module object from the IR
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()

        # Export the module in an object file
        o_name = '{}.o'.format(os.path.splitext(self.__filename)[0])

        with open(o_name, 'wb') as o_file:
            o_file.write(target_machine.emit_object(mod))

        # Compile object file to create an executable
        exec_name = os.path.splitext(self.__filename)[0]
        command = 'clang {} -o {}'.format(o_name, exec_name)

        os.system(command)
