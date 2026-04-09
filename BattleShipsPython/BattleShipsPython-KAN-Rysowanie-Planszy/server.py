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
connected_clients = {}  # Klienci aktualnie podłączeni (po ID)
rooms = {}  # Pokoje gier
waiting_random_player = None  # Gracz czekający na szybką grę


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
            None  # Miejsce dla drugiego gracza
        ],
        "turn": 0,
        "boards": [{}, {}],
        "scores": [0, 0]
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
            data = conn.recv(2048).decode('utf-8')
            if not data:
                break

            request = json.loads(data)
            action = request.get("action")

            # --- LOGOWANIE ---
            if action == "join":
                username = request.get("name", username)
                logging.info(f"Gracz '{username}' (ID: {player_id}) wszedł do gry.")
                conn.sendall(str.encode(json.dumps({"status": "joined", "message": f"Witaj {username}!"})))

            # --- TWORZENIE POKOJU ---
            elif action == "create_room":
                room_code = generate_room_code()
                rooms[room_code] = create_game_state(conn, username)
                current_room_code = room_code

                logging.info(f"Gracz {username} stworzył pokój: {room_code}")
                conn.sendall(str.encode(json.dumps({"status": "room_created", "room_code": room_code})))

            # --- DOŁĄCZANIE DO POKOJU ---
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
                    conn.sendall(str.encode(json.dumps({"status": "error", "message": "Błędny kod lub pokój pełny."})))

            # --- SZYBKA GRA ---
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

    except Exception as e:
        logging.error(f"Błąd gracza {username} ({player_id}): {e}")

    finally:
        logging.info(f"Zamykanie połączenia: {username} ({player_id}).")

        # Jeśli gracz czekał na szybką grę i wyszedł
        if waiting_random_player and waiting_random_player["player_id"] == player_id:
            waiting_random_player = None

        # Jeśli grał w pokoju, powiadamiamy przeciwnika
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
            del rooms[current_room_code]  # Usuwamy pokój

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