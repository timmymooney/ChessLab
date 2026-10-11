import chess
import chess.engine
import chess.pgn
import pandas as pd


STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"


def analyse_position(fen: str, depth: int = 15) -> dict:
    """Analyse a chess position using Stockfish."""
    board = chess.Board(fen)

    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        result = engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
        )

    return result


def analyse_game_moves(
    game: chess.pgn.Game,
    engine: chess.engine.SimpleEngine,
    depth: int = 10,
) -> pd.DataFrame:
    """Analyse each move and the resulting position in a chess game."""
    board = game.board()
    rows = []

    for move in game.mainline_moves():
        move_number = board.fullmove_number
        side_to_move = "White" if board.turn == chess.WHITE else "Black"
        move_san = board.san(move)

        # evaluate the position before the move
        before = engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
        )
        eval_before = before["score"].white().score(mate_score=10000)

        # play the move and evaluate the resulting position
        board.push(move)

        after = engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
        )
        eval_after = after["score"].white().score(mate_score=10000)

        rows.append(
            {
                "move_number": move_number,
                "player": side_to_move,
                "move": move_san,
                "eval_before_white": eval_before / 100,
                "eval_after_white": eval_after / 100,
                "evaluation_change_white": (eval_after - eval_before) / 100,
            }
        )

    return pd.DataFrame(rows)
