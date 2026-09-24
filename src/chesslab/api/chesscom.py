import requests


BASE_URL = "https://api.chess.com/pub/player"
HEADERS = {
    "User-Agent": "ChessLab/0.1"
}


def get_game_archives(username: str) -> list[str]:
    """Return the available monthly game archives for a Chess.com player."""
    url = f"{BASE_URL}/{username}/games/archives"

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    return response.json()["archives"]


def download_monthly_games(username: str, year: int, month: int) -> str:
    """Download a player's games for a specific month as PGN."""
    url = f"{BASE_URL}/{username}/games/{year}/{month:02d}/pgn"

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    return response.text