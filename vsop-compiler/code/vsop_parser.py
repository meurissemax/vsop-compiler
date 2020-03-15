"""
INFO0085-1 - Compilers
University of Liege
Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""

# Remark / TO-DO for the future :
#   - error handling (clean and meaningful error messages)

#############
# Libraries #
#############

import utils
import ply.yacc as yacc

from vsop_ast import *


###########
# Classes #
###########

class Parser:
    ###############
    # Constructor #
    ###############

    def __init__(self, filename, debug, lexer, tokens, tabmodule):
        # We save the filename (to print error)
        self.__filename = filename

        # We get the file content
        with open(filename, 'r', encoding='ascii') as f:
            data = f.read()

        # We save the file content (to retrieve column of tokens)
        self.__data = data

        # We save the argument values
        self.__debug = debug
        self.__lexer = lexer

        self.tokens = tokens

        # We remove some tokens from the token list
        # (it is not really useful but if we don't do
        # that, the parser will output some warning
        # messages and so disturb the tests on the
        # submission platform)
        self.tokens.remove('IDENTIFIER')
        self.tokens.remove('INLINE_COMMENT')
        self.tokens.remove('LEFT_COMMENT')
        self.tokens.remove('NON_TERMINATED_STRING_LITERAL')
        self.tokens.remove('OPERATOR')
        self.tokens.remove('RIGHT_COMMENT')

        self.__tabmodule = tabmodule

    ####################
    # Precedence rules #
    ####################

    # Tokens are ordered from lowest to highest precedence
    precedence = (
        ('right', 'ASSIGN'),
        ('left', 'AND'),
        ('right', 'NOT'),
        ('nonassoc', 'LOWER', 'LOWER_EQUAL', 'EQUAL'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIV'),
        ('right', 'ISNULL'),
        ('right', 'POW'),
        ('left', 'DOT'),
    )

    #################
    # Grammar rules #
    #################

    # Remark : each rule is written in the docstring of the
    # corresponding function

    def p_program(self, p):
        """
        program : class program
                | class
        """

        self.__ast.add_class(p[1])

    def p_class(self, p):
        """
        class : CLASS TYPE_IDENTIFIER class_body
              | CLASS TYPE_IDENTIFIER EXTENDS TYPE_IDENTIFIER class_body
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # If we are in the 'extends' case
        if len(p) > 4:
            p[0] = Class(lineno, column, p[2], p[4])
            class_body = p[5]

        # If we are not in the 'extends' case
        else:
            p[0] = Class(lineno, column, p[2], 'Object')
            class_body = p[3]

        # If there is a class body
        if class_body is not None:

            # We iterate over each element of the
            # class body
            for e in class_body:

                # We check wether the element is a Field
                # or a method
                type_e = type(e).__name__

                if type_e == 'Field':
                    p[0].add_field(e)
                elif type_e == 'Method':
                    p[0].add_method(e)

    def p_class_body(self, p):
        """
        class_body : LBRACE class_body_aux RBRACE
                   | LBRACE empty RBRACE
        """

        p[0] = p[2]

    def p_class_body_aux(self, p):
        """
        class_body_aux : field class_body_aux
                       | method class_body_aux
                       | field
                       | method
        """

        # We always return a list with all fields and
        # methods of the class body

        # If there is multiple elements
        if len(p) > 2:
            p[0] = [p[1]] + p[2]

        # If there is only one element
        else:
            p[0] = [p[1]]

    def p_field(self, p):
        """
        field : OBJECT_IDENTIFIER COLON type SEMICOLON
              | OBJECT_IDENTIFIER COLON type ASSIGN expr SEMICOLON
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # If we are in the 'assign' case
        if len(p) > 5:
            p[0] = Field(lineno, column, p[1], p[3], p[5])

        # If we are not in the 'assign' case
        else:
            p[0] = Field(lineno, column, p[1], p[3], None)

    def p_method(self, p):
        """
        method : OBJECT_IDENTIFIER LPAR formals RPAR COLON type block
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # Create the method
        p[0] = Method(lineno, column, p[1], p[6], p[7])

        # We check if 'formals' is not empy
        if p[3][0] is not None:

            # We iterate over each formal
            for f in p[3]:
                p[0].add_formal(f)

    def p_type(self, p):
        """
        type : TYPE_IDENTIFIER
             | INT32
             | BOOL
             | STRING
             | UNIT
        """

        p[0] = p[1]

    def p_formals(self, p):
        """
        formals : empty
                | formal
                | formal COMMA formals
        """

        # We always return a list with all formals

        # If there is multiple elements
        if len(p) > 2:
            p[0] = [p[1]] + p[3]

        # If there is only one element
        else:
            p[0] = [p[1]]

    def p_formal(self, p):
        """
        formal : OBJECT_IDENTIFIER COLON type
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # Create the formal
        p[0] = Formal(lineno, column, p[1], p[3])

    def p_block(self, p):
        """
        block : LBRACE expr block_aux RBRACE
        """

        p[0] = Block()

        # We add the required expression to the block
        p[0].add_expr(p[2])

        # We check if there is other expressions
        if p[3] is not None:

            # We iterate over the expression list
            for e in p[3]:

                # If expression is not empty, we add it
                if e is not None:
                    p[0].add_expr(e)

    def p_block_aux(self, p):
        """
        block_aux : SEMICOLON expr block_aux
                  | empty
        """

        # We always return a list with all expressions

        # If there is at least an element
        if len(p) > 2:

            # If there multiple elements
            if p[3] is not None:
                p[0] = [p[2]] + p[3]

            # If there is only one element
            else:
                p[0] = [p[2]]

    def p_expr_if(self, p):
        """
        expr : IF expr THEN expr
             | IF expr THEN expr ELSE expr
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # If we are in the 'else' case
        if len(p) > 5:
            p[0] = If(lineno, column, p[2], p[4], p[6])

        # If we are not in the 'else' case
        else:
            p[0] = If(lineno, column, p[2], p[4], None)

    def p_expr_while(self, p):
        """
        expr : WHILE expr DO expr
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # Create the while
        p[0] = While(lineno, column, p[2], p[4])

    def p_expr_let(self, p):
        """
        expr : LET OBJECT_IDENTIFIER COLON type IN expr
             | LET OBJECT_IDENTIFIER COLON type ASSIGN expr IN expr
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # If we are in the 'assign' case
        if len(p) > 7:
            p[0] = Let(lineno, column, p[2], p[4], p[6], p[8])

        # If we are not in the assign case
        else:
            p[0] = Let(lineno, column, p[2], p[4], None, p[6])

    def p_expr_assign(self, p):
        """
        expr : OBJECT_IDENTIFIER ASSIGN expr
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # Create the assign
        p[0] = Assign(lineno, column, p[1], p[3])

    def p_expr_unop(self, p):
        """
        expr : NOT expr
             | MINUS expr
             | ISNULL expr
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # Create the unop
        p[0] = UnOp(lineno, column, p[1], p[2])

    def p_expr_binop(self, p):
        """
        expr : expr AND expr
             | expr EQUAL expr
             | expr LOWER expr
             | expr LOWER_EQUAL expr
             | expr PLUS expr
             | expr MINUS expr
             | expr TIMES expr
             | expr DIV expr
             | expr POW expr
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # Create the binop
        p[0] = BinOp(lineno, column, p[2], p[1], p[3])

    def p_expr_call(self, p):
        """
        expr : OBJECT_IDENTIFIER LPAR args RPAR
             | expr DOT OBJECT_IDENTIFIER LPAR args RPAR
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # If we are not in the 'self' case
        if len(p) > 5:
            p[0] = Call(lineno, column, p[1], p[3])
            args = p[5]

        # If we are in the 'self' case
        else:
            p[0] = Call(lineno, column, 'self', p[1])
            args = p[3]

        # We check if there is 'args'
        if args[0] is not None:

            # We iterate over each arg
            for e in args:
                p[0].add_expr(e)

    def p_expr_new(self, p):
        """
        expr : NEW TYPE_IDENTIFIER
        """

        # Get position of the element
        lineno = p.lineno(0)
        column = self.__find_column(p.lexpos(0))

        # Create the new
        p[0] = New(lineno, column, p[2])

    def p_expr_obj_id(self, p):
        """
        expr : OBJECT_IDENTIFIER
        """

        p[0] = p[1]

    def p_expr_literal(self, p):
        """
        expr : literal
        """

        p[0] = p[1]

    def p_expr_unit(self, p):
        """
        expr : LPAR RPAR
        """

        p[0] = '()'

    def p_expr_par(self, p):
        """
        expr : LPAR expr RPAR
        """

        p[0] = p[2]

    def p_expr_block(self, p):
        """
        expr : block
        """

        p[0] = p[1]

    def p_args(self, p):
        """
        args : empty
             | expr
             | expr COMMA args
        """

        # We always return a list with all args

        # If there is multiple elements
        if len(p) > 2:
            p[0] = [p[1]] + p[3]

        # If there is only one element
        else:
            p[0] = [p[1]]

    def p_literal(self, p):
        """
        literal : INTEGER_LITERAL
                | STRING_LITERAL
                | boolean_literal
        """

        p[0] = p[1]

    def p_boolean_literal(self, p):
        """
        boolean_literal : TRUE
                        | FALSE
        """

        p[0] = p[1]

    def p_empty(self, p):
        """
        empty :
        """

        pass

    ##################
    # Error handling #
    ##################

    def __print_error(self, lineno, column, message):
        """
        Prints an error on stderr in the right format
        and exits the parser.
        """

        utils.print_error('{}:{}:{}: syntax error: {}'.format(self.__filename, lineno, column, message))

    def p_error(self, p):
        # We get line and column information
        if p is not None:
            lineno = p.lineno
            column = self.__find_column(p.lexpos)
            value = p.value
        else:
            lineno = 0
            column = 0
            value = 'unknown'

        # We print the message
        self.__print_error(lineno, column, 'element "{}"'.format(value))

    ########################
    # Additional functions #
    ########################

    def __find_column(self, lexpos):
        """
        Returns the column of a token in a line
        based on his position relatively to
        the beginning of the file.
        """

        line_start = self.__data.rfind('\n', 0, lexpos) + 1

        return (lexpos - line_start) + 1

    ############################
    # Build and use the parser #
    ############################

    def build(self):
        self.parser = yacc.yacc(module=self, debug=self.__debug, tabmodule=self.__tabmodule)

    def parse(self):
        # We instantiate the abstract syntax tree
        self.__ast = Program()

        # We parse the content of the file
        self.parser.parse(input=self.__data, lexer=self.__lexer)

    def print_ast(self):
        """
        Print the abstract syntax tree in stdout.
        """

        print(self.__ast)
