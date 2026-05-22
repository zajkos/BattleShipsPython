import socket
import threading
import json
import psycopg2
import os
import logging
import random
import string
import time
from dotenv import load_dotenv
import bcrypt

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

# --- ZABEZPIECZENIE PRZED PODWÓJNYM LOGOWANIEM ---
logged_in_users = set()  # Przechowuje user_id zalogowanych aktualnie graczy

def turn_timer_thread():
    """Wątek monitorujący czas na ruch w pokojach."""
    while True:
        try:
            rooms_to_check = list(rooms.items())
            for code, room in rooms_to_check:
                # Sprawdzamy tylko pokoje w fazie bitwy (gdzie obaj gotowi i gra trwa)
                if room["players"][0] and room["players"][0].get("ready") and \
                   room["players"][1] and room["players"][1].get("ready"):
                    
                    if room["last_action_time"] == 0:
                        room["last_action_time"] = time.time()
                        continue
                    
                    # Jeśli minęło więcej niż 35 sekund od ostatniej akcji
                    if time.time() - room["last_action_time"] > 35:
                        # Timeout! Zmiana tury.
                        room["turn"] = 1 - room["turn"]
                        room["last_action_time"] = time.time()
                        
                        msg = json.dumps({
                            "status": "turn_timeout",
                            "next_turn": room["turn"],
                            "message": "Czas minął! Zmiana tury."
                        })
                        try:
                            room["players"][0]["conn"].sendall(str.encode(msg))
                            room["players"][1]["conn"].sendall(str.encode(msg))
                        except:
                            pass
            time.sleep(1)
        except Exception as e:
            logging.error(f"Błąd w turn_timer_thread: {e}")
            time.sleep(2)

# Uruchomienie wątku timera
timer_t = threading.Thread(target=turn_timer_thread, daemon=True)
timer_t.start()


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


def create_game_state(conn, username, db_user_id, is_private=False):
    return {
        "players": [
            {"conn": conn, "username": username, "user_id": db_user_id, "ready": False},
            None
        ],
        "turn": 0,
        "boards": [{}, {}],
        "scores": [0, 0],
        "hits": [set(), set()],
        "last_action_time": 0,  # Do obsługi timera tury
        "rematch_votes": [False, False],  # Do systemu rewanżu
        "is_private": is_private
    }


