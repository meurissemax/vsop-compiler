# INFO0085-1 - Compilers
# University of Liege
# Academic year 2019-2020

# Authors :
#    - Maxime Meurisse
#    - Valentin Vermeylen

# Clean the workspace
clean-workspace:
	rm -f -r __pycache__/
	rm -f -r build/
	rm -f parser.out
	rm -f vsop_parsetab.py

# Remove the executable
clean-exec:
	rm -f vsopc

# Install any software needed to build the compiler
# (we suppose that python3 is already installed)
install-tools:
	sudo apt-get install --yes python3-pip
	sudo apt-get install --yes python-setuptools
	yes | sudo pip3 install argparse
	yes | sudo pip3 install ply
	yes | sudo pip3 install pyinstaller

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
