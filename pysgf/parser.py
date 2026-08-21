from __future__ import annotations

import copy
import math
import re
from collections import defaultdict
from typing import Any, ClassVar, Generic, Self, TypeVar, cast

import chardet

NodeT = TypeVar("NodeT", bound="BaseGoNode[Any]")


class ParseError(Exception):
    """Exception raised on a parse error"""


class Move:
    GTP_COORD = list("ABCDEFGHJKLMNOPQRSTUVWXYZ") + [xa + c for xa in "ABCDEFGH" for c in "ABCDEFGHJKLMNOPQRSTUVWXYZ"]
    PLAYERS = "BW"
    SGF_COORD = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ".lower()) + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    @classmethod
    def from_gtp(cls, gtp_coords, player="B"):
        if "pass" in gtp_coords.lower():
            return cls(coords=None, player=player)
        match = re.match(r"([A-Z]+)(\d+)", gtp_coords)
        return cls(coords=(Move.GTP_COORD.index(match[1]), int(match[2]) - 1), player=player)

    @classmethod
    def from_sgf(cls, sgf_coords, board_size, player="B"):
        if sgf_coords == "" or (sgf_coords == "tt" and board_size[0] <= 19 and board_size[1] <= 19):
            return cls(coords=None, player=player)
        return cls(
            coords=(Move.SGF_COORD.index(sgf_coords[0]), board_size[1] - Move.SGF_COORD.index(sgf_coords[1]) - 1),
            player=player,
        )

    def __init__(self, coords: tuple[int, int] | None = None, player: str = "B"):
        self.player = player
        self.coords = coords

    def __repr__(self):
        return f"Move({self.player or ''}{self.gtp()})"

    def __eq__(self, other):
        return self.coords == other.coords and self.player == other.player

    def __hash__(self):
        return hash((self.coords, self.player))

    def gtp(self):
        if self.is_pass:
            return "pass"
        return Move.GTP_COORD[self.coords[0]] + str(self.coords[1] + 1)

    def sgf(self, board_size):
        if self.is_pass:
            return ""
        return f"{Move.SGF_COORD[self.coords[0]]}{Move.SGF_COORD[board_size[1] - self.coords[1] - 1]}"

    @property
    def is_pass(self):
        return self.coords is None

    @staticmethod
    def opponent_player(player):
        return "W" if player == "B" else "B"

    @property
    def opponent(self):
        return self.opponent_player(self.player)


