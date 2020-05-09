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


####################
# Type definitions #
####################

t_int32 = ir.IntType(32)
t_bool = ir.IntType(1)
t_string = ir.IntType(8)
t_unit = ir.VoidType()


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

    ##################
    # Initialization #
    ##################

    def __initialize(self):
        # We initialize the symbol table
        self.__initialize_st()

        # We initialize constructor (methods 'new' and 'init')
        # of each class
        self.__initialize_constr()

    def __initialize_st(self):
        # First, we add the 'Object' class to the symbol table
        self.__initialize_object()

        # Then, we iterate over each class
        for c in self.__a_ast.classes:

            # We create the dictionary for the fields
            d_fields = {}

            for f in c.fields:
                d_fields[f.name] = f_type

            # We create the dictionary for the class
            d_class = {
                'parent': c.parent,
                'struct': None,
                'struct_vtable': None,
                'new': None,
                'init': None,
                'fields': d_fields,
                'methods': None
            }

            # We add the class to the symbol table
            self.__symbol_table[c.name] = d_class

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
        m_print_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(), t_string.as_pointer()))
        m_print_bool_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(), t_bool))
        m_print_int32_type = ir.FunctionType(struct.as_pointer(), (struct.as_pointer(), t_int32))

        m_input_line_type = ir.FunctionType(t_string.as_pointer(), (struct.as_pointer(),))
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
        init = ir.Function(self.module, init_type, name='Object_init')

        constr_type = ir.FunctionType(struct.as_pointer(), ())
        constr = ir.Function(self.module, constr_type, name='Object_new')

        # We create the dictionary with each method
        d_methods = {
            'print': m_print,
            'printBool': m_print_bool,
            'printInt32': m_print_int32,
            'inputLine': m_input_line,
            'inputBool': m_input_bool,
            'inputInt32': m_input_int32
        }

        # We create the dictionary for the 'Object' element
        d_object = {
            'parent': None,
            'struct': struct,
            'struct_vtable': struct_vtable
            'new': constr
            'init': init
            'fields': {}
            'methods': d_methods
        }

        # We add the 'Object' class to the symbol table
        self.__symbol_table['Object'] = d_object

    def __initialize_constr(self):
        pass

    def __initialize_init(self):
        pass

    def __initialize_new(self):
        pass

    ###########
    # Analyze #
    ###########

    def __analyze(self):
        pass

    def __analyze_fields(self):
        pass

    def __analyze_methods(self):
        pass

    ###################
    # Code generation #
    ###################

    def __codegen(self):
        pass

    def __codegen_If(self):
        pass

    def __codegen_While(self):
        pass

    def __codegen_Let(self):
        pass

    def __codegen_Assign(self):
        pass

    def __codegen_UnOp(self):
        pass

    def __codegen_BinOp(self):
        pass

    def __codegen_Call(self):
        pass

    def __codegen_New(self):
        pass

    def __codegen_Self(self):
        pass

    def __codegen_ObjectIdentifier(self):
        pass

    def __codegen_Literal(self):
        pass

    def __codegen_Unit(self):
        pass

    def __codegen_Block(self):
        pass

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
        llvm_ir = str(self.module)

        # We remove the first two lines
        llvm_ir = llvm_ir.split('\n', 2)[2]

        # We append the LLVM IR code of the 'Object' class
        with open('object/object.ll', 'r') as object_file:
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
        command = 'llc {}'.format(ll_name)
        os.system(command)

        # Compile assembly file to create an executable
        command = 'clang {}.s -o {} -lm'.format(basename, basename)
        os.system(command)
