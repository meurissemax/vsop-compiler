# INFO0085-1 - Compilers
# Project 1 : Lexical analysis
# University of Liege - Academic year 2019-2020

# Authors :
#    - Maxime Meurisse
#    - Valentin Vermeylen

# Clean the workspace
clean-workspace:
	rm -f -r __pycache__/
	rm -f -r build/

# Remove the executable
clean-exec:
	rm -f -r vsopc

# Install any software needed to build the compiler
install-tools:

# Build the compiler
vsopc:
	pyinstaller \
		--onefile main.py \
		--distpath ./ \
		--clean \
		--onefile \
		--name vsopc \
		--specpath ./build \
		--workpath ./build \

# Make test
test:
	./vsopc -lex ../tests/personal/brief.vsop
