import io

import chess.pgn


def parse_game(pgn: str) -> chess.pgn.Game | None:
    """Parse a single PGN game."""
    return chess.pgn.read_game(io.StringIO(pgn))


def parse_games(pgn: str) -> list[chess.pgn.Game]:
    """Parse multiple games from a PGN string."""
    games = []
    pgn_io = io.StringIO(pgn)

    while game := chess.pgn.read_game(pgn_io):
        games.append(game)

    return games