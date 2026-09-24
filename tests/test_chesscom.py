# import API functions for testing
from chesslab.api.chesscom import (
    get_game_archives,
    download_monthly_games,
)

# get_game_archives ==============================================================================================================

## archives is defined as we'd expect
def test_get_game_archives():
    archives = get_game_archives("hikaru")

    assert isinstance(archives, list)
    assert len(archives) > 0

## archives URL has correct prefix
def test_get_game_archives_contains_archive_url():
    archives = get_game_archives("hikaru")

    assert archives[0].startswith("https://api.chess.com/")

# download_monthly_games =========================================================================================================

## pgn object is defined as we'd expect
def test_download_monthly_games():
    pgn = download_monthly_games("hikaru", 2025, 1)

    assert isinstance(pgn, str)
    assert len(pgn) > 0

## pgn contains expected information
def test_download_monthly_games_contains_pgn():
    pgn = download_monthly_games("hikaru", 2025, 1)

    assert "[Event" in pgn