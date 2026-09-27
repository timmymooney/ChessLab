from chesslab.chess.parser import (
    parse_game,
    parse_games,
)

# parse_game ====================================================================================================================

## that one PGN becomes one Game object and that the headers were parsed correctly.
def test_parse_game():
    pgn = """
[Event "Test Game"]
[White "Player 1"]
[Black "Player 2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
"""

    game = parse_game(pgn)

    assert game is not None
    assert game.headers["White"] == "Player 1"
    assert game.headers["Black"] == "Player 2"

# parse_games ===================================================================================================================

## that multiple PGNs become multiple Game objects and that we're getting the right games back
def test_parse_games():
    pgn = """
[Event "Game 1"]
[White "Player 1"]
[Black "Player 2"]
[Result "1-0"]

1. e4 e5 1-0

[Event "Game 2"]
[White "Player 3"]
[Black "Player 4"]
[Result "0-1"]

1. d4 d5 0-1
"""

    games = parse_games(pgn)

    assert len(games) == 2
    assert games[0].headers["White"] == "Player 1"
    assert games[1].headers["White"] == "Player 3"