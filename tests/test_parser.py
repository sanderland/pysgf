import os

import pytest

from pysgf import BaseGoGame, BaseGoNode, GoGame, GoNode, Move, ParseError


def data_file(name):
    return os.path.join(os.path.dirname(__file__), "data", name)


def test_simple():
    input_sgf = "(;GM[1]FF[4]SZ[19]DT[2020-04-12]AB[dd][dj];B[dp];W[pp];B[pj])"
    root = GoGame.parse(input_sgf)
    assert "4" == root.get_property("FF")
    assert root.get_property("XYZ") is None
    assert "dp" == root.children[0].get_property("B")
    assert input_sgf == root.sgf()


def test_parse_aliases_agree():
    input_sgf = "(;GM[1]FF[4]SZ[19];B[dp])"
    assert GoGame.parse(input_sgf).sgf() == GoGame.parse_sgf(input_sgf).sgf()
    assert GoGame.from_string(input_sgf).root.sgf() == GoGame.parse(input_sgf).sgf()


def test_branch():
    input_sgf = "(;GM[1]FF[4]CA[UTF-8]AP[Sabaki:0.43.3]KM[6.5]SZ[19]DT[2020-04-12]AB[dd][dj](;B[dp];W[pp](;B[pj])(;PL[B]AW[jp]C[sdfdsfdsf]))(;B[pd]))"
    root = GoGame.parse(input_sgf)
    assert input_sgf == root.sgf()


def test_dragon_weirdness():  # dragon go server has weird line breaks
    input_sgf = "\n(\n\n;\nGM[1]\nFF[4]\nCA[UTF-8]AP[Sabaki:0.43.3]KM[6.5]SZ[19]DT[2020-04-12]AB[dd]\n[dj]\n(\n;\nB[dp]\n;\nW[pp]\n(\n;\nB[pj]\n)\n(\n;\nPL[B]\nAW[jp]\nC[sdfdsfdsf]\n)\n)\n(\n;\nB[pd]\n)\n)\n"
    root = GoGame.parse(input_sgf)
    assert input_sgf.replace("\n", "") == root.sgf()


def test_newline_between_property_and_value():
    input_sgf = "(;GM[1]FF[4]SZ[19]DT\n[2020-04-12];B\n[dp])"
    root = GoGame.parse(input_sgf)
    assert "2020-04-12" == root.get_property("DT")
    assert "dp" == root.children[0].get_property("B")


def test_weird_escape():
    input_sgf = """(;GM[1]FF[4]CA[UTF-8]AP[Sabaki:0.43.3]KM[6.5]SZ[19]DT[2020-04-12]C[how does it escape
[
or \\]
])"""
    root = GoGame.parse(input_sgf)
    assert input_sgf == root.sgf()


def test_backslash_escape():
    nasty_string = "[]]\\"
    nasty_strings = ["[\\]\\]\\\\", "[", "]", "\\", "\\[", "\\]", "\\\\[", "\\\\]", "]]]\\]]\\]]["]
    assert "[\\]\\]\\\\" == GoNode._escape_value(nasty_string)
    for value in nasty_strings:
        assert value == GoNode._unescape_value(GoNode._escape_value(value))

    c2 = ["]", "\\"]
    node = GoNode(properties={"C1": nasty_string})
    node.set_property("C2", c2)
    assert "(;C1[[\\]\\]\\\\]C2[\\]][\\\\])" == node.sgf()
    assert {"C1": [nasty_string], "C2": c2} == GoGame.parse(node.sgf()).properties


def test_alphago():
    GoGame.parse_file(data_file("LS vs AG - G4 - English.sgf"))


def test_pandanet():
    root = GoGame.parse_file(data_file("panda1.sgf"))
    root_props = {
        "GM",
        "EV",
        "US",
        "CP",  # normalized from old-style 'CoPyright'
        "GN",
        "RE",
        "PW",
        "WR",
        "NW",
        "PB",
        "BR",
        "NB",
        "PC",
        "DT",
        "SZ",
        "TM",
        "KM",
        "LT",
        "RR",
        "HA",
        "AB",
        "C",
    }
    assert root_props == root.properties.keys()

    move = root
    while move.children:
        move = move.children[0]
    assert 94 == len(move.get_list_property("TW"))
    assert "Trilan" == move.get_property("OS")
    while move.parent:
        move = move.parent
    assert move is root


def test_old_long_properties():
    root = GoGame.parse_file(data_file("xmgt97.sgf"))
    assert (9, 9) == root.board_size
    assert -1.5 == root.komi


def test_old_server_style():
    GoGame.parse("... 01:23:45 +0900 (JST) ... (;SZ[19];B[aa];W[ba];)")


def test_old_server_style_again():
    input_sgf = """(;
SZ[19]TM[600]KM[0.500000]LT[]

;B[fp]BL[500];

)"""
    tree = GoGame.parse(input_sgf)
    assert 2 == len(tree.nodes_in_tree)


def test_ogs():
    GoGame.parse_file(data_file("ogs.sgf"))


def test_kgs():
    GoGame.parse_file(data_file("kgs.sgf"))


