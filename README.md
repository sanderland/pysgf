# PySGF

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
For documentation, run `make html` in the `docs` directory.






