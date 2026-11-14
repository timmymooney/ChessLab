import io
import os
import shutil

import chess
import chess.engine
import chess.pgn
import pandas as pd

from chesslab.api.chesscom import download_monthly_games, get_game_archives


def get_recent_games(username, limit=5):
    # read the newest monthly archives first
    games = []

    for archive in reversed(get_game_archives(username)):
        year, month = archive.rstrip("/").split("/")[-2:]
        pgn_text = download_monthly_games(username, int(year), int(month))
        pgn_stream = io.StringIO(pgn_text)
        monthly_games = []

        while game := chess.pgn.read_game(pgn_stream):
            white = game.headers.get("White", "").lower()
            black = game.headers.get("Black", "").lower()

            if username.lower() in (white, black):
                monthly_games.append(game)

        # reverse the month's games to start with the most recent
        games.extend(reversed(monthly_games))
        if len(games) >= limit:
            break

    return games[:limit]


def analyse_recent_games(username, limit=5, depth=10):
    # support stockfish on macos and in docker (for later)
    engine_path = os.getenv("STOCKFISH_PATH") or shutil.which("stockfish")
    if not engine_path:
        raise FileNotFoundError(
            "Stockfish was not found. Set STOCKFISH_PATH to its executable path."
        )

    games = get_recent_games(username, limit)
    rows = []

    with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
        for game_number, game in enumerate(games, start=1):
            white = game.headers.get("White", "").lower() == username.lower()
            player_colour = chess.WHITE if white else chess.BLACK
            colour = "White" if white else "Black"
            result = game.headers.get("Result", "*")
            if result == "1/2-1/2":
                my_result = "Draw"
            elif result == "1-0":
                my_result = "Win" if white else "Loss"
            elif result == "0-1":
                my_result = "Loss" if white else "Win"
            else:
                my_result = "Unknown"

            board = game.board()
            game_link = game.headers.get("Link", "")

            for move in game.mainline_moves():
                # only evaluate the user's moves
                if board.turn != player_colour:
                    board.push(move)
                    continue

                played_san = board.san(move)
                position_fen = board.fen()
                move_number = board.fullmove_number

                # classify the position before the move is played
                if move_number <= 12:
                    phase = "Opening"
                elif len(board.piece_map()) <= 12:
                    phase = "Endgame"
                else:
                    phase = "Middlegame"

                # find stockfish's preferred move
                best_analysis = engine.analyse(
                    board, chess.engine.Limit(depth=depth)
                )
                best_line = best_analysis.get("pv", [])
                if not best_line:
                    board.push(move)
                    continue

                best_move = best_line[0]
                best_san = board.san(best_move)

                # do not penalise a move stockfish already considers best
                if move == best_move:
                    board.push(move)
                    continue

                # compare against the move played from the same position
                played_analysis = engine.analyse(
                    board,
                    chess.engine.Limit(depth=depth),
                    root_moves=[move],
                )

                # mate scores are handled separately in a future version
                best_score = best_analysis["score"].pov(player_colour)
                played_score = played_analysis["score"].pov(player_colour)

                board.push(move)

                if best_score.is_mate() or played_score.is_mate():
                    continue

                best_cp = best_score.score()
                played_cp = played_score.score()
                if best_cp is None or played_cp is None:
                    continue

                loss_cp = max(0, best_cp - played_cp)
                if loss_cp < 100:
                    continue

                # classify evaluation losses using chesslab thresholds
                if loss_cp >= 500:
                    category = "Blunder"
                elif loss_cp >= 250:
                    category = "Major Mistake"
                else:
                    category = "Mistake"
                rows.append({
                    "game": game_number,
                    "date": game.headers.get("Date", "Unknown"),
                    "colour": colour,
                    "result": my_result,
                    "move": move_number,
                    "played": played_san,
                    "best": best_san,
                    "category": category,
                    "loss_cp": loss_cp,
                    "fen": position_fen,
                    "phase": phase,
                    "game_link": game_link,
                })

    columns = [
        "game", "date", "colour", "result", "move", "played", "best",
        "category", "loss_cp", "fen", "phase", "game_link",
    ]
    return pd.DataFrame(rows, columns=columns), len(games)


def build_study_plan(mistakes):
    if mistakes.empty:
        return [
            "No moves crossed the current mistake threshold. "
            "Review your closest games and try analysing at a higher depth."
        ]

    priorities = []
    for phase, count in mistakes["phase"].value_counts().items():
        priorities.append(
            f"{phase}: Review {count} significant evaluation drops "
            "and compare your moves with Stockfish suggestions."
        )

    return priorities
