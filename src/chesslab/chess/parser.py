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


def get_game_info(game: chess.pgn.Game, username: str | None = None) -> dict:
    """Extract basic information from a parsed game."""
    return {
        "username": username,
        "white": game.headers.get("White"),
        "black": game.headers.get("Black"),
        "result": game.headers.get("Result"),
        "date": game.headers.get("Date"),
        "eco": game.headers.get("ECO"),
        "white_elo": game.headers.get("WhiteElo"),
        "black_elo": game.headers.get("BlackElo"),
        "time_control": game.headers.get("TimeControl"),
        "termination": game.headers.get("Termination"),
        "link": game.headers.get("Link"),
    }