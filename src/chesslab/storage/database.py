import sqlite3
from pathlib import Path


def create_connection(database_path: str | Path) -> sqlite3.Connection:
    """Create a connection to the ChessLab SQLite database."""
    return sqlite3.connect(database_path)


def create_games_table(connection: sqlite3.Connection) -> None:
    """Create the games table if it does not already exist."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            white TEXT,
            black TEXT,
            result TEXT,
            date TEXT,
            eco TEXT,
            white_elo INTEGER,
            black_elo INTEGER,
            time_control TEXT,
            termination TEXT,
            link TEXT,
            pgn TEXT
        )
        """
    )

    connection.commit()


def save_game(
    connection: sqlite3.Connection,
    game_info: dict,
    pgn: str,
) -> None:
    """Save a game to the database."""
    connection.execute(
        """
        INSERT INTO games (
            username,
            white,
            black,
            result,
            date,
            eco,
            white_elo,
            black_elo,
            time_control,
            termination,
            link,
            pgn
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            game_info.get("username"),
            game_info.get("white"),
            game_info.get("black"),
            game_info.get("result"),
            game_info.get("date"),
            game_info.get("eco"),
            game_info.get("white_elo"),
            game_info.get("black_elo"),
            game_info.get("time_control"),
            game_info.get("termination"),
            game_info.get("link"),
            pgn,
        ),
    )

    connection.commit()


def get_games(connection: sqlite3.Connection) -> list[tuple]:
    """Return all games stored in the database."""
    cursor = connection.execute(
        "SELECT * FROM games"
    )

    return cursor.fetchall()