from pysgf import SGF, Move
import os


def test_simple():
    tree = SGF.parse("(;GM[1]FF[4]SZ[19]DT[2020-04-12]AB[dd][dj];B[dp];W[pp];B[pj])")
    assert "Move({'GM': '1', 'FF': '4', 'SZ': 19, 'DT': '2020-04-12', 'AB': ['dd', 'dj']})\n\tMove({'B': 'dp'})\n\t\tMove({'W': 'pp'})\n\t\t\tMove({'B': 'pj'})" == str(tree)


def test_branch():
    tree = SGF.parse("(;GM[1]FF[4]CA[UTF-8]AP[Sabaki:0.43.3]KM[6.5]SZ[19]DT[2020-04-12]AB[dd][dj](;B[dp];W[pp](;B[pj])(;PL[B]AW[jp]C[sdfdsfdsf]))(;B[pd]))")
    assert (
        "Move({'GM': '1', 'FF': '4', 'CA': 'UTF-8', 'AP': 'Sabaki:0.43.3', 'KM': 6.5, 'SZ': 19, 'DT': '2020-04-12', 'AB': ['dd', 'dj']})\n\tMove({'B': 'dp'})\n\t\tMove({'W': 'pp'})\n\t\t\tMove({'B': 'pj'})\n\t\t\tMove({'PL': 'B', 'AW': ['jp'], 'C': 'sdfdsfdsf'})\n\tMove({'B': 'pd'})"
        == str(tree)
    )


def test_weird_escsape():
    tree = SGF.parse(
        """(;GM[1]FF[4]CA[UTF-8]AP[Sabaki:0.43.3]KM[6.5]SZ[19]DT[2020-04-12]C[how does it escape
[
or \\]
])"""
    )
    assert "Move({'GM': '1', 'FF': '4', 'CA': 'UTF-8', 'AP': 'Sabaki:0.43.3', 'KM': 6.5, 'SZ': 19, 'DT': '2020-04-12', 'C': 'how does it escape\\n[\\nor \\\\]\\n'})" == str(tree)


def test_alphago():
    file = os.path.join(os.path.dirname(__file__), "data/LS vs AG - G4 - English.sgf")
    tree = SGF.parse_file(file)


def test_pandanet():
    file = os.path.join(os.path.dirname(__file__), "data/panda1.sgf")
    root = SGF.parse_file(file)
    assert {
        "GM": "1",
        "EV": "Internet Go Server game: player1 vs player2",
        "US": "Brought to you by IGS PANDANET",
        "CoPyright": "\r\n  Copyright (c) PANDANET Inc. 2020\r\n  Permission to reproduce this game is given, provided proper credit is given.\r\n  No warrantee, implied or explicit, is understood.\r\n  Use of this game is an understanding and agreement of this notice.\r\n",
        "GN": "player1-player2(B) IGS",
        "RE": "W+34.5",
        "PW": "player1",
        "WR": "11k+",
        "NW": "18",
        "PB": "player2",
        "BR": "12k ",
        "NB": "17",
        "PC": "IGS:  igs.joyjoy.net 6969",
        "DT": "2020-04-10",
        "SZ": 19,
        "TM": "60",
        "KM": 0.5,
        "LT": "",
        "RR": "Normal",
        "HA": "2",
        "AB": ["pd", "dp"],
        "C": "\r\n player2 12k : gg\r\n player1 11k+: Hi!\r\n player2 12k : Hi!\r\n",
    } == root.properties

    move = root
    while move.children:
        move = move.children[0]
    assert ['am', 'al', 'ak', 'bm', 'bl', 'cm', 'dg', 'df', 'ef', 'ee', 'ff', 'fe', 'fd', 'fc',
            'fb', 'fa', 'gs', 'gr', 'gq', 'gp', 'go', 'gf', 'ge', 'gd', 'gc', 'gb', 'ga', 'hs',
            'hr', 'hq', 'hp', 'ho', 'hn', 'hg', 'he', 'hd', 'hc', 'hb', 'ha', 'is', 'ir', 'iq',
            'ip', 'io', 'in', 'ig', 'if', 'ie', 'id', 'ic', 'ib', 'ia', 'jq', 'jp', 'jo', 'jn',
            'jm', 'jl', 'jk', 'jj', 'ko', 'kn', 'km', 'kl', 'kk', 'po', 'qq', 'qp', 'qo', 'qn',
            'qe', 'rs', 'rr', 'rq', 'rp', 'ro', 'rn', 're', 'rd', 'rc', 'rb', 'ra', 'ss', 'sr',
            'sq', 'sp', 'so', 'sn', 'sm', 'se', 'sd', 'sc', 'sb', 'sa'] == move.properties["TW"]

    assert "Trilan" == move.properties["OS"]


def test_ogs():
    file = os.path.join(os.path.dirname(__file__), "data/ogs.sgf")
    tree = SGF.parse_file(file)
