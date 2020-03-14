"""
INFO0085-1 - Compilers
University of Liege
Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""

#############
# Libraries #
#############

import utils
import ply.yacc as yacc

from tree import *


###########
# Classes #
###########

class Parser:
    ###############
    # Constructor #
    ###############

    def __init__(self, filename, tokens):
        self.filename = filename
        self.tokens = tokens

        self.tokens.remove('IDENTIFIER')
        self.tokens.remove('INLINE_COMMENT')
        self.tokens.remove('LEFT_COMMENT')
        self.tokens.remove('NON_TERMINATED_STRING_LITERAL')
        self.tokens.remove('OPERATOR')
        self.tokens.remove('RIGHT_COMMENT')

        # We get the file content
        with open(filename, 'r', encoding='ascii') as f:
            data = f.read()

        # We save the file content (to retrieve column of tokens)
        self.data = data

    ####################
    # Precedence rules #
    ####################

    precedence = (
        ('right', 'ASSIGN'),
        ('left', 'AND'),
        ('right', 'NOT'),
        ('nonassoc', 'LOWER', 'LOWER_EQUAL', 'EQUAL'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIV'),
        ('right', 'ISNULL'), #UMINUS to add !
        ('right', 'POW'),
        ('left', 'DOT'),
    )

    #################
    # Grammar rules #
    #################

    def p_program(self, p):
        '''
        program : class program
                | class
        '''

        self.ast.add_class(p[1])

    def p_class(self, p):
        '''
        class : CLASS TYPE_IDENTIFIER class_body
              | CLASS TYPE_IDENTIFIER EXTENDS TYPE_IDENTIFIER class_body
        '''

        if len(p) > 4:
            p[0] = Class(p[2], p[4])
            class_body = p[5]
        else:
            p[0] = Class(p[2])
            class_body = p[3]

        if class_body is not None:
            for e in class_body:
                if type(e).__name__ == 'Field':
                    p[0].add_field(e)
                else:
                    p[0].add_method(e)

    def p_class_body(self, p):
        '''
        class_body : LBRACE class_body_aux RBRACE
                   | LBRACE empty RBRACE
        '''

        p[0] = p[2]

    def p_class_body_aux(self, p):
        '''
        class_body_aux : field class_body_aux
                       | method class_body_aux
                       | field
                       | method
        '''

        if len(p) > 2:
            p[0] = [p[1]] + p[2]
        else:
            p[0] = [p[1]]

    def p_field(self, p):
        '''
        field : OBJECT_IDENTIFIER COLON type SEMICOLON
              | OBJECT_IDENTIFIER COLON type ASSIGN expr SEMICOLON
        '''

        if len(p) > 5:
            p[0] = Field(p[1], p[3], p[5])
        else:
            p[0] = Field(p[1], p[3], None)

    def p_method(self, p):
        '''
        method : OBJECT_IDENTIFIER LPAR formals RPAR COLON type block
        '''

        p[0] = Method(p[1], p[6], p[7])

        if p[3][0] is not None:
            for f in p[3]:
                p[0].add_formal(f)

    def p_type(self, p):
        '''
        type : TYPE_IDENTIFIER
             | INT32
             | BOOL
             | STRING
             | UNIT
        '''

        p[0] = p[1]

    def p_formals(self, p):
        '''
        formals : empty
                | formal
                | formal COMMA formals
        '''

        if len(p) > 2:
            p[0] = [p[1]] + p[3]
        else:
            p[0] = [p[1]]

    def p_formal(self, p):
        '''
        formal : OBJECT_IDENTIFIER COLON type
        '''

        p[0] = Formal(p[1], p[3])

    def p_block(self, p):
        '''
        block : LBRACE expr block_aux RBRACE
        '''

        p[0] = Block()

        p[0].add_expr(p[2])

        if p[3] is not None:
            for e in p[3]:
                if e is not None:
                    p[0].add_expr(e)

    def p_block_aux(self, p):
        '''
        block_aux : SEMICOLON expr block_aux
                  | empty
        '''

        if len(p) > 2:
            if p[3] is not None:
                p[0] = [p[2]] + p[3]
            else:
                p[0] = [p[2]]

    def p_expr_if(self, p):
        '''
        expr : IF expr THEN expr
             | IF expr THEN expr ELSE expr
        '''

        if len(p) > 5:
            p[0] = If(p[2], p[4], p[6])
        else:
            p[0] = If(p[2], p[4], None)

    def p_expr_while(self, p):
        '''
        expr : WHILE expr DO expr
        '''

        p[0] = While(p[2], p[4])

    def p_expr_let(self, p):
        '''
        expr : LET OBJECT_IDENTIFIER COLON type IN expr
             | LET OBJECT_IDENTIFIER COLON type ASSIGN expr IN expr
        '''

        if len(p) > 7:
            p[0] = Let(p[2], p[4], p[6], p[8])
        else:
            p[0] = Let(p[2], p[4], None, p[6])

    def p_expr_assign(self, p):
        '''
        expr : OBJECT_IDENTIFIER ASSIGN expr
        '''

        p[0] = Assign(p[1], p[3])

    def p_expr_unop(self, p):
        '''
        expr : NOT expr
             | MINUS expr
             | ISNULL expr
        '''

        p[0] = UnOp(p[1], p[2])

    def p_expr_binop(self, p):
        '''
        expr : expr AND expr
             | expr EQUAL expr
             | expr LOWER expr
             | expr LOWER_EQUAL expr
             | expr PLUS expr
             | expr MINUS expr
             | expr TIMES expr
             | expr DIV expr
             | expr POW expr
        '''

        p[0] = BinOp(p[2], p[1], p[3])

    def p_expr_call(self, p):
        '''
        expr : OBJECT_IDENTIFIER LPAR args RPAR
             | expr DOT OBJECT_IDENTIFIER LPAR args RPAR
        '''

        if len(p) > 5:
            p[0] = Call(p[1], p[3])
            args = p[5]
        else:
            p[0] = Call('self', p[1])
            args = p[3]

        if args[0] is not None:
            for e in args:
                p[0].add_expr(e)

    def p_expr_new(self, p):
        '''
        expr : NEW TYPE_IDENTIFIER
        '''

        p[0] = New(p[2])

    def p_expr_obj_id(self, p):
        '''
        expr : OBJECT_IDENTIFIER
        '''

        p[0] = p[1]

    def p_expr_literal(self, p):
        '''
        expr : literal
        '''

        p[0] = p[1]

    def p_expr_unit(self, p):
        '''
        expr : LPAR RPAR
        '''

        p[0] = '()'

    def p_expr_par(self, p):
        '''
        expr : LPAR expr RPAR
        '''

        p[0] = p[2]

    def p_expr_block(self, p):
        '''
        expr : block
        '''

        p[0] = p[1]

    def p_args(self, p):
        '''
        args : empty 
             | expr
             | expr COMMA args
        '''

        if len(p) > 2:
            p[0] = [p[1]] + p[3]
        else:
            p[0] = [p[1]]

    def p_literal(self, p):
        '''
        literal : INTEGER_LITERAL
                | STRING_LITERAL
                | boolean_literal
        '''

        p[0] = p[1]

    def p_boolean_literal(self, p):
        '''
        boolean_literal : TRUE
                        | FALSE
        '''

        p[0] = p[1]

    def p_error(self, p):
        utils.print_error('{}:1:1: syntax error'.format(self.filename))

    def p_empty(self, p):
        '''
        empty :
        '''

        pass

    ############################
    # Build and use the parser #
    ############################

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, debug=False, tabmodule='vsopparsetab', **kwargs)

    def parse(self, lexer):
        self.ast = Program()

        self.parser.parse(input=self.data, lexer=lexer)

        print(self.ast)
