import io

import chess.pgn


def parse_game(pgn: str):
    """Parse a single PGN game."""
    game = chess.pgn.read_game(io.StringIO(pgn))

    return game