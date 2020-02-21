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
# (we suppose that python3 is already installed)
install-tools:
	sudo apt-get install python-pip
	sudo pip install argparse
	sudo pip install ply
	sudo pip install pyinstaller

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
