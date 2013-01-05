PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
HOSTPYTHON = $(KIVYIOSROOT)/tmp/Python-$(PYTHON_VERSION)/hostpython

.PHONY: build force hook test clean distclean theming

build:
	$(PYTHON) setup.py build_ext --inplace

force:
	$(PYTHON) setup.py build_ext --inplace -f

hook:
	# Install pre-commit git hook to check your changes for styleguide
	# consistency.
	cp kivy/tools/pep8checker/pre-commit.githook .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

test:
	-rm -rf kivy/tests/build
	$(NOSETESTS) kivy/tests

install:
	python setup.py install
clean:
	-rm -rf build
	-find App -iname '*.so' -exec rm {} \;
	-find App -iname '*.pyc' -exec rm {} \;
	-find App -iname '*.pyo' -exec rm {} \;
	-find App -iname '*.cpp' -exec rm {} \;

distclean: clean
	-git clean -dxf

theming:
	$(PYTHON) -m kivy.atlas kivy/data/images/defaulttheme 512 kivy/tools/theming/defaulttheme/*.png

