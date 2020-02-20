"""
INFO0085-1 - Compilers
Project 1 : Lexical analysis
University of Liege - Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""

#############
# Libraries #
#############

import utils
import ply.lex as lex


####################
# Global variables #
####################

base = (
    'inline_comment',
    'left_comment',
    'right_comment',
    'integer_literal',
    'keyword',
    'type_identifier',
    'object_identifier',
    'string_literal',
    'operator'
)

keywords = (
    'and',
    'bool',
    'class',
    'do',
    'else',
    'extends',
    'false',
    'if',
    'in',
    'int32',
    'isnull',
    'let',
    'new',
    'not',
    'string',
    'then',
    'true',
    'unit',
    'while'
)

operators = {
    '<=': 'lower_equal',
    '<-': 'assign',
    '{': 'lbrace',
    '}': 'rbrace',
    '(': 'lpar',
    ')': 'rpar',
    ':': 'colon',
    ';': 'semicolon',
    ',': 'comma',
    '+': 'plus',
    '-': 'minus',
    '*': 'times',
    '/': 'div',
    '^': 'pow',
    '.': 'dot',
    '=': 'equal',
    '<': 'lower'
}

tokens = list(base) + list(keywords) + list(operators.values())


#############
# Functions #
#############

def Lexer(filename):
    ###############
    # Token regex #
    ###############

    t_inline_comment = r'\/\/'
    t_left_comment = r'\(\*'
    t_right_comment = r'\*\)'
    t_type_identifier = r'[A-Z](([a-z]|[A-Z])|[0-9]|_)*'
    t_object_identifier = r'[a-z](([a-z]|[A-Z])|[0-9]|_)*'

    t_ignore = '[ \r\f\t]'

    ##############################
    # Token with special actions #
    ##############################

    def t_string_literal(t): 
        r'\"[^\"]*\"' # Faire le bon truc
        t.lexer.lineno += t.value.count('\n') #vérifier que ça fait ce qu'on veut, normalement oui.
        return t

    def t_integer_literal(t):
        r'0x([0-9]|[a-f]|[A-F])+|[0-9]+'
        t.value = int(t.value, 0)

        return t

    def t_keyword(t):
        r'[a-z2-3]{2,}'

        if t.value in keywords:
            t.type = t.value

        return t

    def t_operator(t):
        r'{|}|\(|\)|:|;|,|\+|-|\*|/|\^|\.|<=|<-|<|='

        if t.value in operators:
            t.type = operators[t.value]

        return t

    def t_newline(t):
        r'[\n]+'
        t.lexer.lineno += t.value.count('\n')

    ##################
    # Error handling #
    ##################

    def t_error(t):
        utils.print_error('{}:{}:{}: lexical error for character {}'.format(filename, t.lineno, t.lexpos, repr(t.value[0])))
        t.lexer.skip(1)

    # Build the lexer from my environment and return it    
    return lex.lex()


def find_column(input, token):
     line_start = input.rfind('\n', 0, token.lexpos) + 1
     return (token.lexpos - line_start) + 1