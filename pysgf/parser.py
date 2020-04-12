import re
from typing import Tuple, List, Union


class ParseError(Exception):
    pass


class Move:
    def __init__(self):
        self.children = []
        self.properties = {}

    def __str__(self):
        return "\n".join([f"Move({self.properties})"] + [f"\t{l}" for m in self.children for l in str(m).split("\n")])

    def empty(self):
        return not self.children and not self.properties

    def set_property(self, prop, value):
        if prop in ["AB", "AW", "TW", "TB"]:  # lists (placements, marked dead)
            self.properties[prop] = re.split(r"\]\s*\[", value)
        elif prop in ["KM"]:  # floats
            self.properties[prop] = float(value)
        elif prop in ["SZ"]:  # ints
            self.properties[prop] = int(value)
        else:
            self.properties[prop] = value

    def __getitem__(self, ix):
        return self.properties.get(ix)


class SGF:
    def __init__(self, contents):
        self.contents = contents
        self.ix = 0
        if self._nextchr() != "(":
            raise ParseError("Expected '(' at start of input")
        self.root = self._parse_branch()

    @staticmethod
    def parse(input_str):
        return SGF(input_str).root

    @staticmethod
    def parse_file(filename, encoding=None):
        with open(filename, "rb") as f:
            str = f.read()
            if not encoding:
                match = re.search(rb"CA\[(.*?)\]", str)
                if match:
                    encoding = match[1].decode("ascii")
                else:
                    encoding = "utf-8"  # default
            decoded = str.decode(encoding=encoding)
            return SGF.parse(decoded)

    def _nextchr(self, ignore_whitespace=True) -> str:
        c = self.contents[self.ix]
        while ignore_whitespace and c in [" ", "\n", "\r", "\t"]:
            self.ix += 1
            c = self.contents[self.ix]
        self.ix += 1
        return c

    def _parse_branch(self) -> Move:
        move_tree = Move()
        current_move = move_tree

        while self.ix < len(self.contents):
            c = self._nextchr()
            if c == ")":
                return move_tree
            if c == "(":
                current_move.children.append(self._parse_branch())
            elif c == ";":
                if not current_move.empty():  # ignore ; that generate empty nodes
                    nextmove = Move()
                    current_move.children.append(nextmove)
                    current_move = nextmove
            else:
                self.ix -= 1
                prop, value = self.parse_property()
                current_move.set_property(prop, value)
        raise ParseError("Expected ')' at end of input")

    def parse_property(self) -> Tuple[str, str]:
        match = re.match(r"(\w+)((?:\[.*?(?<!\\)\]\s*)+)", self.contents[self.ix :], re.DOTALL)
        if not match:
            raise ParseError(f"Parse Error (expected property) at {self.contents[self.ix-25:self.ix]}>{self.contents[self.ix]}<{self.contents[self.ix+1:self.ix+25]}")
        self.ix += len(match[0])
        return match[1], match[2].strip()[1:-1]
