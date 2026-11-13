import requests


BASE_URL = "https://api.chess.com/pub"
HEADERS = {"User-Agent": "ChessLab/0.1"}


def get_game_archives(username):
    url = f"{BASE_URL}/player/{username}/games/archives"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()["archives"]


def download_monthly_games(username, year, month):
    url = f"{BASE_URL}/player/{username}/games/{year}/{month:02d}/pgn"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def get_player_stats(username):
    url = f"{BASE_URL}/player/{username}/stats"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()
