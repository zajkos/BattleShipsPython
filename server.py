import socket
import threading
import json
import sys
import os

# Obsługa ścieżek dla PyInstallera
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

import psycopg2
from psycopg2 import pool
import os
import logging
import random
import string
import time
import struct
import ssl
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
HOST = os.getenv("SERVER_HOST", '127.0.0.1')
PORT = int(os.getenv("SERVER_PORT", 5555))
USE_SSL = False # Ustaw na True i podaj ścieżki do certyfikatów, aby włączyć TLS

# --- KONFIGURACJA BAZY DANYCH ---
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

try:
    db_pool = pool.SimpleConnectionPool(1, 20, 
        host=DB_HOST, 
        database=DB_NAME, 
        user=DB_USER, 
        password=DB_PASS
    )
    logging.info("Pula połączeń PostgreSQL zainicjalizowana.")
except Exception as e:
    logging.error(f"Nie można zainicjalizować puli połączeń: {e}")
    db_pool = None

# --- STAN GRY I MATCHMAKING ---
rooms = {}
rooms_lock = threading.Lock()
waiting_random_player = None
waiting_random_name = None
waiting_random_id = None
waiting_lock = threading.Lock()

# --- LIMIT POŁĄCZEŃ ---
MAX_CONNECTIONS = 100
current_connections = 0
connections_lock = threading.Lock()

# --- CACHE RANKINGU ---
high_scores_cache = {"data": [], "last_updated": 0}
CACHE_TIMEOUT = 300 # 5 minut

# --- ZABEZPIECZENIE PRZED PODWÓJNYM LOGOWANIEM ---
logged_in_users = set()
auth_lock = threading.Lock()

def get_high_scores_from_db():
    global high_scores_cache
    if time.time() - high_scores_cache["last_updated"] < CACHE_TIMEOUT:
        return high_scores_cache["data"]

    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
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
            rows = cur.fetchall()
            data = []
            for row in rows:
                data.append({
                    "username": row[0],
                    "best_score": row[1],
                    "wins": int(row[2]),
                    "losses": int(row[3]),
                    "avg_points": float(row[4])
                })
            high_scores_cache["data"] = data
            high_scores_cache["last_updated"] = time.time()
            return data
    except Exception as e:
        logging.error(f"Błąd odświeżania cache rankingu: {e}")
        return []
    finally:
        db_pool.putconn(conn)

def send_msg(conn, data):
    """Wysyła wiadomość z prefiksem długości (4 bajty)."""
    try:
        msg = json.dumps(data).encode('utf-8')
        length = struct.pack('!I', len(msg))
        # Zabezpieczenie przed zablokowaniem całego serwera przez 1 gracza z pełnym buforem TCP
        old_timeout = conn.gettimeout()
        conn.settimeout(3.0)
        conn.sendall(length + msg)
        conn.settimeout(old_timeout)
    except:
        pass

def recv_msg(conn):
    """Odbiera wiadomość z prefiksem długości."""
    try:
        raw_msg_len = recv_all(conn, 4)
        if not raw_msg_len: return None
        msg_len = struct.unpack('!I', raw_msg_len)[0]
        return json.loads(recv_all(conn, msg_len).decode('utf-8'))
    except:
        return None

def recv_all(conn, n):
    """Pomocnicza funkcja do odbierania n bajtów."""
    data = bytearray()
    while len(data) < n:
        try:
            packet = conn.recv(n - len(data))
            if packet == b'': return None # Zapobieganie Hot-Loop 100% CPU
            data.extend(packet)
        except Exception:
            return None
    return data

