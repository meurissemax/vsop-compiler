# INFO0085-1 - Compilers
# University of Liege
# Academic year 2019-2020

# Authors :
#    - Maxime Meurisse
#    - Valentin Vermeylen

# Build the compiler
vsopc: *.py
	cp main.py vsopc
	chmod +x vsopc

# Install any software needed to build the compiler
# (we suppose that python3 is already installed)
install-tools:
	sudo apt-get install --yes python3-pip
	sudo apt-get install --yes python-setuptools
	yes | sudo pip3 install argparse
	yes | sudo pip3 install ply
	yes | sudo pip3 install llvmlite

# Phony
.PHONY: clean-workspace clean-exec clean

# Clean the workspace
clean-workspace:
	@rm -f -r __pycache__/
	@rm -f -r **/__pycache__/
	@rm -f *.pyc
	@rm -f **/parser.out

# Clean the executable
clean-exec:
	@rm -f vsopc

# Clean everything
clean:
	@make clean-workspace
	@make clean-exec