def handle_client(conn, player_id):
    logging.info(f"Klient {player_id} połączył się z serwerem (oczekiwanie na logowanie).")

    db_conn = get_db_connection()
    db_cursor = db_conn.cursor() if db_conn else None
    username = f"Nieznajomy_{player_id}"
    current_room_code = None
    current_db_user_id = None  # Przechowuje ID z bazy danych w celu usunięcia z sesji po wyjściu
    global waiting_random_player

    conn.send(str.encode(json.dumps({"status": "connected", "message": "Połączono. Zaloguj się."})))

    try:
        while True:
            data = conn.recv(8192).decode('utf-8')
            if not data:
                break

            if current_room_code is None:
                for code, r_data in rooms.items():
                    if r_data["players"][0] and r_data["players"][0]["conn"] == conn:
                        current_room_code = code
                        break
                    elif r_data["players"][1] and r_data["players"][1]["conn"] == conn:
                        current_room_code = code
                        break

            messages = data.replace("}{", "}SPLIT{").split("SPLIT")

            for msg_str in messages:
                if not msg_str.strip():
                    continue

                request = json.loads(msg_str)
                action = request.get("action")

                if action == "register":
                    req_username = request.get("username")
                    password = request.get("password").encode('utf-8')
                    hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

                    try:
                        if not db_conn:
                            db_conn = get_db_connection()
                            db_cursor = db_conn.cursor()

                        db_cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                                          (req_username, hashed_pw))
                        db_conn.commit()
                        conn.sendall(str.encode(json.dumps({"status": "success", "message": "Zarejestrowano!"})))
                        logging.info(f"Zarejestrowano nowego gracza: {req_username}")

                    except psycopg2.IntegrityError:
                        db_conn.rollback()
                        conn.sendall(str.encode(json.dumps({"status": "error", "message": "Login jest już zajęty!"})))
                    except Exception as e:
                        if db_conn: db_conn.rollback()
                        logging.error(f"Błąd rejestracji gracza {req_username}: {e}")
                        conn.sendall(str.encode(json.dumps({"status": "error", "message": "Błąd bazy danych."})))


                elif action == "login":
                    req_username = request.get("username")
                    password = request.get("password").encode('utf-8')

                    try:
                        if not db_cursor:
                            db_conn = get_db_connection()
                            db_cursor = db_conn.cursor() if db_conn else None

                        if db_cursor:
                            db_cursor.execute("SELECT user_id, password_hash FROM users WHERE username = %s",
                                              (req_username,))
                            result = db_cursor.fetchone()

                            if result:
                                db_user_id = result[0]
                                stored_hash = result[1].encode('utf-8')

                                if bcrypt.checkpw(password, stored_hash):
                                    # --- NOWOŚĆ: Zabezpieczenie przed wielokrotnym logowaniem ---
                                    if db_user_id in logged_in_users:
                                        conn.sendall(str.encode(json.dumps(
                                            {"status": "error", "message": "Konto jest aktualnie w użyciu!"})))
                                    else:
                                        username = req_username
                                        current_db_user_id = db_user_id
                                        logged_in_users.add(db_user_id)  # Oznaczamy jako zalogowanego w sesji serwera

                                        conn.sendall(str.encode(json.dumps({
                                            "status": "success",
                                            "message": "Zalogowano!",
                                            "user_id": db_user_id
                                        })))
                                        logging.info(
                                            f"Gracz '{username}' (DB ID: {db_user_id}) zalogował się pomyślnie.")
                                else:
                                    conn.sendall(
                                        str.encode(json.dumps({"status": "error", "message": "Błędne hasło!"})))
                            else:
                                conn.sendall(
                                    str.encode(json.dumps({"status": "error", "message": "Użytkownik nie istnieje!"})))
                        else:
                            conn.sendall(
                                str.encode(json.dumps({"status": "error", "message": "Brak połączenia z bazą!"})))

                    except Exception as e:
                        if db_conn: db_conn.rollback()
                        logging.error(f"Błąd logowania gracza {req_username}: {e}")
                        conn.sendall(
                            str.encode(json.dumps({"status": "error", "message": "Błąd serwera bazy danych."})))

                elif action == "get_high_scores":
                    try:
                        if not db_cursor:
                            db_conn = get_db_connection()
                            db_cursor = db_conn.cursor() if db_conn else None

                        if db_cursor:
                            db_cursor.execute("""
                                SELECT 
                                    u.username, 
                                    MAX(s.points) as best_score, 
                                    SUM(CASE WHEN s.is_winner = TRUE THEN 1 ELSE 0 END) as wins,
                                    SUM(CASE WHEN s.is_winner = FALSE THEN 1 ELSE 0 END) as losses,
                                    ROUND(AVG(s.points), 2) as avg_points
                                FROM users u
                                JOIN scores s ON u.user_id = s.user_id
                                GROUP BY u.user_id, u.username
                                ORDER BY best_score DESC
                                LIMIT 100
                            """)
                            rows = db_cursor.fetchall()
                            scores_data = []
                            for row in rows:
                                scores_data.append({
                                    "username": row[0],
                                    "best_score": row[1],
                                    "wins": int(row[2]),
                                    "losses": int(row[3]),
                                    "avg_points": float(row[4])
                                })
                            conn.sendall(str.encode(json.dumps({"status": "success", "data": scores_data})))
                        else:
                            conn.sendall(str.encode(json.dumps({"status": "error", "message": "Brak połączenia z bazą!"})))
                    except Exception as e:
                        logging.error(f"Błąd pobierania rankingu: {e}")
                        conn.sendall(str.encode(json.dumps({"status": "error", "message": "Błąd bazy danych."})))

                elif action == "create_room":
                    room_code = generate_room_code()
                    rooms[room_code] = create_game_state(conn, username, current_db_user_id, is_private=True)
                    current_room_code = room_code

                    logging.info(f"Gracz {username} stworzył pokój: {room_code}")
                    conn.sendall(str.encode(json.dumps({"status": "room_created", "room_code": room_code})))

                elif action == "join_room":
                    target_code = request.get("room_code")
                    if target_code in rooms and rooms[target_code]["players"][1] is None:
                        rooms[target_code]["players"][1] = {"conn": conn, "username": username, "user_id": current_db_user_id, "ready": False}
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
                        waiting_random_player = {"conn": conn, "username": username, "user_id": current_db_user_id, "player_id": player_id}
                        logging.info(f"Gracz {username} szuka losowej gry...")
                        conn.sendall(str.encode(json.dumps({"status": "waiting"})))
                    else:
                        if waiting_random_player["player_id"] == player_id:
                            continue

                        room_code = generate_room_code()
                        p1 = waiting_random_player

                        rooms[room_code] = create_game_state(p1["conn"], p1["username"], p1["user_id"])
                        rooms[room_code]["players"][1] = {"conn": conn, "username": username, "user_id": current_db_user_id, "ready": False}
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
                        sunk = False
                        sunk_cells = []

                        for ship in opp_board:
                            cells = [tuple(c) for c in ship["cells"]]
                            if (x, y) in cells:
                                hit = True
                                room["hits"][opp_idx].add((x, y))

                                # Sprawdzanie, czy CAŁY statek zatonął
                                is_sunk = all(c in room["hits"][opp_idx] for c in cells)
                                if is_sunk:
                                    sunk = True
                                    sunk_cells = list(cells)
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
                        room["last_action_time"] = time.time()
                        if hit:
                            room["scores"][player_idx] += points_gained if sunk else 50
                            room["scores"][opp_idx] -= points_lost if sunk else 10
                        else:
                            room["turn"] = opp_idx
                            room["scores"][player_idx] -= 10  # Kara za pudło

                        shot_result = {
                            "status": "shot_result",
                            "x": x,
                            "y": y,
                            "hit": hit,
                            "sunk": sunk,
                            "sunk_cells": sunk_cells,
                            "shooter": player_idx,
                            "next_turn": room["turn"],
                            "scores": room["scores"]
                        }

                        msg = str.encode(json.dumps(shot_result))
                        try:
                            room["players"][0]["conn"].sendall(msg)
                            room["players"][1]["conn"].sendall(msg)
                        except:
                            pass

                        # --- SPRAWDZANIE KOŃCA GRY (18 trafień = wygrana) ---
                        if len(room["hits"][opp_idx]) == 18:
                            winner = room["players"][player_idx]
                            loser = room["players"][opp_idx]

                            try:
                                if not db_cursor:
                                    db_conn = get_db_connection()
                                    db_cursor = db_conn.cursor() if db_conn else None

                                if db_cursor:
                                    db_cursor.execute(
                                        "INSERT INTO matches (player1_id, player2_id, winner_id) VALUES (%s, %s, %s) RETURNING match_id",
                                        (room["players"][0]["user_id"], room["players"][1]["user_id"], winner["user_id"])
                                    )
                                    match_id = db_cursor.fetchone()[0]

                                    db_cursor.execute(
                                        "INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                                        (winner["user_id"], match_id, room["scores"][player_idx], True)
                                    )
                                    db_cursor.execute(
                                        "INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                                        (loser["user_id"], match_id, room["scores"][opp_idx], False)
                                    )
                                    db_conn.commit()
                                    logging.info(f"Mecz {match_id} zapisany. Zwycięzca: {winner['username']}")
                            except Exception as db_e:
                                logging.error(f"Błąd zapisu meczu: {db_e}")
                                if db_conn: db_conn.rollback()

                            over_msg = json.dumps({
                                "status": "game_over",
                                "winner": winner["username"],
                                "final_scores": room["scores"]
                            })
                            try:
                                room["players"][0]["conn"].sendall(str.encode(over_msg))
                                room["players"][1]["conn"].sendall(str.encode(over_msg))
                            except:
                                pass

                elif action == "request_rematch":
                    if current_room_code and current_room_code in rooms:
                        room = rooms[current_room_code]
                        player_idx = 0 if room["players"][0]["conn"] == conn else 1
                        room["rematch_votes"][player_idx] = True

                        opp_idx = 1 - player_idx
                        if room["rematch_votes"][opp_idx]:
                            # Obaj chcą rewanżu! Resetujemy pokój.
                            logging.info(f"Rewanż w pokoju {current_room_code}!")
                            room["turn"] = random.randint(0, 1)
                            room["scores"] = [0, 0]
                            room["hits"] = [set(), set()]
                            room["boards"] = [{}, {}]
                            room["players"][0]["ready"] = False
                            room["players"][1]["ready"] = False
                            room["rematch_votes"] = [False, False]

                            rematch_msg = json.dumps({"status": "rematch_start"})
                            try:
                                room["players"][0]["conn"].sendall(str.encode(rematch_msg))
                                room["players"][1]["conn"].sendall(str.encode(rematch_msg))
                            except:
                                pass
                        else:
                            # Powiadom przeciwnika o prośbie
                            try:
                                room["players"][opp_idx]["conn"].sendall(str.encode(json.dumps({
                                    "status": "rematch_requested"
                                })))
                            except:
                                pass

                elif action == "chat_message":
                    if current_room_code and current_room_code in rooms:
                        room = rooms[current_room_code]
                        player_idx = 0 if (room["players"][0] and room["players"][0]["conn"] == conn) else 1
                        opp_idx = 1 - player_idx
                        
                        if room["players"][opp_idx]:
                            msg = json.dumps({
                                "status": "chat_message",
                                "sender": username,
                                "message": request.get("message")
                            })
                            try:
                                room["players"][opp_idx]["conn"].sendall(str.encode(msg))
                            except:
                                pass

                elif action == "surrender":
                    if current_room_code and current_room_code in rooms:
                        room = rooms[current_room_code]
                        player_idx = 0 if (room["players"][0] and room["players"][0]["conn"] == conn) else 1
                        opp_idx = 1 - player_idx
                        opponent = room["players"][opp_idx]

                        if opponent:
                            logging.info(f"Gracz {username} poddał się. Zwycięstwo dla {opponent['username']}")
                            
                            # Zapis do bazy danych
                            try:
                                if not db_cursor:
                                    db_conn = get_db_connection()
                                    db_cursor = db_conn.cursor() if db_conn else None
                                
                                if db_cursor:
                                    winner = opponent
                                    loser = room["players"][player_idx]
                                    
                                    db_cursor.execute(
                                        "INSERT INTO matches (player1_id, player2_id, winner_id) VALUES (%s, %s, %s) RETURNING match_id",
                                        (room["players"][0]["user_id"], room["players"][1]["user_id"], winner["user_id"])
                                    )
                                    match_id = db_cursor.fetchone()[0]
                                    
                                    db_cursor.execute(
                                        "INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                                        (winner["user_id"], match_id, room["scores"][opp_idx], True)
                                    )
                                    db_cursor.execute(
                                        "INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                                        (loser["user_id"], match_id, room["scores"][player_idx], False)
                                    )
                                    db_conn.commit()
                            except Exception as db_e:
                                logging.error(f"Błąd zapisu poddania: {db_e}")
                                if db_conn: db_conn.rollback()

                            over_msg = json.dumps({
                                "status": "game_over",
                                "winner": opponent["username"],
                                "final_scores": room["scores"],
                                "message": f"Przeciwnik ({username}) poddał się!"
                            })
                            try:
                                opponent["conn"].sendall(str.encode(over_msg))
                            except:
                                pass
                        
                        # Pokój zostanie usunięty w bloku finally po wyjściu gracza z pętli
                        break

    except Exception as e:
        logging.error(f"Błąd połączenia klienta (ID:{player_id}): {e}")

    finally:
        logging.info(f"Zamykanie połączenia: Klient {player_id}.")

        # --- NOWOŚĆ: Usuwamy gracza z aktywnych sesji po wyjściu z gry ---
        if current_db_user_id and current_db_user_id in logged_in_users:
            logged_in_users.remove(current_db_user_id)

        if waiting_random_player and waiting_random_player["player_id"] == player_id:
            waiting_random_player = None

        if current_room_code and current_room_code in rooms:
            room = rooms[current_room_code]
            opponent_idx = -1
            player_idx = -1
            
            if room["players"][0] and room["players"][0]["conn"] == conn:
                player_idx = 0
                opponent_idx = 1
            elif room["players"][1] and room["players"][1]["conn"] == conn:
                player_idx = 1
                opponent_idx = 0

            if opponent_idx != -1 and room["players"][opponent_idx]:
                opponent = room["players"][opponent_idx]
                opponent_conn = opponent["conn"]
                
                # Jeśli trwała bitwa (obaj byli gotowi) i nikt jeszcze nie wygrał
                if room["players"][0].get("ready") and room["players"][1].get("ready") and \
                   len(room["hits"][0]) < 18 and len(room["hits"][1]) < 18:
                    
                    logging.info(f"Gracz {username} uciekł z bitwy. Przyznaję zwycięstwo: {opponent['username']}")
                    
                    # Zapisujemy walkower do bazy danych
                    try:
                        if not db_cursor:
                            db_conn = get_db_connection()
                            db_cursor = db_conn.cursor() if db_conn else None

                        if db_cursor:
                            # Gracz który został jest zwycięzcą
                            winner = opponent
                            loser = room["players"][player_idx]

                            db_cursor.execute(
                                "INSERT INTO matches (player1_id, player2_id, winner_id) VALUES (%s, %s, %s) RETURNING match_id",
                                (room["players"][0]["user_id"], room["players"][1]["user_id"], winner["user_id"])
                            )
                            match_id = db_cursor.fetchone()[0]

                            db_cursor.execute(
                                "INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                                (winner["user_id"], match_id, room["scores"][opponent_idx], True)
                            )
                            db_cursor.execute(
                                "INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                                (loser["user_id"], match_id, room["scores"][player_idx], False)
                            )
                            db_conn.commit()
                            logging.info(f"Walkower (Mecz {match_id}) zapisany.")
                    except Exception as db_e:
                        logging.error(f"Błąd zapisu walkowera: {db_e}")
                        if db_conn: db_conn.rollback()

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