def save_match_result(winner_id, loser_id, winner_score, loser_score):
    if not db_pool: return
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO matches (player1_id, player2_id, winner_id) VALUES (%s, %s, %s) RETURNING match_id",
                       (winner_id, loser_id, winner_id))
            match_id = cur.fetchone()[0]
            cur.execute("INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                       (winner_id, match_id, winner_score, True))
            cur.execute("INSERT INTO scores (user_id, match_id, points, is_winner) VALUES (%s, %s, %s, %s)",
                       (loser_id, match_id, loser_score, False))
            conn.commit()
    except Exception as e:
        logging.error(f"Błąd zapisu meczu: {e}")
        conn.rollback()
    finally:
        db_pool.putconn(conn)

def find_room_by_conn(conn):
    """Przeszukuje aktywne pokoje w poszukiwaniu połączenia danego gracza."""
    with rooms_lock:
        for code, room in rooms.items():
            if any(p["conn"] == conn for p in room["players"]):
                return code, room
    return None, None

def handle_client(conn, addr):
    global waiting_random_player, waiting_random_name, waiting_random_id, current_connections
    
    # 1. Sprawdzenie limitu połączeń
    with connections_lock:
        if current_connections >= MAX_CONNECTIONS:
            logging.warning(f"Odrzucono połączenie od {addr}: Serwer pełny ({MAX_CONNECTIONS})")
            send_msg(conn, {"status": "error", "message": "Serwer jest pełny. Spróbuj później."})
            conn.close()
            return
        current_connections += 1

    logging.info(f"Nowe połączenie: {addr} (Aktywne: {current_connections})")

    # Konfiguracja TCP Keep-Alive do wykrywania brutalnie zerwanych połączeń (np. odpięcie kabla)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    try:
        # Windows: czas bezczynności 10s, interwał 3s
        conn.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 3000))
    except Exception:
        try:
            # Linux fallback
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        except Exception:
            pass
            
    # Wyłączenie algorytmu Nagle'a (TCP_NODELAY) - natychmiastowe wysyłanie małych pakietów (strzały, czat)
    try:
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception:
        pass

    # Wyślij powitanie (wymagane przez Network.connect() w network.py)
    send_msg(conn, {"status": "success", "message": "Witaj na serwerze Statków!"})

    username = None
    current_db_user_id = None
    current_room_code = None

    try:
        while True:
            request = recv_msg(conn)
            if not request: break
            
            action = request.get("action")

            # --- WERYFIKACJA SESJI (Security Fix) ---
            if action not in ["register", "login"] and username is None:
                logging.warning(f"Odrzucono nieautoryzowaną akcję '{action}' od {addr}")
                send_msg(conn, {"status": "error", "message": "Brak autoryzacji. Zaloguj się najpierw."})
                conn.close()
                return

            if action == "register":
                u, p = request.get("username"), request.get("password")
                if not u or not p or len(p) < 8:
                    send_msg(conn, {"status": "error", "message": "Niepoprawne dane (hasło min. 8 znaków)."})
                    continue
                
                db_conn = db_pool.getconn()
                try:
                    with db_conn.cursor() as cur:
                        cur.execute("SELECT user_id FROM users WHERE username = %s", (u,))
                        if cur.fetchone():
                            send_msg(conn, {"status": "error", "message": "Użytkownik już istnieje."})
                        else:
                            hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (u, hashed))
                            db_conn.commit()
                            send_msg(conn, {"status": "success", "message": "Zarejestrowano pomyślnie!"})
                except Exception as e:
                    logging.error(f"Błąd rejestracji: {e}")
                    send_msg(conn, {"status": "error", "message": "Błąd bazy danych."})
                finally:
                    db_pool.putconn(db_conn)

            elif action == "login":
                u, p = request.get("username"), request.get("password")
                db_conn = db_pool.getconn()
                try:
                    with db_conn.cursor() as cur:
                        cur.execute("SELECT user_id, password_hash FROM users WHERE username = %s", (u,))
                        row = cur.fetchone()
                        if row and bcrypt.checkpw(p.encode('utf-8'), row[1].encode('utf-8')):
                            uid = row[0]
                            with auth_lock:
                                if uid in logged_in_users:
                                    send_msg(conn, {"status": "error", "message": "Użytkownik jest już zalogowany!"})
                                else:
                                    logged_in_users.add(uid)
                                    username = u
                                    current_db_user_id = uid
                                    send_msg(conn, {"status": "success", "message": "Zalogowano!", "user_id": uid})
                        else:
                            send_msg(conn, {"status": "error", "message": "Błędny login lub hasło."})
                except Exception as e:
                    logging.error(f"Błąd logowania: {e}")
                    send_msg(conn, {"status": "error", "message": "Błąd serwera."})
                finally:
                    db_pool.putconn(db_conn)

            elif action == "get_high_scores":
                scores = get_high_scores_from_db()
                send_msg(conn, {"status": "success", "data": scores})

            elif action == "create_room":
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                with rooms_lock:
                    rooms[code] = {
                        "players": [{"conn": conn, "username": username, "db_id": current_db_user_id, "ready": False}],
                        "boards": [{}, {}],
                        "hits": [set(), set()],
                        "misses": [set(), set()],
                        "scores": [0, 0],
                        "turn": 0,
                        "game_over": False,
                        "is_private": True,
                        "rematch_votes": [False, False],
                        "match_epoch": int(time.time()),
                        "last_action_time": time.time()
                    }
                current_room_code = code
                send_msg(conn, {"status": "room_created", "room_code": code})

            elif action == "join_room":
                code = request.get("room_code")
                with rooms_lock:
                    if code in rooms and len(rooms[code]["players"]) == 1:
                        rooms[code]["players"].append({"conn": conn, "username": username, "db_id": current_db_user_id, "ready": False})
                        current_room_code = code
                        # Start game event
                        p1 = rooms[code]["players"][0]
                        send_msg(p1["conn"], {"status": "game_start", "opponent": username})
                        send_msg(conn, {"status": "game_start", "opponent": p1["username"]})
                    else:
                        send_msg(conn, {"status": "error", "message": "Pokój nie istnieje lub jest pełny."})

            elif action == "random_match":
                with waiting_lock:
                    if waiting_random_player and waiting_random_player != conn:
                        # Połącz graczy
                        p1_conn, p1_name, p1_id = waiting_random_player, waiting_random_name, waiting_random_id
                        waiting_random_player = None
                        waiting_random_name = None
                        waiting_random_id = None
                        
                        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                        with rooms_lock:
                            rooms[code] = {
                                "players": [
                                    {"conn": p1_conn, "username": p1_name, "db_id": p1_id, "ready": False},
                                    {"conn": conn, "username": username, "db_id": current_db_user_id, "ready": False}
                                ],
                                "boards": [{}, {}],
                                "hits": [set(), set()],
                                "scores": [0, 0],
                                "turn": 0,
                                "is_private": False,
                                "rematch_votes": [False, False],
                                "match_epoch": int(time.time()),
                                "last_action_time": time.time()
                            }
                        current_room_code = code
                        send_msg(p1_conn, {"status": "game_start", "opponent": username})
                        send_msg(conn, {"status": "game_start", "opponent": p1_name})
                    else:
                        waiting_random_player = conn
                        waiting_random_name = username
                        waiting_random_id = current_db_user_id
                        send_msg(conn, {"status": "waiting"})

            elif action == "player_ready":
                board = request.get("board")
                if not current_room_code:
                    current_room_code, room = find_room_by_conn(conn)
                else:
                    with rooms_lock: room = rooms.get(current_room_code)
                
                if room:
                    with rooms_lock:
                        p_idx = 0 if room["players"][0]["conn"] == conn else 1
                        if room["players"][p_idx]["ready"]:
                            continue  # Zapobieganie exploitowi double-ready
                        room["boards"][p_idx] = board
                        room["players"][p_idx]["ready"] = True
                        if all(p["ready"] for p in room["players"]):
                            room["turn"] = random.randint(0, 1)
                            room["last_action_time"] = time.time()
                            # Race condition fix: powiadomienia o starcie mają priorytet przed logiką strzałów
                            for i, p in enumerate(room["players"]):
                                send_msg(p["conn"], {
                                    "status": "battle_start",
                                    "your_idx": i,
                                    "starting_turn": room["turn"]
                                })

            elif action == "shoot":
                x, y = request.get("x"), request.get("y")
                if not current_room_code:
                    current_room_code, room = find_room_by_conn(conn)
                else:
                    with rooms_lock: room = rooms.get(current_room_code)
                
                if room:
                    with rooms_lock:
                        p_idx = 0 if room["players"][0]["conn"] == conn else 1
                        if room["turn"] == p_idx and not room.get("game_over"):
                            opp_idx = 1 - p_idx
                            opp_board = room["boards"][opp_idx]
                            
                            # Zabezpieczenie przed dublowaniem punktów w to samo pole
                            if (x, y) in room["hits"][opp_idx] or (x, y) in room.get("misses", [set(), set()])[opp_idx]:
                                continue

                            if "misses" not in room:
                                room["misses"] = [set(), set()]

                            hit = False
                            sunk = False
                            sunk_cells = []
                            points_gained = 0
                            points_lost = 0

                            # Prosta logika trafień (można rozbudować o Sunk Detection)
                            for ship in opp_board:
                                cells = [tuple(c) for c in ship["cells"]]
                                if (x, y) in cells:
                                    hit = True
                                    room["hits"][opp_idx].add((x, y))
                                    # Check if sunk
                                    is_sunk = all(c in room["hits"][opp_idx] for c in cells)
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
                                room["scores"][p_idx] += points_gained if sunk else 50
                                room["scores"][opp_idx] -= points_lost if sunk else 10
                            else:
                                room["misses"][opp_idx].add((x, y))
                                room["turn"] = opp_idx
                                room["scores"][p_idx] -= 10
                            
                            room["last_action_time"] = time.time()
                            
                            shot_result = {
                                "status": "shot_result",
                                "x": x,
                                "y": y,
                                "hit": hit,
                                "sunk": sunk,
                                "sunk_cells": sunk_cells,
                                "shooter": p_idx,
                                "next_turn": room["turn"],
                                "scores": room["scores"]
                            }
                            send_msg(room["players"][0]["conn"], shot_result)
                            send_msg(room["players"][1]["conn"], shot_result)

                            # Sprawdź koniec gry (18 trafień to suma segmentów: 4+3+3+2+2+1+1+1+1 = 18)
                            if len(room["hits"][opp_idx]) == 18:
                                room["game_over"] = True
                                winner = room["players"][p_idx]
                                loser = room["players"][opp_idx]
                                w_id, l_id = winner["db_id"], loser["db_id"]
                                w_score, l_score = room["scores"][p_idx], room["scores"][opp_idx]
                                
                                msg = {"status": "game_over", "winner": winner["username"], "final_scores": room["scores"]}
                                send_msg(room["players"][0]["conn"], msg)
                                send_msg(room["players"][1]["conn"], msg)
                                
                                # Zapis poza lockiem, aby nie mrozić serwera
                                threading.Thread(target=save_match_result, args=(w_id, l_id, w_score, l_score), daemon=True).start()

            elif action == "leave_room":
                # Kiedy gracz wychodzi do menu
                if not current_room_code:
                    current_room_code, room = find_room_by_conn(conn)
                else:
                    with rooms_lock: room = rooms.get(current_room_code)
                
                if room:
                    with rooms_lock:
                        p_idx = 0 if room["players"][0]["conn"] == conn else 1
                        opp_idx = 1 - p_idx
                        
                        if len(room["players"]) > opp_idx:
                            opp = room["players"][opp_idx]
                            if opp:
                                send_msg(opp["conn"], {"status": "opponent_disconnected", "message": "Przeciwnik opuścił grę!"})
                                
                                # Jeśli uciekł w trakcie bitwy (obaj byli gotowi i nie było końca gry), rywal wygrywa walkowerem
                                if not room.get("game_over") and all(p and p["ready"] for p in room["players"]):
                                    room["game_over"] = True
                                    winner = opp
                                    loser = room["players"][p_idx]
                                    threading.Thread(target=save_match_result, 
                                                   args=(winner["db_id"], loser["db_id"], room["scores"][opp_idx], room["scores"][p_idx]), 
                                                   daemon=True).start()
                                    
                        if current_room_code in rooms:
                            del rooms[current_room_code]
                            logging.info(f"Pokój {current_room_code} usunięty z pamięci (leave_room).")
                current_room_code = None
                
                with waiting_lock:
                    if waiting_random_player == conn:
                        waiting_random_player = None
                        waiting_random_name = None
                        waiting_random_id = None

            elif action == "chat_message":
                import re
                raw_msg = request.get("message", "")[:100]
                # Przepuszczamy małe/duże litery łacińskie, polskie, cyfry i podstawowe znaki (bez emoji)
                msg_text = "".join(c for c in raw_msg if re.match(r'^[a-zA-Z0-9ąćęłńóśźżĄĆĘŁŃÓŚŹŻ \!\@\#\$\%\^\&\*\(\)\-\_\=\+\[\]\{\}\\\|\;\:\'\"\,\.\<\>\/\?]+$', c))
                
                if not current_room_code:
                    current_room_code, room = find_room_by_conn(conn)
                else:
                    with rooms_lock: room = rooms.get(current_room_code)
                
                if room:
                    with rooms_lock:
                        opp_idx = 1 if room["players"][0]["conn"] == conn else 0
                        if len(room["players"]) > opp_idx and room["players"][opp_idx]:
                            send_msg(room["players"][opp_idx]["conn"], {
                                "status": "chat_message", "sender": username, "message": msg_text
                            })

            elif action == "request_rematch":
                if not current_room_code:
                    current_room_code, room = find_room_by_conn(conn)
                else:
                    with rooms_lock: room = rooms.get(current_room_code)
                
                if room:
                    with rooms_lock:
                        p_idx = 0 if room["players"][0]["conn"] == conn else 1
                        room["rematch_votes"][p_idx] = True
                        opp_idx = 1 - p_idx
                        if room["rematch_votes"][opp_idx]:
                            room["match_epoch"] = int(time.time())
                            room["turn"] = random.randint(0, 1)
                            room["scores"] = [0, 0]
                            room["hits"] = [set(), set()]
                            room["misses"] = [set(), set()]
                            room["game_over"] = False
                            room["boards"] = [{}, {}]
                            room["players"][0]["ready"] = False
                            room["players"][1]["ready"] = False
                            room["rematch_votes"] = [False, False]
                            room["last_action_time"] = 0
                            send_msg(room["players"][0]["conn"], {"status": "rematch_start"})
                            send_msg(room["players"][1]["conn"], {"status": "rematch_start"})
                        else:
                            send_msg(room["players"][opp_idx]["conn"], {"status": "rematch_requested"})

            elif action == "surrender":
                if not current_room_code:
                    current_room_code, room = find_room_by_conn(conn)
                else:
                    with rooms_lock: room = rooms.get(current_room_code)
                
                if room:
                    with rooms_lock:
                        if room.get("game_over"):
                            continue
                            
                        p_idx = 0 if room["players"][0]["conn"] == conn else 1
                        opp_idx = 1 - p_idx
                        winner = room["players"][opp_idx]
                        loser = room["players"][p_idx]
                        
                        if winner:
                            room["game_over"] = True
                            msg = {"status": "game_over", "winner": winner["username"], "final_scores": room["scores"]}
                            send_msg(room["players"][0]["conn"], {**msg, "message": "Koniec gry (poddanie)."})
                            send_msg(room["players"][1]["conn"], {**msg, "message": "Koniec gry (poddanie)."})
                            
                            # Zapis poza lockiem
                            threading.Thread(target=save_match_result, 
                                           args=(winner["db_id"], loser["db_id"], room["scores"][opp_idx], room["scores"][p_idx]), 
                                           daemon=True).start()

    except Exception as e:
        logging.error(f"Błąd klienta {addr}: {e}")
    finally:
        with connections_lock:
            current_connections -= 1
            
        with auth_lock:
            if current_db_user_id in logged_in_users: logged_in_users.remove(current_db_user_id)
            
        with waiting_lock:
            if waiting_random_player == conn:
                waiting_random_player = None
                waiting_random_name = None
                waiting_random_id = None
                logging.info(f"Gracz {username} usunięty z kolejki wyszukiwania.")

        with rooms_lock:
            if current_room_code in rooms:
                room = rooms[current_room_code]
                for p in room["players"]:
                    if p and p["conn"] == conn:
                        logging.info(f"Gracz {username} rozłączony. Natychmiastowe zamykanie pokoju {current_room_code}.")
                        
                        opp_idx = 1 if room["players"][0] == p else 0
                        if len(room["players"]) > opp_idx:
                            opp = room["players"][opp_idx]
                            if opp:
                                send_msg(opp["conn"], {"status": "opponent_disconnected", "message": "Przeciwnik opuścił grę!"})
                        break
                
                # Natychmiastowe usunięcie pokoju po rozłączeniu któregokolwiek z graczy
                del rooms[current_room_code]
                logging.info(f"Pokój {current_room_code} usunięty z pamięci.")
        conn.close()

