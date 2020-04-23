#ifndef OBJECT_H_
#define OBJECT_H_

#include <stdbool.h>
#include <stdint.h>

// Forward declarations for mutually recursive types
typedef struct Object Object;
typedef struct ObjectVTable ObjectVTable;

// Type for Object class. Object has no field per se, just the pointer to its
// virtual function table (vtable).
struct Object {
    // Underscore prevents clash with user-defined field, as VSOP identifiers
    // cannot start with underscore
    const ObjectVTable *_vtable;
};

// Type for Object's vtable. Contains one function pointer per method.
struct ObjectVTable {
    // Prints the given string on stdout.
    Object *(*print)(Object *self, const char *s);
    // Prints the given boolean on stdout.
    Object *(*printBool)(Object *self, bool b);
    // Prints the given integer on stdout (in decimal).
    Object *(*printInt32)(Object *self, int32_t i);
    // Reads a line of input into a string, with the end-of-line removed.
    // If no input can be read, returns the empty string "".
    char *(*inputLine)(Object *self);
    // Reads a boolean ("true" or "false") from stdin. Skips leading white
    // spaces. In case of error, prints an error message and exits the program.
    bool (*inputBool)(Object *self);
    // Reads a VSOP integer literal (with optional +/- sign) from stdin. Skips
    // leading white spaces. In case of error, prints an error message and
    // exits the program.
    int32_t (*inputInt32)(Object *self);
};

// We also declare Object's methods directly to allow for static dispatch
Object *Object_print(Object *self, const char *s);
Object *Object_printBool(Object *self, bool b);
Object *Object_printInt32(Object *self, int32_t i);
char *Object_inputLine(Object *self);
bool Object_inputBool(Object *self);
int32_t Object_inputInt32(Object *self);


// Object's constructor. Allocates and initialize a new Object.
Object *Object_new(void);

// Object's initializer. Initializes an allocated Object.
Object *Object_init(Object *self);

// Object's vtable instance, shared by all Object instances.
extern const ObjectVTable Object_vtable;

#endif // OBJECT_H_
