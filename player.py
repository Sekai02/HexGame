import time
import math
import heapq
from hexboard import HexBoard

WINSCORE = 10000
LOSESCORE = -10000

class Player:
    def __init__(self, player_id: int):
        self.player_id = player_id

    def play(self, board: HexBoard) -> tuple:
        raise NotImplementedError("Implement this method!")

def get_adjacent_positions(row: int, col: int) -> list[tuple[int, int]]:
    """Utility function para retornar una lista de las posiciones adyacentes a la posición (row, col)"""
    directions = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (1, -1)
    ]
    adjacent = [(row + dr, col + dc) for dr, dc in directions]
    
    return adjacent

def is_valid_position(row: int, col: int, size: int) -> bool:
    """Utility function para verificar si una posición es válida dentro del tablero"""
    return 0 <= row < size and 0 <= col < size

class MordecaiBot(Player):
    # Si se comporta demasiado lento modificar los parametros time_limit y max_depth 
    # (max_depth = 3 recomendado para mayor velocidad, y/o time_limit=5.0)
    # Es recomendado dejar estos parametros como están para mejor tradeoff
    def __init__(self, player_id: int, time_limit=10.0, max_depth=4):
        super().__init__(player_id)
        self.time_limit = time_limit
        self.max_depth = max_depth

    def play(self, board: HexBoard) -> tuple:
        start_time = time.time()
        best_move, _ = self.minimax(board, self.max_depth, -math.inf, math.inf, True, start_time)
        possible_moves = board.get_possible_moves()
        if best_move is None and possible_moves:
            promising_moves = self.get_promising_moves(board)
            return promising_moves[0] if promising_moves else possible_moves[0]
        return best_move

    def minimax(self, board: HexBoard, depth: int, alpha: float, beta: float,
                maximizing: bool, start_time: float) -> tuple:
        if time.time() - start_time >= self.time_limit:
            return (None, self.evaluate(board))
        
        if depth == 0 or board.check_connection(self.player_id) or board.check_connection(3 - self.player_id):
            return (None, self.evaluate(board))

        best_move = None
        if maximizing:
            max_eval = -math.inf
            
            for move in board.get_possible_moves():
                board.place_piece(move[0], move[1], self.player_id)
                _, eval_val = self.minimax(board, depth - 1, alpha, beta, False, start_time)
                board.board[move[0]][move[1]] = 0
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, max_eval)
                if beta <= alpha:
                    break
            return (best_move, max_eval)
        else:
            min_eval = math.inf
            for move in board.get_possible_moves():
                board.place_piece(move[0], move[1], 3 - self.player_id)
                _, eval_val = self.minimax(board, depth - 1, alpha, beta, True, start_time)
                board.board[move[0]][move[1]] = 0
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, min_eval)
                if beta <= alpha:
                    break
            return (best_move, min_eval)

    def evaluate(self, board: HexBoard) -> float:
        
        if board.check_connection(self.player_id):
            return WINSCORE
        if board.check_connection(3 - self.player_id):
            return LOSESCORE

        my_distance = self.shortest_path_distance(board, self.player_id)
        opp_distance = self.shortest_path_distance(board, 3 - self.player_id)
        
        score = (opp_distance - my_distance) * 50

        my_second = self.two_distance(board, self.player_id)
        opp_second = self.two_distance(board, 3 - self.player_id)
        score += (opp_second - my_second) * 20

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

    def get_promising_moves(self, board: HexBoard):
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
