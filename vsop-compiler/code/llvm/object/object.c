#include "object.h"

#include <ctype.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Utility functions ----------------------------------------------------------

// Read characters from stdin until EOF is reached, or the given predicate
// returns true. The character for which the predicate returns true is not
// included in the resulting string, and is put back on stdin.
static char *read_until(int (*predicate)(int)) {
    size_t n = 1024;
    char *buf = malloc(n);
    size_t i = 0;
    while (buf) {
        int c = getc(stdin);
        if (c == EOF || predicate((char) c)) {
            if (c != EOF)
                ungetc(c, stdin);
            buf[i] = '\0';
            return buf;
        }
        buf[i] = (char) c;
        if (i == n - 1) {
            n *= 2;
            buf = realloc(buf, n);
        }
        ++i;
    }
    // If we reach this line, realloc failed an we are out-of-memory
    return NULL;
}

// Removes characters from stdin as long as they match the given predicate.
static void skip_while(int (*predicate)(int)) {
    int c = getc(stdin);
    while (c != EOF && predicate(c))
        c = getc(stdin);
    if (c != EOF)
        ungetc(c, stdin);
}

static int is_eol(int c) {
    return c == '\n';
}

// Methods --------------------------------------------------------------------

Object *Object_print(Object *self, const char *s) {
    printf("%s", s); // Note that printf(s) would allow format-string attacks
    return self;
}

Object *Object_printBool(Object *self, bool b) {
    printf("%s", b ? "true" : "false");
    return self;
}

Object *Object_printInt32(Object *self, int32_t i) {
    printf("%" PRId32, i); // PRId32 is the printf sequence for int32_t
    return self;
}

char *Object_inputLine(Object *self __attribute__((unused))) {
    char *line = read_until(is_eol);
    if (!line)
        line = "";
    return line;
}

bool Object_inputBool(Object *self __attribute__((unused))) {
    skip_while(isspace);
    char *word = read_until(isspace);
    if (!word) {
        fprintf(stderr, "Object::inputBool: cannot read word!\n");
        exit(EXIT_FAILURE);
    }

    size_t len = strlen(word);
    if (len == 4 && strncmp(word, "true", 4) == 0) {
        free(word);
        return true;
    } else if (len == 5 && strncmp(word, "false", 5) == 0) {
        free(word);
        return false;
    } else {
        fprintf(stderr, "Object::inputBool: `%s` is not a valid boolean!\n",
                word);
        free(word);
        exit(EXIT_FAILURE);
    }
}

int32_t Object_inputInt32(Object *self __attribute__((unused))) {
    skip_while(isspace);
    char *word = read_until(isspace);
    if (!word) {
        fprintf(stderr, "Object::inputInt32: cannot read word!\n");
        exit(EXIT_FAILURE);
    }

    char *p;
    long long int i;
    size_t len = strlen(word);
    // We can't use strtoll base detection since it also allows octal, contrary
    // to VSOP
    bool is_hex =
        (len > 2 && word[0] == '0' && word[1] == 'x')
        || (len > 3 && (word[0] == '+' || word[0] == '-') && word[1] == '0'
                && word[2] == 'x');
    if (is_hex) {
        i = strtoll(word, &p, 16);
    } else {
        i = strtoll(word, &p, 10);
    }

    if (*p != '\0') {
        fprintf(stderr,
                "Object::inputInt32: `%s` is not a valid integer literal!\n",
                word);
        exit(EXIT_FAILURE);
    }

    if (i < INT32_MIN || i > INT32_MAX) {
        fprintf(stderr,
                "Object::inputInt32: `%s` does not fit a 32-bit integer!\n",
                word);
        exit(EXIT_FAILURE);
    }

    return (int32_t) i;
}

// Constructor ----------------------------------------------------------------

Object *Object_new(void) {
    Object *ret = malloc(sizeof (Object));
    return Object_init(ret);
}

Object *Object_init(Object *self) {
    if (self)
        self->_vtable = &Object_vtable;
    return self;
}

// Virtual function table instance --------------------------------------------

const ObjectVTable Object_vtable = {
    .print = &Object_print,
    .printBool = &Object_printBool,
    .printInt32 = &Object_printInt32,
    .inputLine = &Object_inputLine,
    .inputBool = &Object_inputBool,
    .inputInt32 = &Object_inputInt32
};