class BaseGoNode(Generic[NodeT]):
    def __init__(
        self,
        parent: NodeT | None = None,
        properties: dict[str, Any] | None = None,
        move: Move | None = None,
    ):
        self.children = []
        self.properties = defaultdict(list)
        if properties:
            for key, value in properties.items():
                self.set_property(key, value)
        self.parent = parent
        if self.parent:
            self.parent.children.append(cast(NodeT, self))
        if parent and move:
            self.set_property(move.player, move.sgf(self.board_size))
        self._clear_cache()

    def _clear_cache(self):
        self.moves_cache = None

    def __repr__(self):
        return f"{self.__class__.__name__}({dict(self.properties)})"

    def sgf_properties(self, **xargs) -> dict:
        return copy.deepcopy(self.properties)

    @staticmethod
    def order_children(children: list[NodeT]) -> list[NodeT]:
        return children

    @property
    def ordered_children(self) -> list[NodeT]:
        return self.order_children(self.children)

    @staticmethod
    def _escape_value(value):
        return re.sub(r"([\]\\])", r"\\\1", value) if isinstance(value, str) else value

    @staticmethod
    def _unescape_value(value):
        return re.sub(r"\\([\]\\])", r"\1", value) if isinstance(value, str) else value

    def sgf(self, **xargs) -> str:
        def node_sgf_str(node):
            return ";" + "".join(
                [
                    prop + "".join(f"[{self._escape_value(v)}]" for v in values)
                    for prop, values in node.sgf_properties(**xargs).items()
                    if values
                ]
            )

        stack = [")", self, "("]
        sgf_str = ""
        while stack:
            item = stack.pop()
            if isinstance(item, str):
                sgf_str += item
            else:
                sgf_str += node_sgf_str(item)
                if len(item.children) == 1:
                    stack.append(item.children[0])
                elif item.children:
                    stack += sum([[")", child, "("] for child in item.ordered_children[::-1]], [])
        return sgf_str

    def add_list_property(self, property: str, values: list):
        normalized_property = re.sub("[a-z]", "", property)
        self._clear_cache()
        self.properties[normalized_property] += values

    def get_list_property(self, property, default=None) -> Any:
        return self.properties.get(property, default)

    def set_property(self, property: str, value: Any):
        if not isinstance(value, list):
            value = [value]
        self._clear_cache()
        self.properties[property] = value

    def get_property(self, property, default=None) -> Any:
        return self.properties.get(property, [default])[0]

    def clear_property(self, property) -> Any:
        return self.properties.pop(property, None)

    @property
    def parent(self) -> NodeT | None:
        return self._parent

    @parent.setter
    def parent(self, parent_node: NodeT | None):
        self._parent = parent_node
        self._root = None
        self._depth = None

    @property
    def root(self) -> NodeT:
        if self._root is None:
            self._root = self.parent.root if self.parent else cast(NodeT, self)
        return self._root

    @property
    def depth(self) -> int:
        if self._depth is None:
            if self.is_root:
                self._depth = 0
            else:
                self._depth = self.parent.depth + len(self.moves)
        return self._depth

    @property
    def board_size(self) -> tuple[int, int]:
        size = str(self.root.get_property("SZ", "19"))
        if ":" in size:
            x, y = map(int, size.split(":"))
        else:
            x = int(size)
            y = x
        return x, y

    @property
    def komi(self) -> float:
        try:
            return float(self.root.get_property("KM", 6.5))
        except ValueError:
            return 6.5

    @property
    def handicap(self) -> int:
        try:
            return int(self.root.get_property("HA", 0))
        except ValueError:
            return 0

    @property
    def ruleset(self) -> str:
        return self.root.get_property("RU", "japanese")

    @property
    def moves(self) -> list[Move]:
        if self.moves_cache is None:
            self.moves_cache = [
                Move.from_sgf(move, player=player, board_size=self.board_size)
                for player in Move.PLAYERS
                for move in self.get_list_property(player, [])
            ]
        return self.moves_cache

    def _expanded_placements(self, player):
        sgf_pl = player if player is not None else "E"
        placements = self.get_list_property("A" + sgf_pl, [])
        if not placements:
            return []
        to_be_expanded = [placement for placement in placements if ":" in placement]
        board_size = self.board_size
        if to_be_expanded:
            coords = {
                Move.from_sgf(sgf_coord, player=player, board_size=board_size)
                for sgf_coord in placements
                if ":" not in sgf_coord
            }
            for placement in to_be_expanded:
                from_coord, to_coord = [
                    Move.from_sgf(coord, board_size=board_size) for coord in placement.split(":")[:2]
                ]
                for x in range(from_coord.coords[0], to_coord.coords[0] + 1):
                    for y in range(to_coord.coords[1], from_coord.coords[1] + 1):
                        if 0 <= x < board_size[0] and 0 <= y < board_size[1]:
                            coords.add(Move((x, y), player=player))
            return list(coords)
        return [Move.from_sgf(sgf_coord, player=player, board_size=board_size) for sgf_coord in placements]

    @property
    def placements(self) -> list[Move]:
        return [coord for player in Move.PLAYERS for coord in self._expanded_placements(player)]

    @property
    def clear_placements(self) -> list[Move]:
        return self._expanded_placements(None)

    @property
    def move_with_placements(self) -> list[Move]:
        return self.placements + self.moves

    @property
    def move(self) -> Move | None:
        moves = self.moves
        if len(moves) == 1:
            return moves[0]
        return None

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def is_pass(self) -> bool:
        return not self.placements and self.move and self.move.is_pass

    @property
    def empty(self) -> bool:
        return not self.children and not self.properties

    @property
    def nodes_in_tree(self) -> list[NodeT]:
        stack = [cast(NodeT, self)]
        nodes = []
        while stack:
            item = stack.pop(0)
            nodes.append(item)
            stack += item.children
        return nodes

    @property
    def nodes_from_root(self) -> list[NodeT]:
        nodes = [cast(NodeT, self)]
        node = cast(NodeT, self)
        while not node.is_root:
            node = node.parent
            nodes.append(node)
        return nodes[::-1]

    def play(self: Self, move: Move) -> Self:
        for child in self.children:
            if child.move and child.move == move:
                return cast(Self, child)
        return type(self)(parent=self, move=move)

    @property
    def initial_player(self):
        root = self.root
        if "PL" in root.properties:
            return "B" if self.root.get_property("PL").upper().strip() == "B" else "W"
        if root.children:
            for child in root.children:
                for color in "BW":
                    if color in child.properties:
                        return color
        if "AB" in self.properties and "AW" not in self.properties:
            return "W"
        return "B"

    @property
    def next_player(self):
        if self.is_root:
            return self.initial_player
        if "B" in self.properties:
            return "W"
        if "W" in self.properties:
            return "B"
        return self.parent.next_player

    @property
    def player(self):
        if "B" in self.properties or ("AB" in self.properties and "W" not in self.properties):
            return "B"
        return "W"

    def place_handicap_stones(self, n_handicaps, tygem=False):
        board_size_x, board_size_y = self.board_size
        if min(board_size_x, board_size_y) < 3:
            return
        near_x = 3 if board_size_x >= 13 else min(2, board_size_x - 1)
        near_y = 3 if board_size_y >= 13 else min(2, board_size_y - 1)
        far_x = board_size_x - 1 - near_x
        far_y = board_size_y - 1 - near_y
        middle_x = board_size_x // 2
        middle_y = board_size_y // 2
        if n_handicaps > 9 and board_size_x == board_size_y:
            stones_per_row = math.ceil(math.sqrt(n_handicaps))
            spacing = (far_x - near_x) / (stones_per_row - 1)
            if spacing < near_x:
                far_x += 1
                near_x -= 1
                spacing = (far_x - near_x) / (stones_per_row - 1)
            coords = list({math.floor(0.5 + near_x + i * spacing) for i in range(stones_per_row)})
            stones = sorted(
                [(x, y) for x in coords for y in coords],
                key=lambda xy: -((xy[0] - (board_size_x - 1) / 2) ** 2 + (xy[1] - (board_size_y - 1) / 2) ** 2),
            )
        else:
            stones = [(far_x, far_y), (near_x, near_y), (far_x, near_y), (near_x, far_y)]
            if n_handicaps % 2 == 1:
                stones.append((middle_x, middle_y))
            stones += [(near_x, middle_y), (far_x, middle_y), (middle_x, near_y), (middle_x, far_y)]
        if tygem:
            stones[2], stones[3] = stones[3], stones[2]
        self.set_property(
            "AB", list({Move(stone).sgf(board_size=(board_size_x, board_size_y)) for stone in stones[:n_handicaps]})
        )


