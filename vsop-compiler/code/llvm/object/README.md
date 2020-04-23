# How to use the provided runtime?

The provided runtime contains the code for the `Object` class, using the
C++-like dynamic dispatch presented in the lecture.

To use it, you have 3 options:

1. Append Object's LLVM IR to your generated LLVM IR.
2. Compile the C or LLVM file at the same time as your LLVM IR.
3. Build a library from the C file, and link it with your LLVM code to form a
   native executable.

In all 3 options, you should not generate any code for `Object` yourself, as it
would clash with the provided code.

However, note that the use of this runtime is not mandatory. You can implement
the `Object` class yourself if you want (especially if you implement the FFI
extension).

## Appending LLVM IR

When generating the LLVM IR for the given VSOP program, prepend or append the
contents of `object.ll` to your generated LLVM IR.

You can keep the LLVM IR for `Object` as a string in your implementation
language. Alternatively, you could place `object.ll` somewhere your compiler
can reach, and load its contents when running your compiler.

## Compiling the runtime with the application

Let's say you compile a file `my_app.vsop`. You could place all the LLVM IR
minus the `Object` class into a `my_app.ll` file. Then, to build the native
executable, you could call `clang` with both your `my_app.ll` file and the C or
LLVM file for the `Object` class (which should be at some place your compiler
can reach). E.g., the call could look like

    clang -o my_app /tmp/vsopc.67xYgu/my_app.ll /usr/local/share/vsopc/object.c

## Building a library

This is a variation of the previous option. Rather than recompile the C (or
LLVM) runtime each time you compile a program, you can pre-compile it and just
link the corresponding object file or library. In general, you would use a
dynamic (`.so`) or static (`.a`) library. However, since our runtime is really
small and fits in a single file, the simpler thing to do here is to use the
object file directly, e.g.

    clang -o my_app /tmp/vsopc.67xYgu/my_app.ll /usr/local/share/vsopc/object.o
