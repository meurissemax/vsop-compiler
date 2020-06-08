# Compilers

## Context

The goal of this project was to build a compiler for the **VSOP** (*Very Simple Object-oriented Programming*) language (created by C. Soldani, inspired by the [COOL](https://dl.acm.org/doi/abs/10.1145/381841.381847) language). More information is provided in the `vsop_manual.pdf` file.

The compiler takes as input a `.vsop` file and generates as output a corresponding executable file. It also allows to view the output of each step (lexing, parsing, ...) separately. 

This project was realized as part of the *Compilers* course given by Professor **Fontaine** to the master students of Civil Engineering at the [University of Liège](https://www.uliege.be/) during the academic year 2019-2020.

## Language

This VSOP compiler was done using **python** (version `3.7`) with the help, mainly, of the [PLY](https://www.dabeaz.com/ply/) tool (version `3.11`).

Other libraries were also used :

* [argparse](https://docs.python.org/3/library/argparse.html)
* [llvmlite](https://github.com/numba/llvmlite) (working with `llvm` version `8.0.x`)

## How to use the compiler ?

The compiler implementation can be found in the `vsop-compiler/code/` folder.

All the resources of a tool (lexer, parser, ...) are in the folder of the same name.

To install all the necessary tools (assuming python 3 is already installed), just do :

```bash
make install-tools
```

To get a executable version of the compiler, just do :

```bash
make vsopc
```

The compiler can then be used via the command :

```bash
./vsopc <VSOP-SOURCE-FILE>
```

The various options available can be viewed via the command :

```bash
./vsopc -h
```

## Authors

* **Maxime Meurisse** - [meurissemax](https://github.com/meurissemax)
* **Valentin Vermeylen** - [ValentinVermeylen](https://github.com/ValentinVermeylen)
