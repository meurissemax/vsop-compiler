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

from lexer import Lexer


########
# Main #
########

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
