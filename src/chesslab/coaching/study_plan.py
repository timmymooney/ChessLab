import io
import os
import shutil

import chess
import chess.engine
import chess.pgn
import pandas as pd

from chesslab.api.chesscom import download_monthly_games, get_game_archives


COLUMNS = [
    "game", "date", "time_control", "colour", "result", "move", "played", "best",
    "category", "loss_cp", "fen", "phase", "game_link",
]


def get_player_result(game, username):
    # interpret the pgn result from the player's perspective
    white = game.headers.get("White", "").lower() == username.lower()
    result = game.headers.get("Result", "*")

    if result == "1/2-1/2":
        return "Draw"
    if result == "1-0":
        return "Win" if white else "Loss"
    if result == "0-1":
        return "Loss" if white else "Win"
    return "Unknown"


TIME_CONTROL_MAPPING = {
    "1800": "Rapid",
    "900+10": "Rapid",
    "600": "Rapid",
    "300": "Blitz",
    "1/86400": "Daily",
    "1/259200": "Daily",
    "1/864000": "Daily",
    "-": "Other",
}


def get_time_control(game):
    # map known chess.com values and classify other common time controls
    value = game.headers.get("TimeControl", "").strip()
    if value in TIME_CONTROL_MAPPING:
        return TIME_CONTROL_MAPPING[value]
    if not value or value == "?":
        return "Other"

    try:
        if "/" in value:
            # daily pgn values are typically moves / seconds per move
            _, seconds = value.split("/", 1)
            return "Daily" if int(seconds) >= 86400 else "Other"

        parts = value.split("+")
        base = int(parts[0])
        increment = int(parts[1]) if len(parts) == 2 else 0
        if base >= 86400:
            return "Daily"
        estimated_seconds = base + 40 * increment
        if estimated_seconds < 180:
            return "Bullet"
        if estimated_seconds < 600:
            return "Blitz"
        return "Rapid"
    except (ValueError, IndexError):
        return "Other"


def get_recent_games(username, limit=5, losses_and_draws_only=False, time_control="All"):
    # select eligible games before limiting how many stockfish will analyse
    games = []
    for archive in reversed(get_game_archives(username)):
        year, month = archive.rstrip("/").split("/")[-2:]
        pgn_text = download_monthly_games(username, int(year), int(month))
        pgn_stream = io.StringIO(pgn_text)
        monthly_games = []

        while game := chess.pgn.read_game(pgn_stream):
            white = game.headers.get("White", "").lower()
            black = game.headers.get("Black", "").lower()
            if username.lower() not in (white, black):
                continue
            if losses_and_draws_only and get_player_result(game, username) not in ("Loss", "Draw"):
                continue
            if time_control != "All" and get_time_control(game) != time_control:
                continue
            monthly_games.append(game)

        games.extend(reversed(monthly_games))
        if len(games) >= limit:
            break

    return games[:limit]


def analyse_recent_games(
    username, limit=5, depth=10, losses_and_draws_only=False, time_control="All"
):
    # support stockfish on macos and in docker
    engine_path = os.getenv("STOCKFISH_PATH") or shutil.which("stockfish")
    if not engine_path:
        raise FileNotFoundError(
            "Stockfish was not found. Set STOCKFISH_PATH to its executable path."
        )

    games = get_recent_games(username, limit, losses_and_draws_only, time_control)
    rows = []

    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        for game_number, game in enumerate(games, start=1):
            white = game.headers.get("White", "").lower() == username.lower()
            player_colour = chess.WHITE if white else chess.BLACK
            colour = "White" if white else "Black"
            my_result = get_player_result(game, username)
            board = game.board()

            for move in game.mainline_moves():
                # only evaluate the player's moves
                if board.turn != player_colour:
                    board.push(move)
                    continue

                played_san = board.san(move)
                position_fen = board.fen()
                move_number = board.fullmove_number

                if move_number <= 12:
                    phase = "Opening"
                elif len(board.piece_map()) <= 12:
                    phase = "Endgame"
                else:
                    phase = "Middlegame"

                best_analysis = engine.analyse(board, chess.engine.Limit(depth=depth))
                best_line = best_analysis.get("pv", [])
                if not best_line:
                    board.push(move)
                    continue

                best_move = best_line[0]
                best_san = board.san(best_move)

                # avoid penalising a move stockfish identifies as best
                if move == best_move:
                    board.push(move)
                    continue

                played_analysis = engine.analyse(
                    board,
                    chess.engine.Limit(depth=depth),
                    root_moves=[move],
                )
                best_score = best_analysis["score"].pov(player_colour)
                played_score = played_analysis["score"].pov(player_colour)
                board.push(move)

                # mate evaluations are not comparable with centipawn thresholds
                if best_score.is_mate() or played_score.is_mate():
                    continue

                best_cp = best_score.score()
                played_cp = played_score.score()
                if best_cp is None or played_cp is None:
                    continue

                loss_cp = max(0, best_cp - played_cp)
                if loss_cp < 100:
                    continue

                # chesslab thresholds: 100 / 250 / 500 centipawns
                if loss_cp >= 500:
                    category = "Blunder"
                elif loss_cp >= 250:
                    category = "Major Mistake"
                else:
                    category = "Mistake"

                rows.append({
                    "game": game_number,
                    "date": game.headers.get("Date", "Unknown"),
                    "time_control": get_time_control(game),
                    "colour": colour,
                    "result": my_result,
                    "move": move_number,
                    "played": played_san,
                    "best": best_san,
                    "category": category,
                    "loss_cp": loss_cp,
                    "fen": position_fen,
                    "phase": phase,
                    "game_link": game.headers.get("Link", ""),
                })

    return pd.DataFrame(rows, columns=COLUMNS), len(games)


def build_study_plan(mistakes):
    # recommendations describe observed patterns, not unverified tactical causes
    if mistakes.empty:
        return [
            "No moves matched the current selection. Try another severity "
            "filter or analyse more games."
        ]

    priorities = []

    # focus on the phase with the most significant errors
    phase_counts = mistakes["phase"].value_counts()
    phase = phase_counts.index[0]
    count = int(phase_counts.iloc[0])
    priorities.append(
        f"‼️ Priority 1, {phase} improvement: {count} significant evaluation "
        f"drops occurred in the {phase.lower()}."
    )

    # compare errors per game rather than raw counts across unequal game samples
    games_by_colour = mistakes.groupby("colour")["game"].nunique()
    if len(games_by_colour) > 1:
        counts = mistakes.groupby("colour").size()
        rates = counts / games_by_colour
        weaker_colour = rates.idxmax()
        priorities.append(
            f"❗️ Priority 2, playing as {weaker_colour}: The analysed games "
            f"with significant errors averaged {rates[weaker_colour]:.1f} "
            "flagged moves per game for this colour."
        )
    else:
        priorities.append(
            "❗️ Priority 2, colour review: Compare your games as White and "
            "Black once you have analysed more games with significant errors."
        )

    # point to concrete positions using the largest evaluation losses
    worst = mistakes.nlargest(3, "loss_cp")
    positions = ", ".join(
        f"game {int(row.game)}, move {int(row.move)} ({int(row.loss_cp)} cp)"
        for row in worst.itertuples()
    )
    priorities.append(
        f"🔍 Priority 3, review decisive errors: Start with {positions}."
    )
    return priorities
