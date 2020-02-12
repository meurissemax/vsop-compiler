from rply import LexerGenerator
from rply.errors import LexingError


class Lexer():
    def __init__(self):
        self.lexer = LexerGenerator()

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
        #self.lexer.add('keyword', ) Le faire ou garder une table et checker que c'est un keyword quand on appelle le lexer dans la boucle?
        
        self.lexer.add('type-identifier', r'[A-Z](([a-z]|[A-Z])|[0-9]|_)*')

        self.lexer.add('object-identifier', r'[a-z](([a-z]|[A-Z])|[0-9]|_)*')

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
