from pathlib import Path

import chess
import chess.svg
import streamlit.components.v1 as components

import plotly.express as px
import requests
import streamlit as st

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


# define the logo path and configure streamlit before displaying anything
LOGO_PATH = Path(__file__).parent / "assets" / "chesslab-logo.png"
st.set_page_config(page_title="ChessLab", page_icon=LOGO_PATH, layout="wide")


# developer information
with st.sidebar:
    st.subheader("About ChessLab")

    st.write(
        "ChessLab is a chess analytics and coaching application "
        "built to help players understand their games and improve."
    )

    st.divider()

    st.markdown("**👨‍💻 Developed by Tim Mooney**")
    st.caption("Built with Python, Stockfish, and Streamlit.")

    st.link_button(
        "View on GitHub",
        "https://github.com/timmymooney/ChessLab",
    )

    st.link_button(
        "Connect on LinkedIn",
        "https://www.linkedin.com/in/timothy-mooney1998/",
    )


# cache chess.com requests without coupling the data modules to streamlit
@st.cache_data(show_spinner=False)
def load_games(username):
    return load_player_games(username)


@st.cache_data(ttl=3600)
def load_ratings(username):
    return get_player_stats(username)



# compare the position before a mistake with the two candidate moves
def show_move_review(mistakes):
    st.markdown("#### ♟️ Interactive Move Review")
    st.caption("Choose a critical move, then switch between the original position and both continuations.")

    if mistakes.empty:
        st.info("No critical moves available to review with the current filters.")
        return

    options = mistakes.reset_index(drop=True)
    selected_index = st.selectbox(
        "Select a critical move",
        options.index.tolist(),
        format_func=lambda i: (
            f"Game {options.loc[i, 'game']} · Move {options.loc[i, 'move']} · "
            f"{options.loc[i, 'category']} · {options.loc[i, 'loss_cp']} cp"
        ),
        key="move_review_selection",
    )
    selected = options.loc[selected_index]

    try:
        original_board = chess.Board(selected["fen"])
        # study_plan.py currently stores SAN (e.g. Nf3), not UCI (e.g. g1f3)
        played_move = original_board.parse_san(str(selected["played"]))
        best_move = original_board.parse_san(str(selected["best"]))
    except (ValueError, TypeError, KeyError) as error:
        st.warning(f"Unable to display this position: {error}")
        return

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.metric("Your Move", original_board.san(played_move),
                      delta=f"-{int(selected['loss_cp'])} cp", delta_color="inverse")
    with col2:
        with st.container(border=True):
            st.metric("Stockfish's Best Move", original_board.san(best_move))

    view = st.radio(
        "Board position",
        ["Before the move", "Your move", "Stockfish's move"],
        horizontal=True,
        key="move_review_view",
    )
    display_board = original_board.copy()
    arrows = []
    if view == "Your move":
        display_board.push(played_move)
        arrows = [chess.svg.Arrow(played_move.from_square, played_move.to_square,
                                  color="#A65E5E")]
    elif view == "Stockfish's move":
        display_board.push(best_move)
        arrows = [chess.svg.Arrow(best_move.from_square, best_move.to_square,
                                  color="#24AF21")]
    else:
        arrows = [
            chess.svg.Arrow(played_move.from_square, played_move.to_square,
                            color="#A65E5E"),
            chess.svg.Arrow(best_move.from_square, best_move.to_square,
                            color="#24AF21"),
        ]

    orientation = chess.WHITE if selected["colour"] == "White" else chess.BLACK
    svg_board = chess.svg.board(board=display_board, orientation=orientation,
                                arrows=arrows, size=480)
    components.html(
        f'<div style="display:flex;justify-content:center">{svg_board}</div>',
        height=505,
    )
    st.caption(
        f"Game {selected['game']} · Playing as {selected['colour']} · "
        f"Result: {selected['result']} · Red = played move · Green = Stockfish"
    )
    if selected.get("game_link"):
        st.link_button("View game on Chess.com", selected["game_link"])


# app header
st.image(str(LOGO_PATH), width=440)
st.title("Analyse and improve your chess!")
st.caption("♟️ Developed by Tim Mooney | Python • Stockfish • Streamlit")
st.divider()

home_tab, analysis_tab = st.tabs(["🧬 Player Profile", "🔍 Game Analysis"])

with home_tab:
    username_input = st.text_input(
        "Enter your Chess.com username",
        placeholder="e.g. hikaru",
    ).strip()

    if st.button("Analyse my games", type="primary"):
        if username_input:
            # avoid showing a previous player's stockfish results
            if st.session_state.get("username") != username_input:
                st.session_state.pop("study_result", None)
            st.session_state["username"] = username_input
        else:
            st.warning("Please enter a Chess.com username.")

