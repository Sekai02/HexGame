import time
import math
import heapq
import random
from hexboard import HexBoard

WINSCORE = 100000
LOSESCORE = -100000
BLOCK_WEIGHT = 100

class Player:
    def __init__(self, player_id: int):
        self.player_id = player_id

    def play(self, board: HexBoard) -> tuple:
        raise NotImplementedError("Implement this method!")

def get_adjacent_positions(row: int, col: int) -> list[tuple[int, int]]:
    directions = [
        (0, -1), 
        (0, 1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (1, -1)
    ]
    return [(row + dr, col + dc) for dr, dc in directions]

def is_valid_position(row: int, col: int, size: int) -> bool:
    return 0 <= row < size and 0 <= col < size

def is_immediate_win(board: HexBoard, row: int, col: int, player_id: int) -> bool:
    board.place_piece(row, col, player_id)
    win = board.check_connection(player_id)
    board.board[row][col] = 0
    return win

class MordecaiBot(Player):
    def __init__(self, player_id: int, time_limit=5.0, max_depth=8, aspiration_delta=50):
        super().__init__(player_id)
        self.time_limit = time_limit
        self.max_depth = max_depth
        self.aspiration_delta = aspiration_delta
        self.tt = {}
        self.history = {}
        self.killer = {}
        self.randomize_moves = True

    def play(self, board: HexBoard) -> tuple:
        for move in board.get_possible_moves():
            if is_immediate_win(board, move[0], move[1], self.player_id):
                return move

        start_time = time.time()
        best_move = None
        guess = 0

        self.tt.clear()
        self.history.clear()
        self.killer.clear()

        for depth in range(1, self.max_depth + 1):
            move, score = self.mtd_f(board, depth, guess, start_time, self.aspiration_delta)
            if time.time() - start_time >= self.time_limit:
                break
            best_move = move
            guess = score
        possible_moves = board.get_possible_moves()
        if best_move is None and possible_moves:
            promising_moves = self.get_promising_moves(board)
            return promising_moves[0] if promising_moves else possible_moves[0]
        return best_move

    def mtd_f(self, board: HexBoard, depth: int, initial_guess: float, start_time: float, delta: float) -> tuple:
        g = initial_guess
        lower_bound = -math.inf
        upper_bound = math.inf

        while lower_bound < upper_bound and time.time() - start_time < self.time_limit:
            alpha = g - delta
            beta = g + delta
            move, g_new = self.minimax(board, depth, alpha, beta, True, start_time)
            g = g_new
            if g == alpha:
                upper_bound = g
            elif g == beta:
                lower_bound = g
            else:
                lower_bound = g
                upper_bound = g
        best_move, final_score = self.minimax(board, depth, -math.inf, math.inf, True, start_time)
        return best_move, final_score

    def minimax(self, board: HexBoard, depth: int, alpha: float, beta: float, maximizing: bool, start_time: float) -> tuple:
        if time.time() - start_time >= self.time_limit:
            return (None, self.evaluate(board))
        if depth == 0 or board.check_connection(self.player_id) or board.check_connection(3 - self.player_id):
            return (None, self.evaluate(board))

        alpha_orig, beta_orig = alpha, beta
        board_hash = self.get_board_hash(board)
        if board_hash in self.tt:
            entry = self.tt[board_hash]
            if entry['depth'] >= depth:
                if entry['flag'] == "exact":
                    return (entry.get('move'), entry['value'])
                elif entry['flag'] == "lower":
                    alpha = max(alpha, entry['value'])
                elif entry['flag'] == "upper":
                    beta = min(beta, entry['value'])
                if alpha >= beta:
                    return (entry.get('move'), entry['value'])

        moves = board.get_possible_moves()
        moves = self.order_moves(moves, depth, board)
        best_move = None
        if maximizing:
            max_eval = -math.inf
            for move in moves:
                board.place_piece(move[0], move[1], self.player_id)
                _, eval_val = self.minimax(board, depth - 1, alpha, beta, False, start_time)
                board.board[move[0]][move[1]] = 0
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                    self.history[move] = self.history.get(move, 0) + depth
                alpha = max(alpha, max_eval)
                if beta <= alpha:
                    self.killer[depth] = move
                    break
            flag = "exact"
            if max_eval <= alpha_orig:
                flag = "upper"
            elif max_eval >= beta_orig:
                flag = "lower"
            self.tt[board_hash] = {'value': max_eval, 'depth': depth, 'flag': flag, 'move': best_move}
            return (best_move, max_eval)
        else:
            min_eval = math.inf
            for move in moves:
                board.place_piece(move[0], move[1], 3 - self.player_id)
                _, eval_val = self.minimax(board, depth - 1, alpha, beta, True, start_time)
                board.board[move[0]][move[1]] = 0
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                    self.history[move] = self.history.get(move, 0) + depth
                beta = min(beta, min_eval)
                if beta <= alpha:
                    self.killer[depth] = move
                    break
            flag = "exact"
            if min_eval <= alpha_orig:
                flag = "upper"
            elif min_eval >= beta_orig:
                flag = "lower"
            self.tt[board_hash] = {'value': min_eval, 'depth': depth, 'flag': flag, 'move': best_move}
            return (best_move, min_eval)

    def simulate_move(self, move: tuple, player_id: int, board: HexBoard) -> HexBoard:
        board_clone = board.clone()
        board_clone.place_piece(move[0], move[1], player_id)
        return board_clone

    def order_moves(self, moves: list, depth: int, board: HexBoard) -> list:
        def defensive_score(move):
            board_copy = self.simulate_move(move, 3 - self.player_id, board)
            opp_dist = self.shortest_path_distance(board_copy, 3 - self.player_id)
            return -opp_dist

        killer_move = self.killer.get(depth, None)
        if killer_move in moves:
            moves.remove(killer_move)
            moves.insert(0, killer_move)

        moves.sort(key=lambda m: (self.history.get(m, 0), defensive_score(m)), reverse=True)
        if self.randomize_moves and not moves:
            random.shuffle(moves)
        return moves


    def get_board_hash(self, board: HexBoard):
        return tuple(tuple(row) for row in board.board)

    def get_promising_moves(self, board: HexBoard) -> list:
        size = board.size
        promising = set()
        for r in range(size):
            for c in range(size):
                if board.board[r][c] != 0:
                    for nr, nc in get_adjacent_positions(r, c):
                        if is_valid_position(nr, nc, size) and board.board[nr][nc] == 0:
                            promising.add((nr, nc))
        moves = list(promising) if promising else board.get_possible_moves()
        center = size / 2
        moves.sort(key=lambda m: abs(m[0] - center) + abs(m[1] - center))
        return moves

    def evaluate(self, board: HexBoard) -> float:
        if board.check_connection(self.player_id):
            return WINSCORE
        if board.check_connection(3 - self.player_id):
            return LOSESCORE

        my_dist = self.shortest_path_distance(board, self.player_id)

        opp_dist = self.shortest_path_distance(board, 3 - self.player_id)
        score = (opp_dist - my_dist) * 50

        my_second = self.two_distance(board, self.player_id)
        opp_second = self.two_distance(board, 3 - self.player_id)
        score += (opp_second - my_second) * 20

        block_bonus = self.blocking_bonus(board)
        score += BLOCK_WEIGHT * block_bonus

        connectivity_bonus = 0
        center = board.size / 2
        for row in range(board.size):
            for col in range(board.size):
                if board.board[row][col] == self.player_id:
                    connectivity_bonus += 5 / (1 + abs(row - center) + abs(col - center))
                elif board.board[row][col] == (3 - self.player_id):
                    connectivity_bonus -= 5 / (1 + abs(row - center) + abs(col - center))
        score += connectivity_bonus

        return score

    def blocking_bonus(self, board: HexBoard) -> float:
        opp_dist = self.shortest_path_distance(board, 3 - self.player_id)
        return opp_dist / 100

    def shortest_path_distance(self, board: HexBoard, player_id: int) -> float:
        size = board.size
        visited = [[False] * size for _ in range(size)]
        heap = []
        if player_id == 1:
            for row in range(size):
                if board.board[row][0] in [0, player_id]:
                    heapq.heappush(heap, (0, row, 0))
        else:
            for col in range(size):
                if board.board[0][col] in [0, player_id]:
                    heapq.heappush(heap, (0, 0, col))
        while heap:
            cost, r, c = heapq.heappop(heap)
            if visited[r][c]:
                continue
            visited[r][c] = True
            if (player_id == 1 and c == size - 1) or (player_id == 2 and r == size - 1):
                return cost
            for nr, nc in get_adjacent_positions(r, c):
                if is_valid_position(nr, nc, size) and not visited[nr][nc]:
                    if board.board[nr][nc] in [0, player_id]:
                        heapq.heappush(heap, (cost + 1, nr, nc))
        return math.inf

    def two_distance(self, board: HexBoard, player_id: int) -> float:
        base = self.shortest_path_distance(board, player_id)
        discount = 0
        for move in board.get_possible_moves():
            count = 0
            for nr, nc in get_adjacent_positions(move[0], move[1]):
                if is_valid_position(nr, nc, board.size) and board.board[nr][nc] == player_id:
                    count += 1
            if count >= 2:
                discount += 0.5
        return base + discount
