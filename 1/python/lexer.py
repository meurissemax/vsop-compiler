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

import ply.lex as lex


###########
# Classes #
###########


class Lexer:
    tokens = (
            'bin_digit',
            'digit',
            'hex_digit',
            'integer_literal',
            'type_identifier',
            'object_identifier',
            'string_literal',
            'operator',
            'comment',
            'comment_left',
            'comment_right',
            'keyword')

    regular_char = r'[^\\]|\\[\x0D]'
    escape_sequence = r'[btnr"\\]|x([0-9]|[a-f]|[A-F]){2}|[\x0A][ \x09]' # A vérifier dans des tests.
    escaped_char = r'\\' + r'[' + escape_sequence + r']'

    t_integer_literal = r'0x([0-9]|[a-f]|[A-F])+|[0-9]+'
    t_type_identifier = r'[A-Z](([a-z]|[A-Z])|[0-9]|_)*'
    t_object_identifier = r'[a-z](([a-z]|[A-Z])|[0-9]|_)*'
    t_string_literal = r'\"['+ regular_char + r'|' + escaped_char + r']\"'
    t_operator = r'[{}():;,]|\+|-|\*|\\|\^|\.|=|<|<=|<-'
    t_comment = r'\\\\'
    t_comment_left = r'\(\*'
    t_comment_right = r'\*\)'

    t_ignore = ' \x09\x0A\x0C\x0D'

    def t_bin_digit(t):
        r'0|1'
        t.value = int(t.value)
        return t

    def t_digit(t):
        r'[0-9]'
        t.value = int(t.value)
        return t

    def t_hex_digit(t):
        r'[0-9]|[a-f]|[A-F]'
        t.value = int(t.value)
        return t

    reserved = {
    'and' : 'and',
    'bool' : 'bool',
    'class' : 'class',
    'do' : 'do',
    'else' : 'else',
    'extends' : 'extends',
    'false' : 'false',
    'if' : 'if',
    'in' : 'in',
    'int32' : 'int32',
    'isnull' : 'isnull',
    'let' : 'let',
    'new' : 'new',
    'not' : 'not',
    'string' : 'string',
    'then' : 'then',
    'true' : 'true',
    'unit' : 'unit',
    'while' : 'while'
    }

    tokens = list(tokens) + list(reserved.values())

    def t_keyword(t):
        r'[a-z](([a-z]|[A-Z])|[0-9]|_)*' # Même que pour object identifier. Faire une bête table ?
        t.type = reserved.get(t.value, 'keyword')
        return t

    # Compute column.
    #     input is the input text string
    #     token is a token instance
    def find_column(self, input, token):
        line_start = input.rfind('\n', 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1


    # Define a rule so we can track line numbers
    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Error handling rule
    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

     # EOF handling rule ??

    def __init__(self):

        self.op = {
                    r'{' : 'lbrace',
                    r'}' : 'rbrace',
                    r'(' : 'lpar',
                    r')' : 'rpar',
                    r':' : 'colon',
                    r';' : 'semicolon',
                    r',' : 'comma',
                    r'\+' : 'plus',
                    r'-' : 'minus',
                    r'\*' : 'times',
                    r'/' : 'div',
                    r'\^' : 'pow',
                    r'\.' : 'dot',
                    r'=' : 'equal',
                    r'<' : 'lower',
                    r'<=' : 'lower-equal',
                    r'<-' : 'assign'
                    }

    def isKeyword(self, element):
        return (element in self.keywords)

    def whichOp(self, element):
        if not element in self.op.keys():
            # Raise exception ? Should not happen
            pass
        return self.op[element]

    # Build the lexer
    def build(self,**kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def input(self, line):
        self.lexer.input(line)

    def token(self):
        return self.lexer.token()