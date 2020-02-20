"""
INFO0085-1 - Compilers
Project 1 : Lexical analysis
University of Liege - Academic year 2019-2020

Authors :
    - Maxime Meurisse
    - Valentin Vermeylen
"""

#########
# TO DO #
#########

# Gérer les commentaires
# Vérifier que les string-literal sont OK


#############
# Libraries #
#############

import utils
import ply.lex as lex


###########
# Classes #
###########

class Lexer():
    ###############
    # Constructor #
    ###############

    def __init__(self, filename):
        self.filename = filename

        self.base = (
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

        self.keywords = (
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

        self.operators = {
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

        self.tokens = list(self.base)
        self.tokens += list(self.keywords)
        self.tokens += list(self.operators.values())

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

    def t_string_literal(self, t):
        r'\"[^\"]*\"'
        t.lexer.lineno += t.value.count('\n')

        return t

    def t_integer_literal(self, t):
        r'0x([0-9]|[a-f]|[A-F])+|[0-9]+'
        t.value = int(t.value, 0)

        return t

    def t_keyword(self, t):
        r'[a-z2-3]{2,}'

        if t.value in self.keywords:
            t.type = t.value

        return t

    def t_operator(self, t):
        r'{|}|\(|\)|:|;|,|\+|-|\*|/|\^|\.|<=|<-|<|='

        if t.value in self.operators:
            t.type = self.operators[t.value]

        return t

    def t_newline(self, t):
        r'[\n]+'
        t.lexer.lineno += t.value.count('\n')

    ##################
    # Error handling #
    ##################

    def t_error(self, t):
        utils.print_error(
            '{}:{}:{}: lexical error for character {}'.format(
                self.filename,
                t.lineno,
                t.lexpos,
                repr(t.value[0])
                )
            )

        t.lexer.skip(1)

    ###########################
    # Build and use the lexer #
    ###########################

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def lex(self, data):
        self.lexer.input(data)

        type_value = (
            'integer_literal',
            'type_identifier',
            'object_identifier',
            'string_literal'
            )

        for token in self.lexer:
            if token.type in type_value:
                print(
                    '{},{},{},{}'.format(
                        token.lineno,
                        find_column(data, token),
                        token.type.replace('_', '-'),
                        token.value
                        )
                    )
            else:
                print(
                    '{},{},{}'.format(
                        token.lineno,
                        find_column(data, token),
                        token.type.replace('_', '-')
                        )
                    )


def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1

    return (token.lexpos - line_start) + 1
