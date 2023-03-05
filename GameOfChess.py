import chess
import chess.engine
import chess.polyglot
import chess.pgn
import time
# noinspection PyUnresolvedReferences
import asyncio


class GameOfChess:

    def __init__(self, engine_path, suggestion_engine_path, engine_limit=chess.engine.Limit(time=0.1),
                 suggestion_limit=chess.engine.Limit(time=1.5),
                 suggestion_book_path="/usr/share/scid/books/Elo2400.bin") -> None:
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.engine_suggest = chess.engine.SimpleEngine.popen_uci(suggestion_engine_path)
        self.suggestion_book = suggestion_book_path
        self.limit = engine_limit
        self.limit_sug = suggestion_limit
        self.engine.configure({'UCI_LimitStrength': True, 'UCI_Elo': 600, 'OwnBook': True})
        self.checkmate = False
        self.engines_running = True
        self.eco_pgn = chess.pgn.Game()
        self.init_eco_file()

    async def get_cpu_move(self, board):
        return self.engine.play(board, self.limit)

    async def get_score(self, board):
        score = self.engine_suggest.analyse(board, self.limit_sug).get('score')
        return score.pov(True)  # returns score in cp relative to white -> always

    async def get_move_suggestion(self, board):
        move = self.get_book_move(board)
        if not move:
            print("Engine move")
            move = self.engine.play(board, self.limit_sug).move
        return f"{move}"  # ex "e3e4"

    def get_book_move(self, board):
        with chess.polyglot.open_reader(self.suggestion_book) as reader:
            try:
                move = reader.weighted_choice(board)
                print(move)
                return move.move
            except IndexError:
                return None

    def quit_chess_engines(self):
        if self.engines_running:
            self.engine.quit()
            self.engine_suggest.quit()
            self.engines_running = False

    def write_to_pgn(self, board):
        cur_time = time.localtime()
        day_str = f'{cur_time.tm_year}.{cur_time.tm_mon:02}.{cur_time.tm_mday:02}'
        time_str = f"{day_str}_{cur_time.tm_hour}_{cur_time.tm_min}"
        game = chess.pgn.Game()
        # noinspection SpellCheckingInspection
        game.headers["Event"] = "VakantOS"
        game.headers["Date"] = day_str
        if board.player_color:
            game.headers["White"] = "Rudi"
            game.headers["Black"] = str(self.engine.id["name"])
        else:
            game.headers["Black"] = "Rudi"
            game.headers["White"] = str(self.engine.id["name"])
        res = board.board.result()
        if res == '*':
            if board.winner == chess.WHITE:
                res = '1-0'
            elif board.winner == chess.BLACK:
                res = '0-1'
            else:
                res = '1/2-1/2'
        game.headers["Result"] = res
        if len(board.board.move_stack) == 0:
            print("No PGN Written")
            return
        move = board.board.move_stack.pop(0)
        node = game.add_main_variation(move)
        for move in board.board.move_stack:
            node = node.add_main_variation(move)
        print(game, file=open(f"/home/rudi/Desktop/{time_str}.pgn", 'w'), end="\n\n")
        print("PGN written")

    def init_eco_file(self, ):
        """
        read the eco file with format:
        'E94    1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Nf3 O-O 6. Be2 e5 7. O-O "King's Indian, Classical Variation"'
        and fill self.eco_pgn with the moves and names
        """
        with open("eco", "rt") as eco_file:
            eco_line = eco_file.readline()
            while eco_line:
                split = eco_line.split('"')
                name = split[1] if len(split) > 1 else ""
                rest = split[0]
                split = rest.split(' ')
                code = split[0]
                moves = list(filter(lambda m: len(m) > 1 and '.' not in m, split[1:]))
                b = chess.Board()
                uci_moves = list(map(lambda m: b.push_san(m.strip()), moves))
                cur_var = self.eco_pgn
                for i, cur_move in enumerate(uci_moves):
                    id_string = f'({name}, {code})\n'
                    if cur_var.has_variation(cur_move):
                        if id_string not in cur_var.variation(cur_move).comment:
                            if len(uci_moves) == i+1:  # if it ends here put it on the front of the string
                                cur_var.variation(cur_move).comment =\
                                    f'{id_string}\n{cur_var.variation(cur_move).comment}'
                            else:
                                cur_var.variation(cur_move).comment += id_string

                    else:
                        cur_var.add_variation(cur_move).comment = id_string
                    cur_var = cur_var.variation(cur_move)
                eco_line = eco_file.readline()
