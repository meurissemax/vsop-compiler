"""
INFO0085-1 - Compilers
University of Liege
Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""

import llvmlite.ir as ir
import llvmlite.binding as llvm
import copy


## Definition of the types
int32 = ir.IntType(32)
int8 = ir.IntType(8)
boolean = ir.IntType(1)

###########
# Classes #
###########

class CodegenError(Exception): pass

class LLVMCodeGenerator:
    ###############
    # Constructor #
    ###############

    def __init__(self, a_ast):
        """
        This creates a new LLVM module into which code is generated.
        generate_code() can be called multiple times and it adds the code 
        generated for this node into the module and returns the IR value for
        the node.
        """
        # We save the annotated AST to generate LLVM code
        self.__a_ast = a_ast

        # We'll create a single module for this project
        self.module = ir.Module()

        # Current IR builder
        self.builder = None

        # Symbol table while codegenerating a function. Maps the names
        # of the variables to ir.Value.
        self.funcSymTab = {}

        # Types 
        self.int32 = ir.IntType(32)
    
    def generate_code(self, node):
        return self._codegen(node)
    
    def _codegen(self, node):
        method = '_codegen_' + node.__class__.__name__
        return getattr(self, method)(node)
    
    def _codegen_BinOp(self, node):
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
            return self._codegen_POW(lhs, rhs) # TODO
        elif node.op == "AND":
            return self._codegen_AND(lhs, rhs)
        elif node.op == "EQUAL":
            return self._codegen_EQUAL(lhs, rhs)
        elif node.op == "LOWER":
            return self.builder.icmp_signed("<", lhs, rhs, 'lowtmp')
        elif node.op == "LOWER_EQUAL":
            return self.builder.icmp_signed("<=", lhs, rhs, 'loweqtmp')
        else:
            raise CodegenError('Unknown binary operator', node.op)
    
    def _codegen_POW(self, lhs, rhs):
        # Not sure whether or not this is correct
        if rhs == 0:
            return self.builder.add(1, 0, 'powtmp')
        elif rhs == 1:
            return self.builder.mul(lhs, 1, 'powtmp')
        else:
            return self.builder.mul(self.builder.mul(lhs, 1, 'powtmp'), self._codegen_POW(lhs, rhs-1))

    def _codegen_AND(self, lhs, rhs):
        # Not sure whether or not this is correct
        if lhs == True:
            return self.builder.icmp_signed("==", rhs, 1, 'andtmp')
        else:
            return self.builder.icmp_signed("==", lhs, 1, 'andtmp')

    def _codegen_EQUAL(self, lhs, rhs):
        #pass
    
    ## Expressions

    def _codegen_IF(self, node, symbolTable):
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


    def _codegen_WHILE(self, node, symbolTable):
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

    
    def _codegen_LET(self, node):
        pass

    def _codegen_Literal(self, node):
        if node._type == 'bool':
            return ir.IntType()(1 if node.literal == 'true' else 0)
        if node._type == 'int32':
            return self.int32(node.literal)
        if node._type == 'string':
            return ir.Constant(ir.ArrayType(ir.IntType(8), len(node.literal)),
                            bytearray((node.literal).encode("utf8")))
        if node._type == 'unit':
            return ir.VoidType()
        
    def _codegen_Unit(self, node):
        # Pas déjà dans les literals ?
        pass

    def _codegen_Unop(self, node):
        # Is it simply - ?
        pass
    
    def _codegen_Assign(self, node, symbTable):
        symbTable[node.name] = self._codegen(node.expr)
        return symbTable[node.name]
        # When is it called again ? 
    
    def _codegen_Block(self, node, symbTable):
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
    
    def _codegen_ObjectIdentifier(self, node, symbTable):
        pass

    def _codegen_Let(self, node, symbTable):

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


    def _codegen_Call(self, node, symbTable):
        pass
    
    def _codegen_


    ###################
    # Code generation #
    ###################

    # Used to link the given object.ll file
    def link_object():
        # Opaque context reference to group modules into logical groups
        context = ir.Context()
        # Module of object.ll
        mod = ir.Module(name = "modObject")
        # The two structures defined in object.ll
        structObject = context.get_identified_type("struct.Object")
        structObjectVTable = context.get_identified_type("struct.ObjectVTable")
        
        # Create the body of the Object structure (contains a pointer to the VTable)
        structObject.set_body(structObjectVTable.as_pointer())
        
        # Set the methods types and then declare them
        objPrintType = ir.FunctionType(structObject.as_pointer(), (structObject.as_pointer(), int8.as_pointer()) )
        # Zero Ext ? 
        objPrintBoolType = ir.FunctionType(structObject.as_pointer(), (structObject.as_pointer(), boolean) )
        objPrintI32Type = ir.FunctionType(structObject.as_pointer(), (structObject.as_pointer(), int32) )
        objInputLineType = ir.FunctionType(int8.as_pointer(), (structObject.as_pointer()) ) 
        objInputBoolType = ir.FunctionType(boolean, (structObject.as_pointer()) )
        objInputInt32Type = ir.FunctionType(int32, (structObject.as_pointer()) )

        objPrint = ir.Function(mod, objPrintType, "object_print")
        objPrintBool = ir.Function(mod, objPrintBoolType, "object_printBool")
        objPrintI32 = ir.Function(mod, objPrintI32Type, "object_printInt32")
        objInputLine = ir.Function(mod, objInputLineType, "object_inputLine")
        objInputBool = ir.Function(mod, objInputBoolType, "object_inputBool")
        objInputInt32 = ir.Function(mod, objInputInt32Type, "object_inputINt32")

        # Create the body of the VTable structure. Contains the previously defined functions in it
        structObjectVTable.set_body(objPrint.as_pointer(), objPrintBool.as_pointer(), objPrintI32.as_pointer(), 
                                    objInputLine.as_pointer(), objInputBool.as_pointer(), objInputInt32.as_pointer())
        
        # Finally, set the Object's shared vtable instance
        pass




    def generate(self):
        return 'TO DO'

    def generate_exec(self, llvm_code):
        print('TO DO')