class GoNode(BaseGoNode["GoNode"]):
    pass


class BaseGoGame(Generic[NodeT]):
    DEFAULT_ENCODING = "UTF-8"

    NODE_TYPE: ClassVar[type[NodeT]]
    SGFPROP_PAT = re.compile(r"\s*(?:\(|\)|;|(\w+)((\s*\[([^\]\\]|\\.)*\])+))", flags=re.DOTALL)
    SGF_PAT = re.compile(r"\(;.*\)", flags=re.DOTALL)

    @classmethod
    def from_string(cls, input_str: str, ext: str = "sgf") -> Self:
        if ext == "sgf":
            return cls._from_sgf_string(input_str)
        if ext == "ngf":
            return cls._from_ngf_string(input_str)
        if ext == "gib":
            return cls._from_gib_string(input_str)
        raise ParseError(f"Unsupported file extension: {ext}")

    @classmethod
    def from_file(cls, filename: str, encoding: str | None = None) -> Self:
        is_gib = filename.lower().endswith(".gib")
        is_ngf = filename.lower().endswith(".ngf")
        with open(filename, "rb") as file_handle:
            bin_contents = file_handle.read()
            if not encoding:
                if is_gib or is_ngf or b"AP[foxwq]" in bin_contents:
                    encoding = "utf8"
                else:
                    match = re.search(rb"CA\[(.*?)\]", bin_contents)
                    if match:
                        encoding = match[1].decode("ascii", errors="ignore")
                    else:
                        encoding = chardet.detect(bin_contents[:300])["encoding"]
                        if encoding in {"Windows-1252", "GB2312"}:
                            encoding = "GBK"
            try:
                decoded = bin_contents.decode(encoding=encoding, errors="ignore")
            except LookupError:
                decoded = bin_contents.decode(encoding=cls.DEFAULT_ENCODING, errors="ignore")
        ext = "ngf" if is_ngf else "gib" if is_gib else "sgf"
        return cls.from_string(decoded, ext=ext)

    @classmethod
    def parse(cls, input_str: str) -> NodeT:
        return cls.parse_sgf(input_str)

    @classmethod
    def parse_sgf(cls, input_str: str) -> NodeT:
        return cls._from_sgf_string(input_str).root

    @classmethod
    def parse_file(cls, filename: str, encoding: str | None = None) -> NodeT:
        return cls.from_file(filename, encoding=encoding).root

    @classmethod
    def _new_game_with_root(cls, root: NodeT) -> Self:
        game = cls.__new__(cls)
        game.contents = ""
        game.ix = 0
        game.root = root
        return game

    @classmethod
    def _from_sgf_string(cls, input_str: str) -> Self:
        match = re.search(cls.SGF_PAT, input_str)
        clipped_str = match.group() if match else input_str
        game = cls(clipped_str)
        root = game.root
        if "foxwq" in root.get_list_property("AP", []):
            if int(root.get_property("HA", 0)) >= 1:
                corrected_komi = 0.5
            elif root.get_property("RU", "japanese").lower() in ["chinese", "cn"]:
                corrected_komi = 7.5
            else:
                corrected_komi = 6.5
            root.set_property("KM", corrected_komi)
        return game

    def __init__(self, contents: str):
        self.contents = contents
        try:
            self.ix = self.contents.index("(") + 1
        except ValueError as exc:
            raise ParseError(f"Parse error: Expected '(' at start, found {self.contents[:50]}") from exc
        self.root = self.NODE_TYPE()
        self._parse_branch(self.root)

    def _parse_branch(self, current_move: NodeT):
        while self.ix < len(self.contents):
            match = re.match(self.SGFPROP_PAT, self.contents[self.ix :])
            if not match:
                break
            self.ix += len(match[0])
            matched_item = match[0].strip()
            if matched_item == ")":
                return
            if matched_item == "(":
                self._parse_branch(self.NODE_TYPE(parent=current_move))
            elif matched_item == ";":
                useless = self.ix < len(self.contents) and self.contents[self.ix :].strip() == ")"
                if not (current_move.empty or useless):
                    current_move = self.NODE_TYPE(parent=current_move)
            else:
                property = match[1]
                value = match[2].strip()[1:-1]
                values = re.split(r"\]\s*\[", value)
                current_move.add_list_property(property, [GoNode._unescape_value(v) for v in values])
        if self.ix < len(self.contents):
            raise ParseError(f"Parse Error: unexpected character at {self.contents[self.ix : self.ix + 25]}")
        raise ParseError("Parse Error: expected ')' at end of input.")

    @classmethod
    def parse_ngf(cls, ngf: str) -> NodeT:
        return cls._from_ngf_string(ngf).root

    @classmethod
    def _from_ngf_string(cls, ngf: str) -> Self:
        ngf = ngf.strip()
        lines = ngf.split("\n")
        try:
            boardsize = int(lines[1])
            handicap = int(lines[5])
            pw = lines[2].split()[0]
            pb = lines[3].split()[0]
            rawdate = lines[8][0:8]
            komi = float(lines[7])
            if handicap == 0 and int(komi) == komi:
                komi += 0.5
        except (IndexError, ValueError):
            boardsize = 19
            handicap = 0
            pw = ""
            pb = ""
            rawdate = ""
            komi = 0

        result = ""
        try:
            if "hite win" in lines[10]:
                result = "W+"
            elif "lack win" in lines[10]:
                result = "B+"
        except IndexError:
            pass

        if handicap < 0 or handicap > 9:
            raise ParseError(f"Handicap {handicap} out of range")

        root = cls.NODE_TYPE()
        node = root
        root.set_property("SZ", boardsize)
        if handicap >= 2:
            root.set_property("HA", handicap)
            root.place_handicap_stones(handicap, tygem=True)
        if komi:
            root.set_property("KM", komi)
        if len(rawdate) == 8 and all(rawdate[n] in "0123456789" for n in range(8)):
            root.set_property("DT", rawdate[0:4] + "-" + rawdate[4:6] + "-" + rawdate[6:8])
        if pw:
            root.set_property("PW", pw)
        if pb:
            root.set_property("PB", pb)
        if result:
            root.set_property("RE", result)

        for line in lines:
            line = line.strip().upper()
            if len(line) >= 7 and line[0:2] == "PM" and line[4] in ["B", "W"]:
                key = line[4]
                raw_move = line[5:7].lower()
                value = "" if raw_move == "aa" else chr(ord(raw_move[0]) - 1) + chr(ord(raw_move[1]) - 1)
                node = cls.NODE_TYPE(parent=node)
                node.set_property(key, value)

        if len(root.children) == 0:
            raise ParseError("Found no moves")
        return cls._new_game_with_root(root)

    @classmethod
    def parse_gib(cls, gib: str) -> NodeT:
        return cls._from_gib_string(gib).root

    @classmethod
    def _from_gib_string(cls, gib: str) -> Self:
        def parse_player_name(raw):
            name = raw
            rank = ""
            parts = raw.split("(")
            if len(parts) == 2 and parts[1][-1] == ")":
                name = parts[0].strip()
                rank = parts[1][0:-1]
            return name, rank

        def gib_make_result(grlt, zipsu):
            easycases = {3: "B+R", 4: "W+R", 7: "B+T", 8: "W+T"}
            if grlt in easycases:
                return easycases[grlt]
            if grlt in [0, 1]:
                return "{}+{}".format("B" if grlt == 0 else "W", zipsu / 10)
            return ""

        def gib_get_result(line, grlt_regex, zipsu_regex):
            try:
                grlt = int(re.search(grlt_regex, line).group(1))
                zipsu = int(re.search(zipsu_regex, line).group(1))
            except (AttributeError, ValueError):
                return ""
            return gib_make_result(grlt, zipsu)

        root = cls.NODE_TYPE()
        node = root

        for line in gib.split("\n"):
            line = line.strip()
            if line.startswith("\\[GAMEBLACKNAME=") and line.endswith("\\]"):
                name, rank = parse_player_name(line[16:-2])
                if name:
                    root.set_property("PB", name)
                if rank:
                    root.set_property("BR", rank)
            if line.startswith("\\[GAMEWHITENAME=") and line.endswith("\\]"):
                name, rank = parse_player_name(line[16:-2])
                if name:
                    root.set_property("PW", name)
                if rank:
                    root.set_property("WR", rank)
            if line.startswith("\\[GAMEINFOMAIN="):
                result = gib_get_result(line, r"GRLT:(\d+),", r"ZIPSU:(\d+),")
                if result:
                    root.set_property("RE", result)
                    try:
                        komi = int(re.search(r"GONGJE:(\d+),", line).group(1)) / 10
                        if komi:
                            root.set_property("KM", komi)
                    except (AttributeError, ValueError):
                        pass
            if line.startswith("\\[GAMETAG="):
                if "DT" not in root.properties:
                    try:
                        match = re.search(r"C(\d\d\d\d):(\d\d):(\d\d)", line)
                        root.set_property("DT", f"{match.group(1)}-{match.group(2)}-{match.group(3)}")
                    except (AttributeError, ValueError):
                        pass
                if "RE" not in root.properties:
                    result = gib_get_result(line, r",W(\d+),", r",Z(\d+),")
                    if result:
                        root.set_property("RE", result)
                if "KM" not in root.properties:
                    try:
                        komi = int(re.search(r",G(\d+),", line).group(1)) / 10
                        if komi:
                            root.set_property("KM", komi)
                    except (AttributeError, ValueError):
                        pass
            if line[0:3] == "INI":
                if node is not root:
                    raise ParseError("Node is not root")
                setup = line.split()
                try:
                    handicap = int(setup[3])
                except (ValueError, IndexError):  # truncated or malformed INI line
                    continue
                if handicap < 0 or handicap > 9:
                    raise ParseError(f"Handicap {handicap} out of range")
                if handicap >= 2:
                    root.set_property("HA", handicap)
                    root.place_handicap_stones(handicap, tygem=True)
            if line[0:3] == "STO":
                try:
                    move = line.split()
                    key = "B" if move[3] == "1" else "W"
                    x = int(move[4])
                    y = 18 - int(move[5])
                except (IndexError, ValueError) as exc:
                    raise ParseError(f"Malformed STO line: {line}") from exc
                if not (0 <= x < 19 and 0 <= y < 19):
                    raise ParseError(f"Coordinates for move ({x},{y}) out of range on line {line}")
                value = Move(coords=(x, y)).sgf(board_size=(19, 19))
                node = cls.NODE_TYPE(parent=node)
                node.set_property(key, value)

        if len(root.children) == 0:
            raise ParseError("No valid nodes found")
        return cls._new_game_with_root(root)


class GoGame(BaseGoGame[GoNode]):
    NODE_TYPE = GoNode
