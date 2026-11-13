import re

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from chesslab.api.chesscom import get_game_archives, download_monthly_games
from chesslab.chess.parser import parse_games, get_game_info


# configure the app
st.set_page_config(page_title="ChessLab", page_icon="♟️", layout="wide")


# download and prepare player games
@st.cache_data(show_spinner=False)
def load_games(username):
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


# get current chess.com ratings
@st.cache_data(ttl=3600)
def load_ratings(username):
    url = f"https://api.chess.com/pub/player/{username}/stats"
    response = requests.get(
        url,
        headers={"User-Agent": "ChessLab/0.1"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# classify how each game ended
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


# prepare the columns needed for our charts
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


# app header
st.title("♟️ ChessLab")
st.caption("Analyse your Chess.com games and improve your chess.")
st.divider()

username = st.text_input(
    "Enter your Chess.com username",
    placeholder="e.g. hikaru",
).strip()

if st.button("Analyse games", type="primary"):
    if username:
        st.session_state["username"] = username
    else:
        st.warning("Please enter a Chess.com username.")


# display the dashboard
if "username" in st.session_state:
    username = st.session_state["username"]

    try:
        with st.spinner("Downloading and analysing games..."):
            games_df = load_games(username)
            ratings = load_ratings(username)

        if games_df.empty:
            st.warning("No games found for this username.")
            st.stop()

        games_df = prepare_games(games_df, username)

    except (requests.RequestException, ValueError, KeyError) as error:
        st.error(f"Unable to load Chess.com data: {error}")
        st.stop()

    st.header(f"Player Overview: {username}")
    st.caption("Your Chess.com performance, ratings and game statistics.")

    # calculate headline statistics
    results = games_df["my_result"].value_counts()
    total_games = len(games_df)
    completed_games = sum(results.get(result, 0) for result in ("Win", "Loss", "Draw"))

    def percentage(result):
        return 100 * results.get(result, 0) / completed_games if completed_games else 0

    # display game statistics
    st.subheader("Performance Overview")
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.metric("♟️ Total Games Played", f"{total_games:,}")

    with col2:
        with st.container(border=True):
            st.metric(
                "🏆 Win Rate",
                f"{percentage('Win'):.1f}%",
                delta=f"{results.get('Win', 0)} wins",
                delta_color="off",
            )

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.metric(
                "Loss Rate",
                f"{percentage('Loss'):.1f}%",
                delta=f"{results.get('Loss', 0)} losses",
                delta_color="off",
            )

    with col4:
        with st.container(border=True):
            st.metric(
                "Draw Rate",
                f"{percentage('Draw'):.1f}%",
                delta=f"{results.get('Draw', 0)} draws",
                delta_color="off",
            )

    # display current chess.com ratings
    st.subheader("Current Chess.com Ratings")
    rapid = ratings.get("chess_rapid", {}).get("last", {}).get("rating", "N/A")
    blitz = ratings.get("chess_blitz", {}).get("last", {}).get("rating", "N/A")
    daily = ratings.get("chess_daily", {}).get("last", {}).get("rating", "N/A")

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric("Rapid", rapid)
    with col2:
        with st.container(border=True):
            st.metric("Blitz", blitz)
    with col3:
        with st.container(border=True):
            st.metric("Daily", daily)

    st.divider()

    # plot rating history
    st.subheader("Rating History")
    rating_df = games_df.dropna(
        subset=["date", "my_rating", "chess_type"]
    ).sort_values("date")

    fig = px.line(
        rating_df,
        x="date",
        y="my_rating",
        color="chess_type",
        markers=True,
        title="Chess Rating Over Time",
        labels={
            "date": "Date",
            "my_rating": "Rating",
            "chess_type": "Chess Type",
        },
        color_discrete_map={
            "Rapid": "#24AF21",
            "Blitz": "#FFF203",
            "Daily": "#FFAE00",
        },
    )
    fig.update_layout(hovermode="x unified", margin=dict(t=55, b=30))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Game Analysis")
    st.caption("How your games end, and which endings lead to wins or losses.")

    # count each game ending
    ending_counts = games_df["game_ending"].value_counts().reset_index()
    ending_counts.columns = ["game_ending", "count"]

    fig = px.bar(
        ending_counts,
        x="count",
        y="game_ending",
        orientation="h",
        title="How My Games Ended",
        labels={"game_ending": "Game Ending", "count": "Games"},
        text="count",
        color_discrete_sequence=["#606060"],
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(t=55, b=30))
    st.plotly_chart(fig, use_container_width=True)

    # compare wins and losses by ending reason
    ending_by_result = (
        games_df[games_df["my_result"].isin(["Win", "Loss"])]
        .groupby(["end_reason", "my_result"])
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        ending_by_result,
        x="end_reason",
        y="count",
        color="my_result",
        barmode="group",
        color_discrete_map={"Win": "#7A9B83", "Loss": "#A65E5E"},
        title="Game Endings: My Wins vs Opponent Wins",
        labels={
            "end_reason": "Ending Reason",
            "count": "Games",
            "my_result": "Result",
        },
        text="count",
    )
    fig.update_layout(margin=dict(t=55, b=30))
    st.plotly_chart(fig, use_container_width=True)