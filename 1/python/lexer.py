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

from rply import LexerGenerator
from rply.errors import LexingError


###########
# Classes #
###########


class Lexer():
    def __init__(self):
        self.lexer = LexerGenerator()
        self.keywords = ('and', 'bool', 'class', 'do', 'else', 'extends', 'false', 'if', 
            'in', 'int32', 'isnull', 'let', 'new', 'not', 'string', 'then', 'true', 'unit', 'while')
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

    def isKeyword(element):
        return (element in self.keywords)

    def whichOp(element):
        if not element in self.op.keys():
            # Raise exception ? Should not happen
            pass
        return self.op[element]

    def _add_tokens(self):
        
        self.lexer.add('lowercase-letter', r'[a-z]')
        self.lexer.add('uppercase-letter', r'[A-Z]')
        self.lexer.add('letter', r'[a-z]|[A-Z]')
        self.lexer.add('bin-digit', r'0|1')
        self.lexer.add('digit', r'[0-9]')
        self.lexer.add('hex-digit', r'[0-9]|[a-f]|[A-F]')

        self.lexer.add('white-space', r'[ \x09\x0A\x0C\x0D]')
        self.lexer.add('comment', r'\\\\')
        self.lexer.add('comment-left', r'\(\*')
        self.lexer.add('comment-right', r'\*\)') # Call a second lexer when inside a comment.

        self.lexer.add('integer-literal', r'0x([0-9]|[a-f]|[A-F])+|[0-9]+')
        
        self.lexer.add('type-identifier', r'[A-Z](([a-z]|[A-Z])|[0-9]|_)*')

        self.lexer.add('object-identifier', r'[a-z](([a-z]|[A-Z])|[0-9]|_)*')

        regular_char = r'[^\\]|\\[\x0D]'
        escape_sequence = r'[btnr"\\]|x([0-9]|[a-f]|[A-F]){2}|[\x0A][ \x09]' # A vérifier dans des tests.
        escaped_char = r'\\' + r'[' + escape_sequence + r']'
        self.lexer.add('string-literal', r'\"['+ regular_char + r'|' + escaped_char + r']\"')
        
        self.lexer.add('operator', r'[{}():;,\+-\*\\\^\.=<]|<=|<-')


    def get_lexer(self):
        self._add_tokens()

        return self.lexer.build()