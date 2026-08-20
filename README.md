# PySGF
[![Release Status](https://github.com/sanderland/pysgf/workflows/release/badge.svg)](https://github.com/sanderland/pysgf/actions)
[![PyPI version](https://badge.fury.io/py/pysgf.svg)](https://pypi.org/project/pysgf/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


PySGF is a lightweight but powerful parser for Go game records,
supporting the SGF format as well as NGF and GIB.

## Quickstart

```python
from pysgf import GoGame
# parse either a string ..
root = GoGame.parse(input_sgf)
# or pass a file name. It will try to detect the encoding specified in the record file.
# files ending in .ngf or .gib are parsed as those formats instead.
root = GoGame.parse_file(input_file_name)
# all properties are stored as lists, but you can ask for the first
root.get_list_property('AB')
root.get_property('KM')
move = root.move # returns a Move object with options for SGF, GTP or 0- based coordinates
children = root.children # returns all child nodes
```

`parse`/`parse_sgf`/`parse_file` return the root node. To keep the game object itself,
use `GoGame.from_string(contents, ext="sgf")` or `GoGame.from_file(filename)` and
access `game.root`.

## Extending

`GoGame` and `GoNode` are the concrete classes for everyday use. Projects that need to
attach their own state or behaviour to nodes can subclass the generic base classes,
which keeps `parent`, `children` and `play()` typed as the subclass:

```python
from pysgf import BaseGoGame, BaseGoNode

class MyNode(BaseGoNode["MyNode"]):
    def __init__(self, parent=None, properties=None, move=None):
        super().__init__(parent=parent, properties=properties, move=move)
        self.my_analysis = None

class MyGame(BaseGoGame[MyNode]):
    NODE_TYPE = MyNode

root = MyGame.parse(input_sgf)  # -> MyNode
```

## Requirements

Python 3.11 or newer.

## Documentation
For documentation, run `make html` in the `docs` directory.