def turn_timer_checker():
    """Wątek sprawdzający czas tury oraz czyszczący stare, nieaktywne pokoje."""
    last_cleanup_time = time.time()
    while True:
        time.sleep(1)
        messages_to_send = []
        current_time = time.time()
        
        with rooms_lock:
            # 1. Automatyczny Garbage Collector dla pokoi (raz na minutę)
            if current_time - last_cleanup_time > 60:
                for code, room in list(rooms.items()):
                    # Jeśli w pokoju nie było akcji od 10 minut - usuwamy go (zapobieganie wyciekom RAM)
                    if current_time - room["last_action_time"] > 600:
                        logging.info(f"Garbage Collector: Usuwanie porzuconego pokoju {code}")
                        del rooms[code]
                last_cleanup_time = current_time

            # 2. Logika AFK Timeout (30 sekund na ruch)
            for code, room in list(rooms.items()):
                # Sprawdzenie czy gra się toczy (2 graczy i obaj gotowi)
                if len(room["players"]) == 2 and all(p and p["ready"] for p in room["players"]):
                    # Jeśli czas od ostatniej akcji > 30s
                    if current_time - room["last_action_time"] > 30:
                        room["turn"] = 1 - room["turn"]
                        room["last_action_time"] = current_time
                        timeout_msg = {
                            "status": "turn_timeout",
                            "next_turn": room["turn"]
                        }
                        for p in room["players"]:
                            if p:
                                messages_to_send.append((p["conn"], timeout_msg))
                                
        # Wysyłamy wiadomości poza blokadą słownika, aby nie blokować innych wątków
        for conn, msg in messages_to_send:
            send_msg(conn, msg)

def start_server():
    threading.Thread(target=turn_timer_checker, daemon=True).start()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    logging.info(f"Serwer (Length-Prefixing) uruchomiony na porcie {PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