def test_gibo():
    root = GoGame.parse_file(data_file("test.gib"))
    assert {
        "PW": ["wildsim1"],
        "WR": ["2D"],
        "PB": ["kim"],
        "BR": ["2D"],
        "RE": ["W+T"],
        "KM": [6.5],
        "DT": ["2020-06-14"],
    } == root.properties
    assert "pd" == root.children[0].get_property("B")


def test_ngf():
    root = GoGame.parse_file(data_file("handicap2.ngf"))
    root.properties["AB"].sort()
    assert {
        "AB": ["dp", "pd"],
        "DT": ["2017-03-16"],
        "HA": [2],
        "PB": ["p81587"],
        "PW": ["ace550"],
        "RE": ["W+"],
        "SZ": [19],
    } == root.properties
    assert "pq" == root.children[0].get_property("W")


def test_unsupported_extension():
    with pytest.raises(ParseError):
        GoGame.from_string("(;GM[1])", ext="xyz")


def test_foxwq():
    for sgf, expected_komi in [("fox sgf error.sgf", 0.5), ("fox sgf works.sgf", 6.5)]:
        root = GoGame.parse_file(data_file(sgf))
        assert "foxwq" in root.get_list_property("AP")
        assert expected_komi == root.komi  # fox KM values are wrong and corrected on parse
        assert [] == root.placements
        node = root
        while node.children:
            assert 1 == len(node.children)
            node = node.children[0]


def test_komi_and_handicap():
    assert 6.5 == GoGame.parse("(;GM[1])").komi
    assert 6.5 == GoGame.parse("(;GM[1]KM[garbage])").komi
    assert 7.5 == GoGame.parse("(;GM[1]KM[7.5])").komi
    assert 0 == GoGame.parse("(;GM[1])").handicap
    assert 0 == GoGame.parse("(;GM[1]HA[garbage])").handicap
    assert 2 == GoGame.parse("(;GM[1]HA[2])").handicap


def test_next_player():
    input_sgf = "(;GM[1]FF[4]AB[aa]AW[bb])"
    assert "B" == GoGame.parse(input_sgf).next_player
    assert "B" == GoGame.parse(input_sgf).initial_player
    input_sgf = "(;GM[1]FF[4]AB[aa]AW[bb]PL[B])"
    assert "B" == GoGame.parse(input_sgf).next_player
    assert "B" == GoGame.parse(input_sgf).initial_player
    input_sgf = "(;GM[1]FF[4]AB[aa]AW[bb]PL[W])"
    assert "W" == GoGame.parse(input_sgf).next_player
    assert "W" == GoGame.parse(input_sgf).initial_player
    input_sgf = "(;GM[1]FF[4]AB[aa])"
    assert "W" == GoGame.parse(input_sgf).next_player
    assert "W" == GoGame.parse(input_sgf).initial_player
    input_sgf = "(;GM[1]FF[4]AB[aa]PL[B])"
    assert "B" == GoGame.parse(input_sgf).next_player
    assert "B" == GoGame.parse(input_sgf).initial_player
    input_sgf = "(;GM[1]FF[4]AB[aa];B[dd])"  # branch exists
    assert "B" == GoGame.parse(input_sgf).next_player
    assert "B" == GoGame.parse(input_sgf).initial_player
    input_sgf = "(;GM[1]FF[4]AB[aa];W[dd])"  # branch exists
    assert "W" == GoGame.parse(input_sgf).next_player
    assert "W" == GoGame.parse(input_sgf).initial_player


def test_placements():
    input_sgf = "(;GM[1]FF[4]SZ[19]DT[2020-04-12]AB[dd][aa:ee]AW[ff:zz]AE[aa][bb][cc:dd])"
    root = GoGame.parse(input_sgf)
    assert 6 == len(root.clear_placements)
    assert 25 + 14 * 14 == len(root.placements)


def test_tt_pass():
    root = GoGame.parse("(;GM[1]FF[4]SZ[19];B[tt])")
    assert root.children[0].move.is_pass
    root = GoGame.parse("(;GM[1]FF[4]SZ[25];B[tt])")  # tt is a normal move on big boards
    assert not root.children[0].move.is_pass


def test_subclassing():
    """Downstream projects (e.g. KaTrain) subclass the generic base classes with their own node type."""

    class MyNode(BaseGoNode["MyNode"]):
        def __init__(self, parent=None, properties=None, move=None):
            super().__init__(parent=parent, properties=properties, move=move)
            self.extra = "custom"

        @staticmethod
        def order_children(children):
            return sorted(children, key=lambda c: -len(c.children))

    class MyGame(BaseGoGame[MyNode]):
        NODE_TYPE = MyNode

    root = MyGame.parse("(;GM[1]FF[4]SZ[19]AB[dd];B[dp];W[pp])")
    assert isinstance(root, MyNode)
    assert "custom" == root.extra
    assert all(isinstance(node, MyNode) for node in root.nodes_in_tree)
    assert isinstance(root.play(Move.from_gtp("Q16", "W")), MyNode)
    assert isinstance(root.children[0].parent, MyNode)
