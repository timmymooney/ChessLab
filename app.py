import plotly.express as px
import requests
import streamlit as st
from pathlib import Path

from chesslab.api.chesscom import get_player_stats
from chesslab.coaching.study_plan import analyse_recent_games, build_study_plan
from chesslab.analytics.performance import (
    get_ending_counts,
    get_endings_by_result,
    get_rating_history,
    get_result_stats,
    load_player_games,
    prepare_games,
)

# define the logo path
LOGO_PATH = Path(__file__).parent / "assets" / "chesslab-logo.png"

# display the chesslab branding
st.image(str(LOGO_PATH), width=440)

# configure the app
st.set_page_config(
    page_title="",
    page_icon=LOGO_PATH,
    layout="wide",
)


# cache chess.com requests without coupling the data modules to streamlit
@st.cache_data(show_spinner=False)
def load_games(username):
    return load_player_games(username)


@st.cache_data(ttl=3600)
def load_ratings(username):
    return get_player_stats(username)


# app header
st.title("Analyse and improve your chess!")
st.divider()

username = st.text_input(
    "Enter your Chess.com username",
    placeholder="e.g. hikaru",
).strip()

if st.button("Analyse my games", type="primary"):
    if username:
        st.session_state["username"] = username
    else:
        st.warning("Please enter a Chess.com username.")


# display the dashboard
if "username" in st.session_state:
    username = st.session_state["username"]

    try:
        with st.spinner("Downloading and analysing your games..."):
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

    # display game statistics
    stats = get_result_stats(games_df)
    st.subheader("Performance Overview")
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.metric("♟️ Total Games Played", f"{stats['total_games']:,}")

    with col2:
        with st.container(border=True):
            st.metric(
                "🏆 Win Rate",
                f"{stats['win_percentage']:.1f}%",
                delta=f"{stats['win_count']} wins",
                delta_color="off",
            )

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.metric(
                "🙂‍↕️ Loss Rate",
                f"{stats['loss_percentage']:.1f}%",
                delta=f"{stats['loss_count']} losses",
                delta_color="off",
            )

    with col4:
        with st.container(border=True):
            st.metric(
                "🤝 Draw Rate",
                f"{stats['draw_percentage']:.1f}%",
                delta=f"{stats['draw_count']} draws",
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
            st.metric("⏱️ Rapid", rapid)
    with col2:
        with st.container(border=True):
            st.metric("⚡️ Blitz", blitz)
    with col3:
        with st.container(border=True):
            st.metric("☀️ Daily", daily)

    st.divider()

    # plot rating history
    st.subheader("Rating History")
    rating_df = get_rating_history(games_df)

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
    ending_counts = get_ending_counts(games_df)

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
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"}, margin=dict(t=55, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)

    # compare wins and losses by ending reason
    ending_by_result = get_endings_by_result(games_df)

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

    st.divider()
    st.subheader("Recommended Study Plan")
    st.caption(
        "Analyse five recent games with Stockfish (Stockfish depth=10). "
        "This may take a minute or two."
    )

    if st.button("Generate study plan", type="primary"):
        try:
            with st.spinner("Stockfish is reviewing your recent games..."):
                mistakes, analysed_count = analyse_recent_games(
                    username, limit=5, depth=10
                )
            st.session_state["study_result"] = (
                username, mistakes, analysed_count
            )
        except (FileNotFoundError, OSError, ValueError, requests.RequestException) as error:
            st.error(f"Unable to analyse games: {error}")

    study_result = st.session_state.get("study_result")
    if study_result and study_result[0] == username:
        _, mistakes, analysed_count = study_result
        st.write(f"Games analysed: **{analysed_count}**")

        if analysed_count == 0:
            st.info("No recent games were found.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Mistakes",
                int((mistakes["category"] == "Mistake").sum()),
            )
            col2.metric(
                "Major Mistakes",
                int((mistakes["category"] == "Major Mistake").sum()),
            )
            col3.metric(
                "Blunders",
                int((mistakes["category"] == "Blunder").sum()),
            )

            st.markdown("#### Suggested study priorities")
            for recommendation in build_study_plan(mistakes):
                st.write(f"- {recommendation}")

            # display mistakes with clickable chess.com links
            if not mistakes.empty:
                st.markdown("#### Critical moves to review")
                st.dataframe(
                    mistakes,
                    column_config={
                        "colour": st.column_config.TextColumn("Playing As"),
                        "result": st.column_config.TextColumn("Game Result"),
                        "game_link": st.column_config.LinkColumn(
                            "View Game",
                            display_text="Open on Chess.com",
                        ),
                        "loss_cp": st.column_config.NumberColumn(
                            "Evaluation Loss (cp)",
                            format="%d",
                        ),
                        "fen": None,
                    },
                    hide_index=True,
                    use_container_width=True,
                )

            st.caption(
                "Thresholds: Mistake ≥100 centipawns(cp); Major Mistake ≥250 cp; "
                "Blunder ≥500 cp. These are ChessLab classifications, not official Chess.com classifications."
            )
