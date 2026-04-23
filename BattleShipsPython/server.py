import socket
import threading
import json
import psycopg2
import os
import logging
import random
import string
from dotenv import load_dotenv

# --- KONFIGURACJA LOGOWANIA ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

load_dotenv()

# --- KONFIGURACJA SERWERA ---
HOST = '127.0.0.1'
PORT = 5555

# --- KONFIGURACJA BAZY DANYCH ---
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# --- STAN GRY I MATCHMAKING ---
connected_clients = {}
rooms = {}
waiting_random_player = None


def get_db_connection():
    try:
        return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    except Exception as e:
        logging.error(f"Nie można połączyć z bazą danych: {e}")
        return None


def generate_room_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if code not in rooms:
            return code


def create_game_state(player1_conn, player1_username):
    return {
        "players": [
            {"conn": player1_conn, "username": player1_username, "ready": False},
            None
        ],
        "turn": 0,
        "boards": [{}, {}],
        "scores": [0, 0],
        "hits": [set(), set()]  # NOWE: Śledzenie trafionych komórek dla obu graczy
    }


def handle_client(conn, player_id):
    logging.info(f"Gracz {player_id} połączył się z serwerem.")

    db_conn = get_db_connection()
    db_cursor = db_conn.cursor() if db_conn else None
    username = f"Nieznajomy_{player_id}"
    current_room_code = None
    global waiting_random_player

    conn.send(str.encode(json.dumps({"status": "connected", "message": "Połączono. Podaj nick."})))

    try:
        while True:
            # Zwiększony bufor i bezpieczne parsowanie TCP
            data = conn.recv(8192).decode('utf-8')
            if not data:
                break
            # --- NAPRAWA BŁĘDU SZYBKIEJ GRY (SYNCHRONIZACJA POKOJU) ---
            # Jeśli zmienna pokoju jest pusta, sprawdzamy, czy inny gracz
            # nie utworzył już dla nas pokoju, gdy czekaliśmy w kolejce.
            if current_room_code is None:
                for code, r_data in rooms.items():
                    if r_data["players"][0] and r_data["players"][0]["conn"] == conn:
                        current_room_code = code
                        break
                    elif r_data["players"][1] and r_data["players"][1]["conn"] == conn:
                        current_room_code = code
                        break
            # Rozdzielanie połączonych JSON-ów w przypadku szybkiego klikania
            messages = data.replace("}{", "}SPLIT{").split("SPLIT")

            for msg_str in messages:
                if not msg_str.strip():
                    continue

                request = json.loads(msg_str)
                action = request.get("action")

                if action == "join":
                    username = request.get("name", username)
                    logging.info(f"Gracz '{username}' (ID: {player_id}) wszedł do gry.")
                    conn.sendall(str.encode(json.dumps({"status": "joined", "message": f"Witaj {username}!"})))

                elif action == "create_room":
                    room_code = generate_room_code()
                    rooms[room_code] = create_game_state(conn, username)
                    current_room_code = room_code

                    logging.info(f"Gracz {username} stworzył pokój: {room_code}")
                    conn.sendall(str.encode(json.dumps({"status": "room_created", "room_code": room_code})))

                elif action == "join_room":
                    target_code = request.get("room_code")
                    if target_code in rooms and rooms[target_code]["players"][1] is None:
                        rooms[target_code]["players"][1] = {"conn": conn, "username": username, "ready": False}
                        current_room_code = target_code
                        logging.info(f"Gracz {username} dołączył do pokoju: {target_code}")

                        start_msg = {"status": "game_start", "opponent": rooms[target_code]["players"][0]["username"]}
                        start_msg_p1 = {"status": "game_start", "opponent": username}

                        conn.sendall(str.encode(json.dumps(start_msg)))
                        rooms[target_code]["players"][0]["conn"].sendall(str.encode(json.dumps(start_msg_p1)))
                    else:
                        conn.sendall(
                            str.encode(json.dumps({"status": "error", "message": "Błędny kod lub pokój pełny."})))

                elif action == "random_match":
                    if waiting_random_player is None:
                        waiting_random_player = {"conn": conn, "username": username, "player_id": player_id}
                        logging.info(f"Gracz {username} szuka losowej gry...")
                        conn.sendall(str.encode(json.dumps({"status": "waiting"})))
                    else:
                        if waiting_random_player["player_id"] == player_id:
                            continue

                        room_code = generate_room_code()
                        p1 = waiting_random_player

                        rooms[room_code] = create_game_state(p1["conn"], p1["username"])
                        rooms[room_code]["players"][1] = {"conn": conn, "username": username, "ready": False}
                        current_room_code = room_code
                        waiting_random_player = None

                        logging.info(f"Matchmaking: {p1['username']} vs {username} (Pokój: {room_code})")

                        start_msg = {"status": "game_start", "opponent": p1["username"]}
                        start_msg_p1 = {"status": "game_start", "opponent": username}

                        conn.sendall(str.encode(json.dumps(start_msg)))
                        p1["conn"].sendall(str.encode(json.dumps(start_msg_p1)))

                elif action == "player_ready":
                    if current_room_code and current_room_code in rooms:
                        room = rooms[current_room_code]
                        board_data = request.get("board")

                        player_idx = 0 if room["players"][0]["conn"] == conn else 1
                        room["players"][player_idx]["ready"] = True
                        room["boards"][player_idx] = board_data

                        logging.info(f"Gracz {username} w pokoju {current_room_code} jest gotowy.")

                        p1 = room["players"][0]
                        p2 = room["players"][1]

                        if p1 and p1.get("ready") and p2 and p2.get("ready"):
                            logging.info(f"Pokój {current_room_code}: Obaj gracze gotowi. Start bitwy!")
                            starting_turn = random.randint(0, 1)
                            room["turn"] = starting_turn

                            msg_p1 = json.dumps(
                                {"status": "battle_start", "your_idx": 0, "starting_turn": starting_turn})
                            msg_p2 = json.dumps(
                                {"status": "battle_start", "your_idx": 1, "starting_turn": starting_turn})

                            try:
                                p1["conn"].sendall(str.encode(msg_p1))
                                p2["conn"].sendall(str.encode(msg_p2))
                            except Exception as e:
                                logging.error(f"Błąd wysyłania startu bitwy: {e}")

                elif action == "shoot":
                    if current_room_code and current_room_code in rooms:
                        room = rooms[current_room_code]
                        player_idx = 0 if room["players"][0]["conn"] == conn else 1

                        if room["turn"] != player_idx:
                            continue

                        x, y = request.get("x"), request.get("y")
                        opp_idx = 1 - player_idx

                        hit = False
                        opp_board = room["boards"][opp_idx]

                        points_gained = 0
                        points_lost = 0

                        for ship in opp_board:
                            cells = [tuple(c) for c in ship["cells"]]
                            if (x, y) in cells:
                                hit = True
                                room["hits"][opp_idx].add((x, y))

                                # Sprawdzanie, czy CAŁY statek zatonął
                                is_sunk = all(c in room["hits"][opp_idx] for c in cells)
                                if is_sunk:
                                    length = len(cells)
                                    if length == 4:
                                        points_gained, points_lost = 500, 250
                                    elif length == 3:
                                        points_gained, points_lost = 400, 200
                                    elif length == 2:
                                        points_gained, points_lost = 200, 100
                                    elif length == 1:
                                        points_gained, points_lost = 100, 50
                                break

                        # Naliczanie punktów i zmiana tur
                        if hit:
                            room["scores"][player_idx] += points_gained
                            room["scores"][opp_idx] -= points_lost
                        else:
                            room["turn"] = opp_idx
                            room["scores"][player_idx] -= 10  # Kara za pudło

                        shot_result = {
                            "status": "shot_result",
                            "x": x,
                            "y": y,
                            "hit": hit,
                            "shooter": player_idx,
                            "next_turn": room["turn"],
                            "scores": room["scores"]  # Wysyłamy stan tabeli wyników
                        }

                        msg = str.encode(json.dumps(shot_result))
                        try:
                            room["players"][0]["conn"].sendall(msg)
                            room["players"][1]["conn"].sendall(msg)
                        except:
                            pass

    except Exception as e:
        logging.error(f"Błąd gracza {username} ({player_id}): {e}")

    finally:
        logging.info(f"Zamykanie połączenia: {username} ({player_id}).")

        if waiting_random_player and waiting_random_player["player_id"] == player_id:
            waiting_random_player = None

        if current_room_code and current_room_code in rooms:
            room = rooms[current_room_code]
            opponent_conn = None
            if room["players"][0] and room["players"][0]["conn"] != conn:
                opponent_conn = room["players"][0]["conn"]
            elif room["players"][1] and room["players"][1]["conn"] != conn:
                opponent_conn = room["players"][1]["conn"]

            if opponent_conn:
                try:
                    opponent_conn.sendall(str.encode(json.dumps({"status": "opponent_disconnected"})))
                except:
                    pass
            del rooms[current_room_code]

        if player_id in connected_clients: del connected_clients[player_id]
        if db_cursor: db_cursor.close()
        if db_conn: db_conn.close()
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((HOST, PORT))
    except socket.error as e:
        logging.critical(f"Błąd startu serwera: {e}")
        return

    server.listen(5)
    logging.info(f"Serwer uruchomiony (Port: {PORT}).")

    test_db = get_db_connection()
    if test_db:
        logging.info("Pomyślnie połączono z bazą PostgreSQL.")
        test_db.close()
    else:
        logging.warning("Brak połączenia z bazą! Opcje bazodanowe będą niedostępne.")

    player_count = 0
    while True:
        conn, addr = server.accept()
        connected_clients[player_count] = conn
        thread = threading.Thread(target=handle_client, args=(conn, player_count))
        thread.start()
        player_count += 1


if __name__ == "__main__":
    start_server()