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

import re
import sys
import ply.lex as lex


###########
# Classes #
###########

class Lexer:
    ###############
    # Constructor #
    ###############

    def __init__(self, filename):
        # We save the filename (to print error)
        self.filename = filename

        # We get the file content
        with open(filename, 'r', encoding='ascii') as f:
            data = f.read()

        # We save the file content (to retrieve column of tokens)
        self.data = data

        # We define base tokens
        self.base = (
            # Unoffical token names (just to detect comment internally)
            'INLINE_COMMENT',
            'LEFT_COMMENT',
            'RIGHT_COMMENT',

            # Official token names
            'INTEGER_LITERAL',
            'TYPE_IDENTIFIER',
            'OBJECT_IDENTIFIER',
            'STRING_LITERAL',
            'OPERATOR',

            # Special tokens
            'IDENTIFIER',
            'NON_TERMINATED_STRING_LITERAL'
        )

        # We define keywords
        self.keywords = {
            'and': 'AND',
            'bool': 'BOOL',
            'class': 'CLASS',
            'do': 'DO',
            'else': 'ELSE',
            'extends': 'EXTENDS',
            'false': 'FALSE',
            'if': 'IF',
            'in': 'IN',
            'int32': 'INT32',
            'isnull': 'ISNULL',
            'let': 'LET',
            'new': 'NEW',
            'not': 'NOT',
            'string': 'STRING',
            'then': 'THEN',
            'true': 'TRUE',
            'unit': 'UNIT',
            'while': 'WHILE'
        }

        # We define operators
        self.operators = {
            '{': 'LBRACE',
            '}': 'RBRACE',
            '(': 'LPAR',
            ')': 'RPAR',
            ':': 'COLON',
            ';': 'SEMICOLON',
            ',': 'COMMA',
            '+': 'PLUS',
            '-': 'MINUS',
            '*': 'TIMES',
            '/': 'DIV',
            '^': 'POW',
            '.': 'DOT',
            '=': 'EQUAL',
            '<': 'LOWER',
            '<=': 'LOWER_EQUAL',
            '<-': 'ASSIGN',
        }

        # We create the full token list
        self.tokens = list(self.base)
        self.tokens += list(self.keywords.values())
        self.tokens += list(self.operators.values())

        # We set a possible state of the lexer (to handle
        # comment)
        self.states = (('comment', 'exclusive'),)

        # Flag to handle single-line comments
        self.s_comments = False

        # List (used as a stack) to handle multiple-line comments
        self.m_comments = list()

        # Flag to handle the case of a lexing with error(s)
        self.has_error = False

    #######################
    # Comments management #
    #######################

    def is_s_comment(self):
        """
        Returns a boolean indicating if we are
        in a single-line comment or not.
        """

        return self.s_comments

    def is_m_comment(self):
        """
        Returns a boolean indicating if we are
        in a multiple-line comment or not.
        """

        return not (len(self.m_comments) == 0)

    def is_comment(self):
        """
        Returns a boolean indicating if we are
        in a comment.
        """

        return self.is_s_comment() or self.is_m_comment()

    def t_ANY_INLINE_COMMENT(self, t):
        r'\/\/'

        # We only consider the token as an
        # inline comment if we are not
        # already in a comment
        if not self.is_comment():
            self.s_comments = True
            t.lexer.begin('comment')

        pass

    def t_ANY_LEFT_COMMENT(self, t):
        r'\(\*'

        # If we are not already in a single-line
        # comment, we keep track of the opened
        # multiple-line comment
        if not self.is_s_comment():
            self.m_comments.append((t.lineno, self.find_column(t)))
            t.lexer.begin('comment')

        pass

    def t_ANY_RIGHT_COMMENT(self, t):
        r'\*\)'

        # We check if we are not already in a
        # single-line comment
        if not self.is_s_comment():

            # We check if we are in a multiple-line
            # comment
            if not self.is_m_comment():

                # If we are not in a multiple-line comment,
                # this token is an error
                self.print_error(t.lineno, self.find_column(t), 'no corresponding opened comment')

            # If we are in a multiple-line comment,
            # we pop the corresponding opening token
            # (the last one that has matched)
            else:
                self.m_comments.pop()

                # If we are not anymore in a comment (stack
                # m_comments empty), we come back to the
                # initial state of the lexer
                if not self.is_comment():
                    t.lexer.begin('INITIAL')

        pass

    ####################
    # Token definition #
    ####################

    # Tokens are ordered by priority.
    # It means that the first token (and so
    # the first regex) will be tested before the
    # second, etc.

    # Characters to ignore during lexing
    t_ANY_ignore = ' \r\f\t'

    def t_IDENTIFIER(self, t):
        r'[a-z](([a-z]|[A-Z])|[0-9]|_)*'

        # Identifier can be keyword or object identifier,
        # so we have to check
        if t.value in self.keywords:
            t.type = self.keywords[t.value]
        else:
            t.type = 'OBJECT_IDENTIFIER'

        return t

    def t_TYPE_IDENTIFIER(self, t):
        r'[A-Z](([a-z]|[A-Z])|[0-9]|_)*'

        return t

    def t_INTEGER_LITERAL(self, t):
        r'([0-9]|0x)([0-9]|[a-z]|[A-Z])*'

        # We check if the value is a decimal or
        # hexadecimal value in order to make a
        # clean conversion
        if t.value[:2] == '0x':

            # We check if the hexadecimal value
            # is a valid value
            try:
                t.value = int(t.value, 16)

                return t
            except ValueError:
                self.print_error(t.lineno, self.find_column(t), 'invalid hexadecimal integer {}'.format(t.value))
        else:

            # We check if the decimal value
            # is a valid value
            try:
                t.value = int(t.value, 10)

                return t
            except ValueError:
                self.print_error(t.lineno, self.find_column(t), 'invalid decimal integer {}'.format(t.value))

    def t_STRING_LITERAL(self, t):
        r'\"(?:[^\"\\]|\\.|\\\n)*\"'

        # We return the processed string
        return self.string_processing(t)

    def t_NON_TERMINATED_STRING_LITERAL(self, t):
        r'\"(?:[^\"\\]|\\.|\\\n)*'

        # We process the string (to check if there is an error)
        # but we do not return here because we know that if there
        # is no error during processing, there is still an error
        # due to the fact that we are in the case of a non-
        # terminated string
        t = self.string_processing(t)

        # We print the error of the non-terminated string
        self.print_error(t.lineno, self.find_column(t), 'string non terminated before end of file')

    def t_OPERATOR(self, t):
        r'{|}|\(|\)|:|;|,|\+|-|\*|/|\^|\.|<=|<-|<|='

        # Remark : we put '<=' and '<-' before
        # '<' and '=' in the regex to be sure
        # that they match before

        # Since the regex "hardcodes" all the operators,
        # we don't really have to check if the value
        # is effectively in the operators list
        t.type = self.operators[t.value]

        return t

    #######################
    # Newlines management #
    #######################

    def t_ANY_newline(self, t):
        r'[\n]+'

        # The rule to update the number of the line
        # consists of counting the number of '\n' character
        t.lexer.lineno += t.value.count('\n')

        # If we are in a single-line comment, a new
        # line ends the comment and pushes back the
        # lexer to its initial state
        if self.is_s_comment():
            self.s_comments = False
            t.lexer.begin('INITIAL')

    ##################
    # Error handling #
    ##################

    def print_error(self, lineno, column, message):
        """
        Prints an error on stderr in the right format
        and exits the lexer.
        """

        # Update the flag
        self.has_error = True

        # Print the error
        print('{}:{}:{}: lexical error: {}'.format(self.filename, lineno, column, message), file=sys.stderr)

    def t_ANY_error(self, t):
        # If we are in a comment, we don't print errors
        # (the only possible error is due to a non-closed
        # comment and this error is printed in the
        # corresponding function)
        if not self.is_comment():
            self.print_error(t.lineno, self.find_column(t), 'invalid character {}'.format(repr(t.value[0])))

        # Skip the character and go to the next
        t.lexer.skip(1)

    ########################
    # Additional functions #
    ########################

    def find_column(self, t):
        """
        Returns the column of a token in a line
        based on his position relatively to
        the beginning of the file.
        """

        line_start = self.data.rfind('\n', 0, t.lexpos) + 1

        return (t.lexpos - line_start) + 1

    def find_pos_string(self, original, sub):
        """
        Returns the line and the column of a
        substring 'sub' of 'original' relatively
        to the 'original' string.
        """

        # We find the position of 'sub' in 'original'
        original_pos = original.find(sub)

        # We keep the part of the 'original' string up to 'sub'.
        original_sub = original[0:original_pos + len(sub)]

        # We get the line position of 'sub' (by counting
        # the number of '\n' up to 'sub')
        lineno = original_sub.count('\n')

        # We split the substring of 'original' and keep
        # the part where 'sub' is located
        original_split = original_sub.split('\n')
        original_split = original_split[lineno]

        # We get the column of 'sub'
        column = original_split.find(sub)

        return lineno, column

    def string_processing(self, t):
        """
        Processes a string literal according to
        the brief (replace valid newline character,
        escaped character and check unknow character).
        """

        t.lexer.lineno += t.value.count('\n')

        # We save the original value of the string (for
        # error reporting)
        original = t.value

        # We remove valid newlines if any (a newline
        # preceded by \) and after that, we check if there
        # is still a line feed (which could be invalid)
        t.value = re.sub(r'(\\\n([\t\b\r ])*|\\\n)', '', t.value)

        if '\n' in t.value:
            self.print_error(t.lineno, self.find_column(t) + t.value.find('\n'), 'string contains line feed')

        # We check if the treated string contains null character
        if len(t.value.split('\x00')) != 1:
            splits = t.value.split('\x00')
            lineno, column = self.find_pos_string(original, '\x00')

            self.print_error(t.lineno + lineno, column + 1, 'string contains null character')

        # We escape special characters (\b, \t, ect)
        # and we check if there are characters that
        # have to be escaped (character with byte
        # value not in range(32, 127))
        t.value = t.value.replace(r'\"', r'\x22')
        t.value = t.value.replace(r'\\', r'\x5c')

        t.value = t.value.replace(r'\b', r'\x08')
        t.value = t.value.replace(r'\t', r'\x09')
        t.value = t.value.replace(r'\n', r'\x0a')
        t.value = t.value.replace(r'\r', r'\x0d')

        for char in t.value:
            c_byte = ord(char)

            if c_byte not in range(32, 127):
                c_hex = format(c_byte, 'x')

                if len(c_hex) == 1:
                    t.value = t.value.replace(char, '\\x0{}'.format(c_hex))
                else:
                    t.value = t.value.replace(char, '\\x{}'.format(c_hex))

        # Now that all characters are normally escaped,
        # we iterate over each escaped sequences to check
        # if there are invalid escaped sequences, null
        # characters or escaped sequences to replace
        to_replace = list()
        escaped = [m.start() for m in re.finditer(r'\\', t.value)]

        for pos in escaped:
            base = t.value[pos + 1]

            # Hexadecimal escaped sequence
            if base == 'x':
                hex_value = t.value[pos + 2:pos + 4]

                # Null character (invalid)
                if hex_value == '00':
                    lineno, column = self.find_pos_string(original, '\\{}{}'.format(base, hex_value))

                    self.print_error(t.lineno + lineno, column + 1, 'string contains null character')
                    continue

                # We get the byte value of the
                # hexadecimal sequence (if valid)
                try:
                    byte_value = int('0x{}'.format(hex_value), 0)
                except ValueError:
                    lineno, column = self.find_pos_string(original, '\\{}{}'.format(base, hex_value))

                    self.print_error(t.lineno + lineno, column + 1, 'invalid hexadecimal escaped sequence {}'.format(hex_value))
                    continue

                # We check if we have to replace
                # the escaped sequence
                if byte_value in range(32, 127):

                    # Exceptions for \" and \\
                    if hex_value != '22' and hex_value != '5c':
                        to_replace.append(hex_value)

            # Not hexadecimal escaped sequence
            # (necessarily invalid)
            else:
                lineno, column = self.find_pos_string(original, '\\{}'.format(base))

                self.print_error(t.lineno + lineno, column + 1, 'unknow escaped sequence {}'.format(base))
                continue

        # We replace hexadecimal sequences
        # that have to be replaced
        for hex_value in to_replace:
            byte_value = int('0x{}'.format(hex_value), 0)
            char = chr(byte_value)

            t.value = t.value.replace(r'\x{}'.format(hex_value), char)

        return t

    #################
    # Use the lexer #
    #################

    def reset(self):
        # Build the lexer
        self.lexer = lex.lex(module=self, optimize=1, lextab='lextab')

    def lex(self, dump=False):
        # We reset the lexer
        self.reset()

        # We give the data as input to the lexer
        self.lexer.input(self.data)

        # Token classes for which we want to display the value
        type_value = ('INTEGER_LITERAL', 'TYPE_IDENTIFIER', 'OBJECT_IDENTIFIER', 'STRING_LITERAL')

        # We tokenize
        while True:
            # We get the token
            token = self.lexer.token()

            # If there is no more token
            if not token:

                # If a multiple-line comment is not terminated,
                # we print an error
                if self.is_m_comment():
                    (lineno, column) = self.m_comments.pop()
                    self.print_error(lineno, column, 'multi-line comment not closed')

                break

            # Else, we save the token
            elif dump:

                # We get column and type of the token
                t_column = self.find_column(token)
                t_type = token.type.replace('_', '-')

                # We print the token (in the right format)
                if token.type in type_value:
                    print('{},{},{},{}'.format(token.lineno, t_column, t_type.lower(), token.value))
                else:
                    print('{},{},{}'.format(token.lineno, t_column, t_type.lower()))

        # If there was error(s), we exit with an error code
        if self.has_error:
            sys.exit(1)


class LexerExt(Lexer):
    ###############
    # Constructor #
    ###############

    def __init__(self, filename):
        # We call the constructor of the parent class
        super().__init__(filename)

        # We define new operators
        self.newop = {'>': 'GREATER', '>=': 'GREATER_EQUAL'}
        self.operators.update(self.newop)

        # We define new keywords
        self.newkey = {'or' : 'OR'}
        self.keywords.update(self.newkey)

        # We list all the new elements
        self.new = {}
        self.new.update(self.newop)
        self.new.update(self.newkey)

        # We add the new elements to the token list
        self.tokens += list(self.new.values())

    ####################
    # Token definition #
    ####################

    # Overriden methods

    def t_OPERATOR(self, t):
        r'{|}|\(|\)|:|;|,|\+|-|\*|/|\^|\.|<=|>=|<-|<|>|='

        t.type = self.operators[t.value]

        return t

    #################
    # Use the lexer #
    #################

    # Overriden methods

    def reset(self):
        # Build the lexer
        self.lexer = lex.lex(module=self, optimize=1, lextab='lextabext')
