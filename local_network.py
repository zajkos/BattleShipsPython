import json
import random
import pygame
from ai_opponent import AIOpponent

class LocalNetwork:
    """Mock network class for singleplayer mode against AI."""
    def __init__(self):
        self.ai = AIOpponent()
        self.ai_board = self.ai.place_ships()
        self.player_board = None
        self.player_name = "Gracz"
        self.opponent_name = "Komputer"
        self.turn = 0 # 0 for player, 1 for AI
        self.hits = [set(), set()] # hits[0] are hits ON player, hits[1] are hits ON AI
        self.scores = [0, 0]
        self.is_singleplayer = True
        self._message_buffer = []
        self.last_ai_action_time = 0
        self.ai_delay = 1500 # 1.5 seconds delay for AI move
        
        # Mocking the socket client
        self.client = self # So net.client.setblocking(False) doesn't fail

    def setblocking(self, mode):
        pass

    def send(self, data):
        """Processes synchronous requests."""
        action = data.get("action")
        if action == "random_match" or action == "create_room":
            return {"status": "game_start", "opponent": self.opponent_name}
        return {"status": "success"}

    def send_no_wait(self, data):
        """Processes asynchronous requests."""
        action = data.get("action")
        if action == "player_ready":
            self.player_board = data.get("board")
            # Start battle
            self.turn = random.randint(0, 1)
            msg = json.dumps({
                "status": "battle_start",
                "your_idx": 0,
                "starting_turn": self.turn
            })
            self._queue_message(msg)
            if self.turn == 1:
                self.last_ai_action_time = pygame.time.get_ticks()
        elif action == "shoot":
            x, y = data.get("x"), data.get("y")
            response = self._process_shot(x, y, 0)
            self._queue_message(response.decode())
            if self.turn == 1:
                self.last_ai_action_time = pygame.time.get_ticks()
        elif action == "request_rematch":
            # AI always accepts rematch
            self.ai = AIOpponent()
            self.ai_board = self.ai.place_ships()
            self.hits = [set(), set()]
            self.scores = [0, 0]
            self.turn = random.randint(0, 1)
            self._queue_message(json.dumps({"status": "rematch_start"}))
            if self.turn == 1:
                self.last_ai_action_time = pygame.time.get_ticks()

    def _queue_message(self, msg):
        self._message_buffer.append(msg)

    def recv(self, size):
        # First check if we have queued messages
        if self._message_buffer:
            msg = self._message_buffer.pop(0)
            return str.encode(msg)
        
        # If it's AI's turn, make a move after delay
        if self.turn == 1:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_ai_action_time > self.ai_delay:
                move_x, move_y = self.ai.get_move()
                response = self._process_shot(move_x, move_y, 1)
                return response

        return b""

    def _process_shot(self, x, y, shooter_idx):
        opp_idx = 1 - shooter_idx
        opp_board = self.ai_board if opp_idx == 1 else self.player_board
        
        hit = False
        sunk = False
        sunk_cells = []
        points_gained = 0
        points_lost = 0

        for ship in opp_board:
            cells = [tuple(c) for c in ship["cells"]]
            if (x, y) in cells:
                hit = True
                self.hits[opp_idx].add((x, y))
                is_sunk = all(c in self.hits[opp_idx] for c in cells)
                if is_sunk:
                    sunk = True
                    sunk_cells = list(cells)
                    length = len(cells)
                    if length == 4: points_gained, points_lost = 500, 250
                    elif length == 3: points_gained, points_lost = 400, 200
                    elif length == 2: points_gained, points_lost = 200, 100
                    elif length == 1: points_gained, points_lost = 100, 50
                break

        if hit:
            self.scores[shooter_idx] += points_gained if sunk else 50
            self.scores[opp_idx] -= points_lost if sunk else 10
        else:
            self.turn = opp_idx
            self.scores[shooter_idx] -= 10

        if shooter_idx == 1: # AI shot
            self.ai.process_result(x, y, hit, sunk, sunk_cells)

        shot_result = {
            "status": "shot_result",
            "x": x,
            "y": y,
            "hit": hit,
            "sunk": sunk,
            "sunk_cells": sunk_cells,
            "shooter": shooter_idx,
            "next_turn": self.turn,
            "scores": self.scores
        }

        # Check for game over
        if len(self.hits[opp_idx]) == 18:
            winner_name = self.player_name if shooter_idx == 0 else self.opponent_name
            over_msg = {
                "status": "game_over",
                "winner": winner_name,
                "final_scores": self.scores
            }
            # Queue game over message after shot result
            self._queue_message(json.dumps(over_msg))

        return str.encode(json.dumps(shot_result))
