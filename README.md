# PySGF
[![Release Status](https://github.com/sanderland/pysgf/workflows/release/badge.svg)](https://github.com/sanderland/pysgf/actions)
[![PyPI version](https://badge.fury.io/py/pysgf.svg)](https://pypi.org/project/pysgf/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


PySGF is a lightweight but powerful parser for the Go SGF Format.

## Quickstart

```python
from pysgf import SGF
# parse either a string ..
root = SGF.parse(input_sgf)
# or pass a file name. It will try to detect the encoding specified in the SGF file
root = SGF.parse_file(input_file_name)
# all properties are stored as lists, but you can ask for the first
root.get_list_property('AB')
root.get_property('KM')
move = root.move # returns a Move object with options for SGF, GTP or 0- based coordinates
children = root.children # returns all child nodes
```

## Documentation
1. Install sphinx and sphinx_rtd_theme
```shell
pip install sphinx sphinx_rtd_theme
```

2. Clone this repository
```shell
git clone https://github.com/sanderland/pysgf.git
cd sanderland/pysgf/docs
```

3. Run the makefile
```shell
make html
```
