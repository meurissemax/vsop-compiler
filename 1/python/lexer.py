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

    def __init__(self, filename):
        # We save the filename (to print error)
        self.__filename = filename

        # We get the file content
        with open(filename, 'r', encoding='ascii') as f:
            data = f.read()

        # We save the file content (to retrieve column of tokens)
        self.__data = data

        # We define base tokens
        self.__base = (
            # Unoffical token names (just to detect comment internally)
            'inline_comment',
            'left_comment',
            'right_comment',

            # Official token names
            'integer_literal',
            'type_identifier',
            'object_identifier',
            'string_literal',
            'operator',

            # Special token for keywords and type identifiers
            'identifier'
        )

        # We define keywords
        self.__keywords = (
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

        # We define operators
        self.__operators = {
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
            '<': 'lower',
            '<=': 'lower_equal',
            '<-': 'assign',
        }

        # We create the full token list
        self.tokens = list(self.__base)
        self.tokens += list(self.__keywords)
        self.tokens += list(self.__operators.values())

        # Flag to handle single-line comments
        self.__s_comments = False

        # List (used as a stack) to handle multiple-line comments
        self.__m_comments = list()

    #######################
    # Comments management #
    #######################

    def __is_s_comment(self):
        """
        Returns a boolean indicating if we are
        in a single-line comment or not.
        """

        return self.__s_comments

    def __is_m_comment(self):
        """
        Returns a boolean indicating if we are
        in a multiple-line comment or not.
        """

        return not (len(self.__m_comments) == 0)

    def __is_comment(self):
        """
        Returns a boolean indicating if we are
        in a comment.
        """

        return self.__is_s_comment() or self.__is_m_comment()

    def t_inline_comment(self, t):
        r'\/\/'

        # We only consider the token as an
        # inline comment if we are not
        # already in a comment
        if not self.__is_comment():
            self.__s_comments = True

        pass

    def t_left_comment(self, t):
        r'\(\*'

        # If we are not already in a single-line
        # comment, we keep track of the opened
        # multiple-line comment
        if not self.__is_s_comment():
            self.__m_comments.append((t.lineno, self.__find_column(t)))

        pass

    def t_right_comment(self, t):
        r'\*\)'

        # We check if we are not already in a
        # single-line comment
        if not self.__is_s_comment():

            # We check if we are in a multiple-line
            # comment
            if not self.__is_m_comment():

                # If we are not in a multiple-line comment,
                # this token is an error
                self.__print_error(t.lineno, self.__find_column(t), 'no corresponding opened comment')

                # Skip the character and go to the next
                t.lexer.skip(1)

            # If we are in a multiple-line comment,
            # we pop the corresponding opening token
            # (the last one that has matched)
            else:
                self.__m_comments.pop()

        pass

    ###################
    # Token defintion #
    ###################

    # Token are ordered by priority.
    # It means that the first token (and so
    # the first regex) will be test before the
    # second, etc.

    # Characters to ignore during lexing
    t_ignore = '[ \r\f\t]'

    def t_identifier(self, t):
        r'[a-z](([a-z]|[A-Z])|[0-9]|_)*'

        # If we are in a comment, we do not return
        # the token, we just keep executing
        if self.__is_comment():
            return

        # Identifer can be keyword or object identifier,
        # so we have to check
        if t.value in self.__keywords:
            t.type = t.value
        else:
            t.type = 'object_identifier'

        return t

    def t_type_identifier(self, t):
        r'[A-Z](([a-z]|[A-Z])|[0-9]|_)*'

        # If we are in a comment, we do not return
        # the token, we just keep executing
        if self.__is_comment():
            return

        return t

    def t_integer_literal(self, t):
        r'([0-9]|0x)([0-9]|[a-z]|[A-Z])*'

        # If we are in a comment, we do not return
        # the token, we just keep executing
        if self.__is_comment():
            return

        # We check if the value is an decimal or
        # hexadecimal value in order to make a
        # clean conversion
        if t.value[:2] == '0x':

            # We check if the hexadecimal value
            # is a valid value
            try:
                t.value = int(t.value, 16)

                return t
            except ValueError:
                self.__print_error(t.lineno, self.__find_column(t), 'invalid hexadecimal integer {}'.format(t.value))
                t.lexer.skip(1)
        else:

            # We check if the decimal value
            # is a valid value
            try:
                t.value = int(t.value, 10)

                return t
            except ValueError:
                self.__print_error(t.lineno, self.__find_column(t), 'invalid decimal integer {}'.format(t.value))
                t.lexer.skip(1)

    def t_string_literal(self, t):
        r'\"(?!\\\")(.|\n)*\"'

        # If we are in a comment, we do not return
        # the token, we just keep executing
        if self.__is_comment():
            return

        t.lexer.lineno += t.value.count('\n')

        # We escape special characters
        t.value = re.sub(r'(\s\s|\s\\\s|\n)*', '', t.value)

        t.value = t.value.replace(r'\b', r'\x08')
        t.value = t.value.replace(r'\t', r'\x09')
        t.value = t.value.replace(r'\n', r'\x0a')
        t.value = t.value.replace(r'\r', r'\x0d')

        t.value = t.value.replace(r'\"', r'\x22')
        t.value = t.value.replace(r'\\', r'\x5c')

        return t

    def t_operator(self, t):
        r'{|}|\(|\)|:|;|,|\+|-|\*|/|\^|\.|<=|<-|<|='

        # Remark : we put '<=' and '<-' before
        # '<' and '=' in the regex to be sure
        # that they match before

        # If we are in a comment, we do not return
        # the token, we just keep executing
        if self.__is_comment():
            return

        # Since the regex "hardcode" all the operators,
        # we don't really have to check if the value
        # is effectively in the operators list
        t.type = self.__operators[t.value]

        return t

    #######################
    # Newlines management #
    #######################

    def t_newline(self, t):
        r'[\n]+'

        # The rule to update the number of the line
        # consists of counting the number of '\n' character
        t.lexer.lineno += t.value.count('\n')

        # If we are in a single-line comment, a new
        # line ends the comment
        if self.__is_s_comment():
            self.__s_comments = False

    ##################
    # Error handling #
    ##################

    def __print_error(self, lineno, column, message):
        """
        Print an error on stderr and changes the
        status of the lexer.
        """

        utils.print_error('{}:{}:{}: lexical error: {}'.format(self.__filename, lineno, column, message))

    def t_error(self, t):
        # If we are in a comment, we don't print errors
        # (because we will have a lot of error since
        # token are not recognised in comment)
        if not self.__is_comment():
            self.__print_error(t.lineno, self.__find_column(t), 'invalid character {}'.format(repr(t.value[0])))

        # Skip the character and go to the next
        t.lexer.skip(1)

    ########################
    # Additional functions #
    ########################

    def __find_column(self, t):
        """
        Returns the column of a token in a line
        based on his position relatively to
        the beginning of the file.
        """

        line_start = self.__data.rfind('\n', 0, t.lexpos) + 1

        return (t.lexpos - line_start) + 1

    ###########################
    # Build and use the lexer #
    ###########################

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def lex(self):
        # Give the data as input to the lexer
        self.lexer.input(self.__data)

        # Token classes for which we want to display the value
        type_value = ('integer_literal', 'type_identifier', 'object_identifier', 'string_literal')

        # Tokenize
        while True:
            token = self.lexer.token()

            # If there is no more token
            if not token:

                # If a multiple-line comment is not terminated,
                # we print an error
                if self.__is_m_comment():
                    (lineno, column) = self.__m_comments.pop()
                    self.__print_error(lineno, column, 'multi-line comment not closed')

                break

            # Get column and type of the token
            t_column = self.__find_column(token)
            t_type = token.type.replace('_', '-')

            # Print the token (in the right format)
            if token.type in type_value:
                print('{},{},{},{}'.format(token.lineno, t_column, t_type, token.value))
            else:
                print('{},{},{}'.format(token.lineno, t_column, t_type))
