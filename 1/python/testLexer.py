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

# Tuple of tokens.
toks = (
            'integer_literal',
            'type_identifier',
            'object_identifier',
            'string_literal',
            'operator',
            'comment',
            'comment_left',
            'comment_right',
            'keyword')

def ownLexer():

    # Simple regex
    regular_char = r'[^\\]|\\[\x0D]'
    escape_sequence = r'[btnr"\\]|x([0-9]|[a-f]|[A-F]){2}|[\x0A][ \x09]' # A vérifier dans des tests.
    escaped_char = r'\\' + r'[' + escape_sequence + r']'

    t_type_identifier = r'[A-Z](([a-z]|[A-Z])|[0-9]|_)*'
    t_object_identifier = r'[a-z](([a-z]|[A-Z])|[0-9]|_)*'
    t_string_literal = r'\"['+ regular_char + r'|' + escaped_char + r']\"'
    t_operator = r'[{}():;,]|\+|-|\*|\\|\^|\.|=|<|<=|<-'
    t_comment = r'\\\\'
    t_comment_left = r'\(\*'
    t_comment_right = r'\*\)'

    t_ignore = ' \x09\x0A\x0C\x0D'

    def t_integer_literal(t):
        r'0x([0-9]|[a-f]|[A-F])+|[0-9]+'
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

    tokens = list(toks) + list(reserved.values())

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
        r'[\0x0D]+'
        t.lexer.lineno += len(t.value)

    # Error handling rule
    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    return lex.lex()