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

import re
import utils
import ply.lex as lex


###########
# Classes #
###########

class Lexer():
    ###############
    # Constructor #
    ###############

    def __init__(self, filename, data):
        self.filename = filename
        self.data = data

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

        t.value = re.sub(r'(\s\s|\s\\\s|\n)*', '', t.value)

        t.value = t.value.replace(r'\b', r'\x08')
        t.value = t.value.replace(r'\t', r'\x09')
        t.value = t.value.replace(r'\n', r'\x0a')
        t.value = t.value.replace(r'\r', r'\x0d')

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

    ########################
    # Additional functions #
    ########################

    def find_column(self, t):
        line_start = self.data.rfind('\n', 0, t.lexpos) + 1

        return (t.lexpos - line_start) + 1

    ###########################
    # Build and use the lexer #
    ###########################

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def lex(self):
        self.lexer.input(self.data)

        type_value = (
            'integer_literal',
            'type_identifier',
            'object_identifier',
            'string_literal'
            )

        for token in self.lexer:
            t_column = self.find_column(token)
            t_type = token.type.replace('_', '-')

            if token.type in type_value:
                print(
                    '{},{},{},{}'.format(
                        token.lineno,
                        t_column,
                        t_type,
                        token.value
                        )
                    )
            else:
                print(
                    '{},{},{}'.format(
                        token.lineno,
                        t_column,
                        t_type
                        )
                    )