# only fetch data after the player has requested a profile
profile_ready = False
if "username" in st.session_state:
    username = st.session_state["username"]
    try:
        with st.spinner("Downloading and analysing your games..."):
            games_df = load_games(username)
            ratings = load_ratings(username)

        if games_df.empty:
            st.warning("No games found for this username.")
        else:
            games_df = prepare_games(games_df, username)
            profile_ready = True
    except (requests.RequestException, ValueError, KeyError) as error:
        st.error(f"Unable to load Chess.com data: {error}")

if profile_ready:
    with home_tab:
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

        st.success("Player profile loaded! Open the 🔍 Chess Analysis tab to study your games.")

    with analysis_tab:
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
            title="Game Endings: My Wins(Green) vs Opponent Wins(Red)",
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
            "Choose which recent games to analyse with Stockfish (depth=10). "
            "Larger selections may take several minutes."
        )

        # choose games before running stockfish
        col1, col2, col3 = st.columns(3)
        with col1:
            game_selection = st.selectbox(
                "Games to analyse",
                ["All results", "Losses and draws only"],
            )
        with col2:
            game_limit = st.number_input(
                "Number of games",
                min_value=1,
                max_value=50,
                value=5,
                step=1,
            )

        with col3:
            time_control = st.selectbox(
                "Chess Type",
                ["All", "Rapid", "Daily", "Blitz", "Bullet"],
            )

        losses_and_draws_only = game_selection == "Losses and draws only"
        analysis_settings = (
            username, int(game_limit), losses_and_draws_only, time_control
        )

        if st.button("Generate study plan", type="primary"):
            # discard an older result if a new analysis fails
            st.session_state.pop("study_result", None)
            try:
                with st.spinner("Stockfish is reviewing your recent games..."):
                    mistakes, analysed_count = analyse_recent_games(
                        username,
                        limit=int(game_limit),
                        depth=10,
                        losses_and_draws_only=losses_and_draws_only,
                        time_control=time_control,
                    )
                st.session_state["study_result"] = (
                    analysis_settings, mistakes, analysed_count
                )
            except (FileNotFoundError, OSError, ValueError, requests.RequestException) as error:
                st.error(f"Unable to analyse games: {error}")

        study_result = st.session_state.get("study_result")
        if study_result and study_result[0] != analysis_settings:
            st.info("Game selection changed. Click 'Generate study plan' to analyse the new selection.")
        elif study_result:
            _, mistakes, analysed_count = study_result
            st.write(f"Games analysed: **{analysed_count}**")

            if analysed_count == 0:
                st.info("No recent games matched your selection.")
            else:
                # metrics always describe all analysed moves, regardless of table filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    with st.container(border=True):
                        st.metric(
                            "Mistakes",
                            int((mistakes["category"] == "Mistake").sum()),
                        )
                with col2:
                    with st.container(border=True):
                        st.metric(
                            "Major Mistakes",
                            int((mistakes["category"] == "Major Mistake").sum()),
                        )
                with col3:
                    with st.container(border=True):
                        st.metric(
                            "Blunders",
                            int((mistakes["category"] == "Blunder").sum()),
                        )

                # filter displayed moves without repeating stockfish analysis
                selected_categories = st.multiselect(
                    "Show move classifications",
                    ["Mistake", "Major Mistake", "Blunder"],
                    default=["Mistake", "Major Mistake", "Blunder"],
                )
                filtered_mistakes = mistakes[
                    mistakes["category"].isin(selected_categories)
                ]

                st.markdown("#### Your personalised study priorities")
                for recommendation in build_study_plan(filtered_mistakes):
                    st.write(f"- {recommendation}")

                # display critical moves with clickable chess.com links
                st.markdown("#### Critical moves to review")
                if filtered_mistakes.empty:
                    st.info("No moves match the selected classifications.")
                else:
                    st.dataframe(
                        filtered_mistakes,
                        column_config={
                            "time_control": st.column_config.TextColumn("Chess Type"),
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

                # review selected mistakes without rerunning stockfish
                st.divider()
                show_move_review(filtered_mistakes)

                st.caption(
                    "Thresholds: Mistake ≥100 centipawns (cp); Major Mistake ≥250 cp; "
                    "Blunder ≥500 cp. These are ChessLab classifications, not official "
                    "Chess.com classifications. Counters show all analysed moves."
                )
else:
    with analysis_tab:
        st.info(
            "🧬 Go back to the Player Profile tab and your fetch your Chess.com data before starting analysis."
        )
