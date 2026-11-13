import re

import pandas as pd

from chesslab.api.chesscom import get_game_archives, download_monthly_games
from chesslab.chess.parser import parse_games, get_game_info


def load_player_games(username):
    archives = get_game_archives(username)
    monthly_pgns = []

    for archive in archives:
        match = re.search(r"/games/(\d{4})/(\d{2})$", archive)

        if match:
            year, month = map(int, match.groups())
            pgn = download_monthly_games(username, year, month)

            if pgn.strip():
                monthly_pgns.append(pgn)

    games = parse_games("\n\n".join(monthly_pgns))
    return pd.DataFrame([get_game_info(game, username) for game in games])


def get_end_reason(termination):
    text = str(termination).lower()

    if "checkmate" in text:
        return "Checkmate"
    if "resign" in text:
        return "Resignation"
    if "time" in text:
        return "Timeout"
    if "abandon" in text:
        return "Abandonment"

    return "Other"


def prepare_games(games_df, username):
    games_df = games_df.copy()

    # identify which colour the user played
    my_white = games_df["white"].str.lower().eq(username.lower())
    my_black = games_df["black"].str.lower().eq(username.lower())

    games_df["my_colour"] = None
    games_df.loc[my_white, "my_colour"] = "White"
    games_df.loc[my_black, "my_colour"] = "Black"

    # identify wins, losses and draws
    games_df["my_result"] = "Unknown"
    games_df.loc[
        (my_white | my_black) & (games_df["result"] == "1/2-1/2"),
        "my_result",
    ] = "Draw"
    games_df.loc[
        (my_white & (games_df["result"] == "1-0"))
        | (my_black & (games_df["result"] == "0-1")),
        "my_result",
    ] = "Win"
    games_df.loc[
        (my_white & (games_df["result"] == "0-1"))
        | (my_black & (games_df["result"] == "1-0")),
        "my_result",
    ] = "Loss"

    # use chess.com time controls to identify game types
    time_control_mapping = {
        "1800": "Rapid",
        "900+10": "Rapid",
        "600": "Rapid",
        "300": "Blitz",
        "1/86400": "Daily",
        "1/259200": "Daily",
        "1/864000": "Daily",
    }
    games_df["chess_type"] = games_df["time_control"].map(time_control_mapping)

    # prepare date and rating
    games_df["date"] = pd.to_datetime(
        games_df["date"], format="%Y.%m.%d", errors="coerce"
    )
    games_df["my_rating"] = pd.to_numeric(
        games_df["white_elo"].where(my_white, games_df["black_elo"]),
        errors="coerce",
    )

    # classify game endings
    games_df["end_reason"] = games_df["termination"].apply(get_end_reason)

    def get_game_ending(row):
        if row["my_result"] == "Draw":
            return "Draw"
        if row["my_result"] == "Win":
            return f"{username} wins by {row['end_reason'].lower()}"
        if row["my_result"] == "Loss":
            return f"Opponent wins by {row['end_reason'].lower()}"
        return "Unknown"

    games_df["game_ending"] = games_df.apply(get_game_ending, axis=1)
    return games_df


def get_result_stats(games_df):
    results = games_df["my_result"].value_counts()
    total_games = len(games_df)
    completed_games = sum(results.get(result, 0) for result in ("Win", "Loss", "Draw"))

    def percentage(result):
        return 100 * results.get(result, 0) / completed_games if completed_games else 0

    return {
        "total_games": total_games,
        "win_count": int(results.get("Win", 0)),
        "loss_count": int(results.get("Loss", 0)),
        "draw_count": int(results.get("Draw", 0)),
        "win_percentage": percentage("Win"),
        "loss_percentage": percentage("Loss"),
        "draw_percentage": percentage("Draw"),
    }


def get_rating_history(games_df):
    return games_df.dropna(
        subset=["date", "my_rating", "chess_type"]
    ).sort_values("date")


def get_ending_counts(games_df):
    ending_counts = games_df["game_ending"].value_counts().reset_index()
    ending_counts.columns = ["game_ending", "count"]
    return ending_counts


def get_endings_by_result(games_df):
    return (
        games_df[games_df["my_result"].isin(["Win", "Loss"])]
        .groupby(["end_reason", "my_result"])
        .size()
        .reset_index(name="count")
    )
