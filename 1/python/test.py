from rply import LexerGenerator
from rply.errors import LexingError


class Lexer():
    def __init__(self):
        self.lexer = LexerGenerator()

    def _add_tokens(self):
        # Print
        self.lexer.add('PRINT', r'print')

        # Parenthesis
        self.lexer.add('OPEN_PAREN', r'\(')
        self.lexer.add('CLOSE_PAREN', r'\)')

        # Semi Colon
        self.lexer.add('SEMI_COLON', r'\;')

        # Operators
        self.lexer.add('SUM', r'\+')
        self.lexer.add('SUB', r'\-')

        # Number
        self.lexer.add('NUMBER', r'\d+')

        # Ignore spaces
        self.lexer.ignore(r'\s+')

    def get_lexer(self):
        self._add_tokens()

        return self.lexer.build()

if __name__ == '__main__':
    filename = 'test.vsop'

    # Get the lexer
    lexer = Lexer().get_lexer()

    # Read input file, line by line (to save the information about line position)
    with open('../tests/test.vsop', mode='r', encoding='ascii') as content_file:
        lines = content_file.readlines()

    # Iterate on each line (i is the line number)
    for i, line in enumerate(lines):
        # Get all tokens of the line
        tokens = lexer.lex(line)

        # Iterate on each token to print them or detect an error
        try:
            for token in tokens:
                # To get the column number
                pos = token.getsourcepos()

                # Print the token
                print(str(i + 1) + ',' + str(pos.idx) + ',' + str(token.gettokentype()))
        except LexingError as err:
            # To get the column number
            pos = err.getsourcepos()

            # Print the error
            print(filename + ':' + str(i + 1) + ':' + str(pos.idx) + ': lexical error:')
