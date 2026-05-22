# game.py
import pygame
import sys
import json
import random
from settings import *
from button import Button, ImageButton
from audio_manager import play_sfx
import options


# Globalny cache dla siatki (żeby nie renderować 20 liter/cyfr w każdej klatce)
_grid_cache = None

def draw_grid(surface, x_offset, y_offset, size=800):
    """Rysuje siatkę 10x10 wraz z oznaczeniami A-J oraz 1-10 (zoptymalizowana pamięcią podręczną)."""
    global _grid_cache
    if _grid_cache is None:
        _grid_cache = pygame.Surface((size + 60, size + 60), pygame.SRCALPHA)
        cell_size = size // 10
        font_labels = pygame.font.SysFont("arial", 30, bold=True)
        letters = "ABCDEFGHIJ"

        # Odsunięcia wewnątrz bufora
        buf_x = 40
        buf_y = 40

        for i in range(10):
            let_surf = font_labels.render(letters[i], True, TEXT_COLOR)
            let_rect = let_surf.get_rect(center=(buf_x + i * cell_size + cell_size // 2, buf_y - 30))
            _grid_cache.blit(let_surf, let_rect)

            num_surf = font_labels.render(str(i + 1), True, TEXT_COLOR)
            num_rect = num_surf.get_rect(center=(buf_x - 30, buf_y + i * cell_size + cell_size // 2))
            _grid_cache.blit(num_surf, num_rect)

        for i in range(11):
            pygame.draw.line(_grid_cache, GRID_COLOR, (buf_x, buf_y + i * cell_size),
                             (buf_x + size, buf_y + i * cell_size), 2)
            pygame.draw.line(_grid_cache, GRID_COLOR, (buf_x + i * cell_size, buf_y),
                             (buf_x + i * cell_size, buf_y + size), 2)

    # Rysujemy skeszowaną siatkę we właściwym miejscu na ekranie
    surface.blit(_grid_cache, (x_offset - 40, y_offset - 40))


def get_player_name(screen, background):
    """Ekran wpisywania nicku przez gracza."""
    font_input = pygame.font.SysFont("arial", 70)
    font_desc = pygame.font.SysFont("arial", 40)
    name = ""
    clock = pygame.time.Clock()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    prompt_surf = font_desc.render("Podaj swój nick:", True, TEXT_COLOR)
    prompt_rect = prompt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
    inst_surf = font_desc.render("Naciśnij ENTER aby zatwierdzić | ESC aby wrócić", True, (200, 200, 200))
    inst_rect = inst_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))

    last_name = None
    name_surf = None
    name_rect = None

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        screen.blit(overlay, (0, 0))
        screen.blit(prompt_surf, prompt_rect)

        input_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 40, 600, 80)
        pygame.draw.rect(screen, BUTTON_COLOR, input_rect, border_radius=15)

        if name != last_name:
            last_name = name
            name_surf = font_input.render(name, True, TEXT_COLOR)
            name_rect = name_surf.get_rect(center=input_rect.center)
        
        screen.blit(name_surf, name_rect)
        screen.blit(inst_surf, inst_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return None
                if event.key == pygame.K_RETURN and name.strip():
                    return name
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 12 and event.unicode.isprintable(): name += event.unicode

        pygame.display.update()
        clock.tick(options.current_fps)


def matchmaking_menu(screen, background):
    """Podmenu wyboru trybu gry po wpisaniu nicku."""
    font_button = pygame.font.SysFont("arial", 50)
    font_title = pygame.font.SysFont("arial", 80, bold=True)
    clock = pygame.time.Clock()

    btn_w = 320
    start_x = WIDTH // 2 - btn_w // 2
    start_y = 350
    spacing = 110

    btn_random = ImageButton(start_x, start_y, "szybka gra.png", width=btn_w)
    btn_create = ImageButton(start_x, start_y + spacing, "stwórz pokój.png", width=btn_w)
    btn_join = ImageButton(start_x, start_y + spacing * 2, "dołącz do pokoju.png", width=btn_w)
    btn_back = ImageButton(WIDTH // 2 - 110, start_y + spacing * 3, "powrót.png", width=220)

    buttons = [btn_random, btn_create, btn_join, btn_back]

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    title_surf = font_title.render("Wybierz Tryb Gry", True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 200))

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        screen.blit(overlay, (0, 0))
        screen.blit(title_surf, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if btn_random.handle_event(event): return {"action": "random_match"}
            if btn_create.handle_event(event): return {"action": "create_room"}
            if btn_join.handle_event(event):
                code = get_room_code_input(screen, background)
                if code: return {"action": "join_room", "room_code": code}
            if btn_back.handle_event(event): return None

        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(options.current_fps)


def get_room_code_input(screen, background):
    """Pop-up do wpisania 5-znakowego kodu pokoju."""
    font_input = pygame.font.SysFont("arial", 70)
    font_desc = pygame.font.SysFont("arial", 40)
    code = ""
    clock = pygame.time.Clock()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    prompt_surf = font_desc.render("Wpisz kod pokoju (5 znaków):", True, TEXT_COLOR)
    prompt_rect = prompt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

    last_code = None
    code_surf = None
    code_rect = None

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        screen.blit(overlay, (0, 0))
        screen.blit(prompt_surf, prompt_rect)

        input_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 40, 400, 80)
        pygame.draw.rect(screen, BUTTON_COLOR, input_rect, border_radius=15)

        if code != last_code:
            last_code = code
            code_surf = font_input.render(code.upper(), True, TEXT_COLOR)
            code_rect = code_surf.get_rect(center=input_rect.center)

        screen.blit(code_surf, code_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return None
                if event.key == pygame.K_RETURN and len(code) == 5:
                    return code.upper()
                elif event.key == pygame.K_BACKSPACE:
                    code = code[:-1]
                else:
                    if len(code) < 5 and event.unicode.isalnum(): code += event.unicode.upper()

        pygame.display.update()
        clock.tick(options.current_fps)


def waiting_screen(screen, background, net, status_message, room_code=None):
    """Ekran oczekiwania z nieblokującym sprawdzaniem serwera."""
    font_title = pygame.font.SysFont("arial", 70, bold=True)
    font_desc = pygame.font.SysFont("arial", 50)
    clock = pygame.time.Clock()

    # Ustawienie socketa na nieblokujący, aby pętla PyGame mogła się kręcić
    net.client.setblocking(False)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    # Pre-renderowanie tekstów
    title_surf = font_title.render(status_message, True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))

    code_surf = None
    code_rect = None
    if room_code:
        code_surf = font_desc.render(f"Twój Kod: {room_code}", True, (255, 215, 0))
        code_rect = code_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

    instruction_surf = font_desc.render("Naciśnij ESC aby wyjść", True, (200, 200, 200))
    instruction_rect = instruction_surf.get_rect(center=(WIDTH // 2, HEIGHT - 100))

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        screen.blit(overlay, (0, 0))
        screen.blit(title_surf, title_rect)

        if code_surf:
            screen.blit(code_surf, code_rect)

        screen.blit(instruction_surf, instruction_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                net.client.setblocking(True)
                return None

        # Odbieranie danych z serwera (nieblokująco)
        try:
            data = net.client.recv(2048).decode()
            if data:
                response = json.loads(data)
                if response.get("status") == "game_start":
                    net.client.setblocking(True)  # Przywracamy blokowanie na czas gry
                    return response.get("opponent")
                elif response.get("status") == "opponent_disconnected":
                    return None  # Przeciwnik uciekł
        except BlockingIOError:
            pass  # Brak nowych wiadomości, pętla leci dalej
        except Exception as e:
            print(f"Błąd sieci: {e}")
            return None

        pygame.display.update()
        clock.tick(options.current_fps)


from ship import Ship


def is_valid_placement(ship, col, row, placed_ships):
    """Sprawdza czy statek mieści się na planszy i nie koliduje z innymi (odstęp 1 kratka)."""
    new_cells = ship.get_grid_cells(col, row)

    # 1. Granice planszy
    for c, r in new_cells:
        if not (0 <= c < 10 and 0 <= r < 10):
            return False

    # 2. Kolizje i odstęp (sprawdzamy 3x3 wokół każdej komórki statku)
    for other_ship in placed_ships:
        if other_ship == ship: continue

        # Pobieramy komórki zajęte przez inny statek
        other_cells = other_ship.get_grid_cells(other_ship.grid_pos[0], other_ship.grid_pos[1])

        for c, r in new_cells:
            # Sprawdzamy sąsiedztwo (8 pól wokół + pole statku)
            for dc in range(-1, 2):
                for dr in range(-1, 2):
                    if (c + dc, r + dr) in other_cells:
                        return False
    return True


import random


def randomize_ships(ships, grid_x, grid_y, cell_size, placed_ships):
    """Automatycznie rozstawia statki na planszy w losowych miejscach."""
    placed_ships.clear()
    for s in ships:
        s.grid_pos = None
        s.update_to_grid_size(cell_size)

        placed = False
        attempts = 0
        while not placed and attempts < 200:
            attempts += 1
            s.horizontal = random.choice([True, False])
            s.update_to_grid_size(cell_size)

            col = random.randint(0, 9)
            row = random.randint(0, 9)

            if is_valid_placement(s, col, row, placed_ships):
                s.grid_pos = (col, row)
                s.rect.x = grid_x + col * cell_size
                s.rect.y = grid_y + row * cell_size
                placed_ships.append(s)
                placed = True

        # Jeśli nie udało się postawić statku po 200 próbach (mało prawdopodobne, ale możliwe),
        # zdejmujemy wszystko i próbujemy jeszcze raz od zera
        if not placed:
            return randomize_ships(ships, grid_x, grid_y, cell_size, placed_ships)


class AnimationEffect:
    def __init__(self, x, y, frames, speed=0.8, loop=False):
        self.x = x
        self.y = y
        self.frames = frames
        self.current_frame = 0
        # Przeliczamy prędkość, aby animacja trwała tyle samo niezależnie od FPS
        # Przy założeniu że bazowa prędkość (np. 0.8) była projektowana pod 60 FPS:
        self.speed = speed * (60.0 / FPS) 
        self.finished = False
        self.loop = loop

    def update(self):
        if self.finished: return
        self.current_frame += self.speed
        if self.current_frame >= len(self.frames):
            if self.loop:
                self.current_frame = 0
            else:
                self.finished = True

    def draw(self, surface):
        if not self.finished and self.frames:
            idx = int(self.current_frame)
            if idx < len(self.frames):
                frame = self.frames[idx]
                rect = frame.get_rect(center=(self.x, self.y))
                surface.blit(frame, rect)


# Globalny cache dla klatek animacji
_animation_cache = {}

def load_spritesheet(filename, rows, cols, target_size, start_frame=0, end_frame=None):
    # Generujemy unikalny klucz dla cache uwzględniający plik i rozmiar docelowy
    cache_key = f"{filename}_{target_size[0]}x{target_size[1]}_{start_frame}_{end_frame}"
    if cache_key in _animation_cache:
        return _animation_cache[cache_key]

    try:
        sheet = pygame.image.load(filename).convert_alpha()
        sheet_w, sheet_h = sheet.get_size()
        frame_w = sheet_w // cols
        frame_h = sheet_h // rows
        frames = []

        total_frames = rows * cols
        if end_frame is None:
            end_frame = total_frames

        for r in range(rows):
            for c in range(cols):
                frame_idx = r * cols + c
                if frame_idx < start_frame or frame_idx >= end_frame:
                    continue

                rect = pygame.Rect(c * frame_w, r * frame_h, frame_w, frame_h)
                # Używamy subsurface bez kopiowania jeśli to możliwe, lub konwertujemy od razu
                frame = sheet.subsurface(rect)
                frame = pygame.transform.smoothscale(frame, target_size)
                frames.append(frame)
        
        _animation_cache[cache_key] = frames
        return frames
    except Exception as e:
        print(f"Błąd ładowania animacji {filename}: {e}")
        return []


def play_game(screen, p1_name, p2_name, net, background=None):
    """Ekran fazy rozstawiania statków z mechaniką Drag & Drop i komunikacją z serwerem."""
    # Próba załadowania specyficznego tła dla fazy rozstawiania
    try:
        placement_bg_raw = pygame.image.load("plansza.png").convert() #plansza1os.png
        placement_bg = pygame.transform.scale(placement_bg_raw, (WIDTH, HEIGHT))
    except Exception as e:
        print(f"Nie można załadować plansza1os.png: {e}")
        placement_bg = background

    font_ui = pygame.font.SysFont("arial", 40)
    font_small = pygame.font.SysFont("arial", 30)
    clock = pygame.time.Clock()

    # Synchronizacja wymiarów i pozycji z battle_phase
    cell_size = 68
    grid_size = cell_size * 10
    grid_x = 180 + 30
    grid_y = 240 + 20

    # Nowy, większy zasobnik zakrywający prawą planszę
    ship_tray_rect = pygame.Rect(960, 150, 880, 860)

    # Inicjalizacja floty (1x4, 2x3, 2x2, 4x1) -> Łącznie 9 statków
    lengths = [4, 3, 3, 2, 2, 1, 1, 1, 1]
    ships = []

    # Rozmieszczenie statków w zasobniku (wyśrodkowane w nowym szerokim panelu)
    current_y = ship_tray_rect.top + 40
    for length in lengths:
        s = Ship(length, color=(70, 130, 180))
        s.update_to_tray_size(scale=0.9)
        s.rect.centerx = ship_tray_rect.centerx
        s.rect.y = current_y
        s.initial_pos = (s.rect.x, s.rect.y)
        ships.append(s)
        current_y += int(cell_size * 0.9) + 12

    dragging_ship = None
    placed_ships = []
    waiting_for_opponent = False

    if net:
        net.client.setblocking(False)

    # Przyciski pomocnicze - ułożone na dole panelu
    bw = 260
    spacing_btn = 290
    btn_start_x = ship_tray_rect.x + (ship_tray_rect.width - (bw * 3 + 40)) // 2 + 130
    
    btn_random = ImageButton(ship_tray_rect.centerx - 410, ship_tray_rect.bottom - 100, "losuj.png", width=bw)
    btn_clear = ImageButton(ship_tray_rect.centerx - 130, ship_tray_rect.bottom - 100, "wyczyść.png", width=bw)
    btn_ready = ImageButton(ship_tray_rect.centerx + 150, ship_tray_rect.bottom - 100, "S T A R T.png", width=bw)
    title_font = pygame.font.SysFont("arial", 50, bold=True)

    last_waiting_status = None
    title_surf = None
    title_rect = None

    net_buffer = ""

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        if placement_bg:
            screen.blit(placement_bg, (0, 0))
        elif background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        # Aktualizacja tytułu tylko gdy stan się zmieni
        if waiting_for_opponent != last_waiting_status:
            last_waiting_status = waiting_for_opponent
            title_text = f"Faza Rozstawiania: {p1_name}" if not waiting_for_opponent else "Oczekiwanie na przeciwnika..."
            title_surf = title_font.render(title_text, True, TEXT_COLOR)
            title_rect = title_surf.get_rect(center=(WIDTH // 2, 60))

        screen.blit(title_surf, title_rect)

        # Siatka jest już na obrazku tła
        if not placement_bg:
            draw_grid(screen, grid_x, grid_y, grid_size)

        if not waiting_for_opponent:
            # UI Zasobnika - ciemnoszary z grubą złotą ramką
            pygame.draw.rect(screen, (45, 45, 45), ship_tray_rect, border_radius=15)
            pygame.draw.rect(screen, BUTTON_HOVER_COLOR, ship_tray_rect, width=5, border_radius=15)

            btn_random.check_hover(mouse_pos)
            btn_random.draw(screen)
            btn_clear.check_hover(mouse_pos)
            btn_clear.draw(screen)

            if len(placed_ships) == 9:
                btn_ready.check_hover(mouse_pos)
                btn_ready.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if waiting_for_opponent:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if net: net.client.setblocking(True)
                    return
                continue  # Zablokowanie edycji planszy

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if len(placed_ships) == 9 and btn_ready.handle_event(event):
                    # Najpierw zmieniamy stan UI, aby użytkownik widział napis "Oczekiwanie..."
                    waiting_for_opponent = True
                    # Przygotuj dane planszy dla serwera
                    board_data = []
                    for s in placed_ships:
                        board_data.append({
                            "cells": s.get_grid_cells(s.grid_pos[0], s.grid_pos[1])
                        })
                    if net:
                        # Używamy nowej metody, która NIE czeka na odpowiedź
                        net.send_no_wait({"action": "player_ready", "board": board_data})
                    continue

                if btn_random.handle_event(event):
                    randomize_ships(ships, grid_x, grid_y, cell_size, placed_ships)
                    continue

                if btn_clear.handle_event(event):
                    placed_ships.clear()
                    for s in ships:
                        s.grid_pos = None
                        s.update_to_tray_size(scale=0.9)
                        s.rect.x, s.rect.y = s.initial_pos
                    continue

                # Chwyć statek
                for s in reversed(ships):
                    if s.rect.collidepoint(mouse_pos):
                        dragging_ship = s
                        s.dragging = True
                        s.offset_x = s.rect.x - mouse_pos[0]
                        s.offset_y = s.rect.y - mouse_pos[1]
                        if s in placed_ships:
                            placed_ships.remove(s)
                        # Używamy tej samej mechaniki co w battle_phase: skalujemy do grid_size
                        s.update_to_grid_size(cell_size)
                        break

            # Rotacja PPM
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and not waiting_for_opponent:
                if dragging_ship:
                    dragging_ship.rotate()
                    # Po rotacji odświeżamy wymiary (już zawarte w rotate(), ale dla pewności przy dragging_ship)
                    dragging_ship.update_to_grid_size(cell_size)
                    dragging_ship.offset_x = dragging_ship.rect.x - mouse_pos[0]
                    dragging_ship.offset_y = dragging_ship.rect.y - mouse_pos[1]
                else:
                    for s in ships:
                        if s.rect.collidepoint(mouse_pos):
                            if s in placed_ships:
                                placed_ships.remove(s)

                            col, row = round((s.rect.x - grid_x) / cell_size), round((s.rect.y - grid_y) / cell_size)
                            s.rotate()
                            s.update_to_grid_size(cell_size)

                            s.rect.x = grid_x + col * cell_size
                            s.rect.y = grid_y + row * cell_size

                            if is_valid_placement(s, col, row, placed_ships):
                                s.grid_pos = (col, row)
                                placed_ships.append(s)
                                play_sfx('drop')
                            else:
                                s.grid_pos = None
                                s.update_to_tray_size()
                                s.rect.x, s.rect.y = s.initial_pos
                            break

            if event.type == pygame.MOUSEBUTTONUP and not waiting_for_opponent:
                if event.button == 1 and dragging_ship:
                    dragging_ship.dragging = False
                    rel_x = dragging_ship.rect.x - grid_x
                    rel_y = dragging_ship.rect.y - grid_y
                    col = round(rel_x / cell_size)
                    row = round(rel_y / cell_size)

                    if is_valid_placement(dragging_ship, col, row, placed_ships):
                        dragging_ship.grid_pos = (col, row)
                        dragging_ship.rect.x = grid_x + col * cell_size
                        dragging_ship.rect.y = grid_y + row * cell_size
                        placed_ships.append(dragging_ship)
                        play_sfx('drop')
                    else:
                        dragging_ship.grid_pos = None
                        dragging_ship.update_to_tray_size()
                        dragging_ship.rect.x, dragging_ship.rect.y = dragging_ship.initial_pos
                    dragging_ship = None

            if event.type == pygame.MOUSEMOTION and dragging_ship and not waiting_for_opponent:
                dragging_ship.rect.x = mouse_pos[0] + dragging_ship.offset_x
                dragging_ship.rect.y = mouse_pos[1] + dragging_ship.offset_y

            if event.type == pygame.KEYDOWN and not waiting_for_opponent:
                if event.key == pygame.K_r and dragging_ship:
                    dragging_ship.rotate()
                    dragging_ship.offset_x = dragging_ship.rect.x - mouse_pos[0]
                    dragging_ship.offset_y = dragging_ship.rect.y - mouse_pos[1]
                if event.key == pygame.K_ESCAPE:
                    if net: net.client.setblocking(True)
                    return

        # Odbieranie sygnałów od serwera w trakcie oczekiwania
        if waiting_for_opponent and net:
            try:
                data = net.client.recv(2048).decode()
                if data:
                    net_buffer += data
                    
                    # Parsowanie wszystkich kompletnych obiektów JSON z bufora
                    while "}" in net_buffer:
                        # Szukamy pierwszego zamykającego nawiasu i odpowiadającego mu otwierającego
                        end_idx = net_buffer.find("}") + 1
                        start_idx = net_buffer.rfind("{", 0, end_idx)
                        
                        if start_idx != -1:
                            json_str = net_buffer[start_idx:end_idx]
                            try:
                                response = json.loads(json_str)
                                # Usuwamy przetworzony fragment z bufora
                                net_buffer = net_buffer[end_idx:]
                                
                                if response.get("status") == "battle_start":
                                    print("Faza bitwy uruchomiona!")
                                    p_idx = response.get("your_idx", 0)
                                    start_turn = response.get("starting_turn", 0)
                                    return battle_phase(screen, p1_name, p2_name, net, p_idx, start_turn, placed_ships, background)
                                elif response.get("status") == "opponent_disconnected":
                                    print("Przeciwnik rozłączony w trakcie oczekiwania.")
                                    if net: net.client.setblocking(True)
                                    return None
                            except json.JSONDecodeError:
                                # Może być zagnieżdżony JSON, czekamy na więcej danych
                                break
                        else:
                            # Oczyszczanie bufora z błędnych danych
                            net_buffer = net_buffer[end_idx:]
            except BlockingIOError:
                pass
            except Exception as e:
                print(f"Błąd sieci podczas oczekiwania: {e}")

        # Rysowanie wszystkich statków
        for s in ships:
            if s != dragging_ship:
                s.draw(screen)

        # Przeciągany statek na samym wierzchu
        if dragging_ship and not waiting_for_opponent:
            dragging_ship.draw(screen)

        pygame.display.update()
        clock.tick(options.current_fps)


def battle_phase(screen, p1_name, p2_name, net, player_idx, initial_turn, my_fleet, background=None):
    """Główny ekran bitwy. Rysuje dwie plansze, własną flotę i zarządza turami."""
    # Próba załadowania specyficznego tła dla fazy bitwy
    is_custom_bg = False
    try:
        battle_bg_raw = pygame.image.load("plansza.png").convert()
        battle_bg = pygame.transform.scale(battle_bg_raw, (WIDTH, HEIGHT))
        is_custom_bg = True
    except Exception as e:
        print(f"Nie można załadować plansza.png: {e}")
        battle_bg = background

    font_title = pygame.font.SysFont("arial", 60, bold=True)
    font_ui = pygame.font.SysFont("arial", 40)
    font_score = pygame.font.SysFont("arial", 30)
    clock = pygame.time.Clock()

    # Nowe wymiary i pozycje dopasowane do plansza.png (Etap 4: +20px prawo, +5px dół)
    cell_size = 68
    grid_size = cell_size * 10
    my_grid_x, my_grid_y = 180 + 30, 240 + 20
    enemy_grid_x, enemy_grid_y = 990 + 28, 240 + 20

    current_turn = initial_turn

    my_shots_hit = set()
    my_shots_miss = set()
    enemy_shots_hit = set()
    enemy_shots_miss = set()

    my_score = 0
    enemy_score = 0

    net.client.setblocking(False)

    # Wczytywanie animacji
    cell_size = 68
    explosion_anim_size = (int(cell_size * 1.8), int(cell_size * 1.8))
    splash_anim_size = (int(cell_size * 1.0), int(cell_size * 1.0)) # Zmniejszono, by mieścił się w kratce
    smoke_anim_size = (int(cell_size * 1.0), int(cell_size * 1.0))

    explosion_frames = load_spritesheet("wybuch.png", 6, 8, explosion_anim_size)
    splash_frames = load_spritesheet("plusk2.png", 6, 8, splash_anim_size)
    smoke_frames = load_spritesheet("smoke.png", 6, 8, smoke_anim_size, start_frame=16, end_frame=40)
    active_animations = []
    persistent_effects = []

    shake_amount = 0
    shake_timer = 0
    render_offset = [0, 0]
    
    game_over = False
    winner_name = ""
    last_game_over_state = False
    res_surf = None
    res_rect = None
    score_surf = None
    score_rect = None
    btn_back_to_menu = ImageButton(WIDTH // 2 - 110, HEIGHT // 2 + 180, "powrot do menu.png", width=220)
    btn_rematch = ImageButton(WIDTH // 2 - 160, HEIGHT // 2 + 70, "RWEANŻ.png", width=320)
    rematch_requested = False
    opponent_requested_rematch = False

    # Optymalizacja: alokujemy powierzchnie raz, by nie obciążać GC i CPU (FPS drop fix)
    display_surface = pygame.Surface((WIDTH, HEIGHT))
    game_over_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    game_over_overlay.fill((0, 0, 0, 200))

    # Timer tury
    turn_start_time = pygame.time.get_ticks()
    turn_limit = 30000  # 30 sekund w ms

    # Pre-renderowanie floty (raz przed pętlą)
    for ship in my_fleet:
        ship.update_to_grid_size(cell_size)
        col, row = ship.grid_pos
        ship.rect.x = my_grid_x + col * cell_size
        ship.rect.y = my_grid_y + row * cell_size

    # Cache dla tekstów UI
    last_turn_status = None
    last_my_score = -1
    last_enemy_score = -1
    turn_surf = None
    my_score_surf = None
    enemy_score_surf = None
    
    # Sunk ships tracking
    enemy_sunk_ships_cells = set()

    # Czat
    chat_log = []
    chat_active = False
    chat_input = ""
    chat_font = pygame.font.SysFont("arial", 22)
    
    # Menu Pauzy
    is_paused = False
    pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pause_overlay.fill((0, 0, 0, 150))
    
    btn_w = 320
    start_x = WIDTH // 2 - btn_w // 2
    start_y = HEIGHT // 2 - 150
    spacing = 110
    
    btn_pause_resume = ImageButton(start_x, start_y, "kontynuuj.png", width=btn_w)
    btn_pause_options = ImageButton(WIDTH // 2 - 140, start_y + spacing, "opcje.png", width=280)
    btn_pause_quit = ImageButton(WIDTH // 2 - 110, start_y + spacing * 2, "wyjście.png", width=220)

    net_buffer = ""

    while True:
        current_time_ms = pygame.time.get_ticks()
        # Jeśli pauza, czas się zatrzymuje (wizualnie)
        if not is_paused and not game_over:
            time_left = max(0, (turn_limit - (current_time_ms - turn_start_time)) // 1000)
        else:
            time_left = max(0, (turn_limit - (current_time_ms - turn_start_time)) // 1000)

        if shake_timer > 0:
            shake_timer -= 1
            render_offset[0] = random.randint(-shake_amount, shake_amount)
            render_offset[1] = random.randint(-shake_amount, shake_amount)
        else:
            render_offset = [0, 0]

        if battle_bg:
            display_surface.blit(battle_bg, (0, 0))
        else:
            display_surface.fill(BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()

        is_my_turn = (current_turn == player_idx)
        
        # Aktualizacja tekstów tylko gdy się zmienią
        if is_my_turn != last_turn_status:
            last_turn_status = is_my_turn
            turn_start_time = pygame.time.get_ticks()
            turn_text = "TWOJA TURA!" if is_my_turn else f"Oczekiwanie na ruch: {p2_name}..."
            turn_color = (50, 205, 50) if is_my_turn else (200, 50, 50)
            turn_surf = font_title.render(turn_text, True, turn_color)
            turn_rect = turn_surf.get_rect(center=(WIDTH // 2, 80))

        if my_score != last_my_score:
            last_my_score = my_score
            my_score_surf = font_score.render(f"Punkty: {my_score}", True, (255, 215, 0))
            my_score_rect = my_score_surf.get_rect(center=(my_grid_x + grid_size // 2, my_grid_y + grid_size + 40))

        if enemy_score != last_enemy_score:
            last_enemy_score = enemy_score
            enemy_score_surf = font_score.render(f"Punkty: {enemy_score}", True, (255, 215, 0))
            enemy_score_rect = enemy_score_surf.get_rect(center=(enemy_grid_x + grid_size // 2, enemy_grid_y + grid_size + 40))

        display_surface.blit(turn_surf, turn_rect)
        display_surface.blit(my_score_surf, my_score_rect)
        display_surface.blit(enemy_score_surf, enemy_score_rect)
        
        # Rysowanie timera
        timer_color = (0, 255, 0) if time_left > 10 else (255, 0, 0)
        timer_surf = font_score.render(f"Czas: {time_left}s", True, timer_color)
        display_surface.blit(timer_surf, (WIDTH // 2 - 50, 120))

        for ship in my_fleet:
            ship.draw(display_surface)

        # Rysowanie zatopionych statków wroga
        for x, y in enemy_sunk_ships_cells:
            pygame.draw.rect(display_surface, (200, 0, 0, 100), 
                             (enemy_grid_x + x * cell_size, enemy_grid_y + y * cell_size, cell_size, cell_size))

        for x, y in my_shots_miss:
            pygame.draw.circle(display_surface, (150, 150, 150), (enemy_grid_x + x * cell_size + cell_size // 2,
                                                                  enemy_grid_y + y * cell_size + cell_size // 2),
                               cell_size // 3)

        for x, y in enemy_shots_miss:
            pygame.draw.circle(display_surface, (150, 150, 150),
                               (my_grid_x + x * cell_size + cell_size // 2, my_grid_y + y * cell_size + cell_size // 2),
                               cell_size // 3)

        # Rysowanie trafień (X na polach)
        for x, y in my_shots_hit:
            pygame.draw.line(display_surface, (255, 0, 0), 
                             (enemy_grid_x + x * cell_size + 10, enemy_grid_y + y * cell_size + 10),
                             (enemy_grid_x + (x+1) * cell_size - 10, enemy_grid_y + (y+1) * cell_size - 10), 3)
            pygame.draw.line(display_surface, (255, 0, 0), 
                             (enemy_grid_x + (x+1) * cell_size - 10, enemy_grid_y + y * cell_size + 10),
                             (enemy_grid_x + x * cell_size + 10, enemy_grid_y + (y+1) * cell_size - 10), 3)

        for x, y in enemy_shots_hit:
             pygame.draw.line(display_surface, (255, 0, 0), 
                             (my_grid_x + x * cell_size + 10, my_grid_y + y * cell_size + 10),
                             (my_grid_x + (x+1) * cell_size - 10, my_grid_y + (y+1) * cell_size - 10), 3)
             pygame.draw.line(display_surface, (255, 0, 0), 
                             (my_grid_x + (x+1) * cell_size - 10, my_grid_y + y * cell_size + 10),
                             (my_grid_x + x * cell_size + 10, my_grid_y + (y+1) * cell_size - 10), 3)

        # Czat UI
        chat_surf = pygame.Surface((400, 250), pygame.SRCALPHA)
        chat_surf.fill((0, 0, 0, 100))
        display_surface.blit(chat_surf, (20, HEIGHT - 300))
        for i, m in enumerate(chat_log[-8:]):
            m_surf = chat_font.render(m, True, TEXT_COLOR)
            display_surface.blit(m_surf, (30, HEIGHT - 290 + i * 25))
        
        if chat_active:
            pygame.draw.rect(display_surface, (50, 50, 70), (20, HEIGHT - 45, 400, 35))
            txt_surf = chat_font.render(f"> {chat_input}|", True, (255, 255, 255))
            display_surface.blit(txt_surf, (30, HEIGHT - 40))
        else:
            hint_surf = chat_font.render("Naciśnij 'T' aby pisać", True, (150, 150, 150))
            display_surface.blit(hint_surf, (30, HEIGHT - 40))

        if is_my_turn and not game_over and not is_paused and not chat_active:
            if enemy_grid_x <= mouse_pos[0] <= enemy_grid_x + grid_size and enemy_grid_y <= mouse_pos[
                1] <= enemy_grid_y + grid_size:
                hover_x = (mouse_pos[0] - enemy_grid_x) // cell_size
                hover_y = (mouse_pos[1] - enemy_grid_y) // cell_size
                if (hover_x, hover_y) not in my_shots_hit and (hover_x, hover_y) not in my_shots_miss:
                    # Rysowanie CELOWNIKA (Crosshair)
                    tx = enemy_grid_x + hover_x * cell_size
                    ty = enemy_grid_y + hover_y * cell_size
                    pygame.draw.rect(display_surface, (255, 0, 0), (tx, ty, cell_size, cell_size), 3)
                    s = cell_size // 4
                    pygame.draw.line(display_surface, (255, 255, 255), (tx, ty), (tx+s, ty), 4)
                    pygame.draw.line(display_surface, (255, 255, 255), (tx, ty), (tx, ty+s), 4)
                    pygame.draw.line(display_surface, (255, 255, 255), (tx+cell_size, ty), (tx+cell_size-s, ty), 4)
                    pygame.draw.line(display_surface, (255, 255, 255), (tx+cell_size, ty), (tx+cell_size, ty+s), 4)
                    pygame.draw.line(display_surface, (255, 255, 255), (tx, ty+cell_size), (tx+s, ty+cell_size), 4)
                    pygame.draw.line(display_surface, (255, 255, 255), (tx, ty+cell_size), (tx, ty+cell_size-s), 4)
                    pygame.draw.line(display_surface, (255, 255, 255), (tx+cell_size, ty+cell_size), (tx+cell_size-s, ty+cell_size), 4)
                    pygame.draw.line(display_surface, (255, 255, 255), (tx+cell_size, ty+cell_size), (tx+cell_size, ty+cell_size-s), 4)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if chat_active:
                    if event.key == pygame.K_RETURN:
                        if chat_input.strip():
                            net.send_no_wait({"action": "chat_message", "message": chat_input})
                            chat_log.append(f"Ty: {chat_input}")
                        chat_input = ""
                        chat_active = False
                    elif event.key == pygame.K_ESCAPE:
                        chat_active = False
                        chat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    else:
                        if len(chat_input) < 30:
                            chat_input += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        if not game_over:
                            is_paused = not is_paused
                        else:
                            net.client.setblocking(True)
                            return "MENU"
                    elif event.key == pygame.K_t:
                        chat_active = True

            if is_paused and not game_over:
                btn_pause_resume.check_hover(mouse_pos)
                btn_pause_options.check_hover(mouse_pos)
                btn_pause_quit.check_hover(mouse_pos)
                
                if btn_pause_resume.handle_event(event):
                    is_paused = False
                if btn_pause_options.handle_event(event):
                    from options import show_options
                    show_options(screen, clock, battle_bg)
                if btn_pause_quit.handle_event(event):
                    net.send_no_wait({"action": "surrender"})
                    is_paused = False

            if game_over:
                btn_rematch.check_hover(mouse_pos)
                btn_back_to_menu.check_hover(mouse_pos)
                
                if btn_rematch.handle_event(event) and not rematch_requested:
                    net.send_no_wait({"action": "request_rematch"})
                    rematch_requested = True

                if btn_back_to_menu.handle_event(event):
                    net.client.setblocking(True)
                    return "MENU"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and is_my_turn and not is_paused and not chat_active and not game_over:
                if enemy_grid_x <= mouse_pos[0] <= enemy_grid_x + grid_size and enemy_grid_y <= mouse_pos[
                    1] <= enemy_grid_y + grid_size:
                    click_x = (mouse_pos[0] - enemy_grid_x) // cell_size
                    click_y = (mouse_pos[1] - enemy_grid_y) // cell_size

                    if (click_x, click_y) not in my_shots_hit and (click_x, click_y) not in my_shots_miss:
                        net.send_no_wait({"action": "shoot", "x": click_x, "y": click_y})

        try:
            data = net.client.recv(2048).decode()
            if data:
                net_buffer += data
                
                while "}" in net_buffer:
                    end_idx = net_buffer.find("}") + 1
                    start_idx = net_buffer.rfind("{", 0, end_idx)
                    
                    if start_idx != -1:
                        json_str = net_buffer[start_idx:end_idx]
                        try:
                            response = json.loads(json_str)
                            net_buffer = net_buffer[end_idx:]

                            if response.get("status") == "chat_message":
                                sender = response.get("sender", "Gracz")
                                text = response.get("message", "")
                                chat_log.append(f"{sender}: {text}")

                            elif response.get("status") == "shot_result":
                                sx, sy = response["x"], response["y"]
                                is_hit = response["hit"]
                                is_sunk = response.get("sunk", False)
                                shooter = response["shooter"]
                                current_turn = response["next_turn"]
                                turn_start_time = pygame.time.get_ticks()

                                if is_hit:
                                    play_sfx('hit')
                                    if is_sunk:
                                        play_sfx('win') # Możesz zmienić na specyficzny dźwięk zatopienia
                                        if shooter == player_idx:
                                            for cx, cy in response.get("sunk_cells", []):
                                                enemy_sunk_ships_cells.add((cx, cy))
                                else:
                                    play_sfx('miss')

                                if shooter == player_idx:
                                    ax = enemy_grid_x + sx * cell_size + cell_size // 2
                                    ay = enemy_grid_y + sy * cell_size + cell_size // 2
                                else:
                                    ax = my_grid_x + sx * cell_size + cell_size // 2
                                    ay = my_grid_y + sy * cell_size + cell_size // 2

                                # Spawnowanie animacji zależnie od ustawień w options.py
                                if is_hit and options.explosions_enabled:
                                    active_animations.append(AnimationEffect(ax, ay, explosion_frames))
                                elif not is_hit and options.splash_enabled:
                                    active_animations.append(AnimationEffect(ax, ay, splash_frames))

                                if is_hit:
                                    if options.smoke_enabled:
                                        persistent_effects.append(AnimationEffect(ax, ay, smoke_frames, speed=0.4, loop=True))
                                    shake_amount = 10
                                    shake_timer = 15
                                elif not is_hit and shooter != player_idx:
                                    shake_amount = 3
                                    shake_timer = 8

                                if shooter == player_idx:
                                    if is_hit:
                                        my_shots_hit.add((sx, sy))
                                    else:
                                        my_shots_miss.add((sx, sy))
                                else:
                                    if is_hit:
                                        enemy_shots_hit.add((sx, sy))
                                    else:
                                        enemy_shots_miss.add((sx, sy))

                                if "scores" in response:
                                    new_scores = response["scores"]
                                    my_score = new_scores[player_idx]
                                    enemy_score = new_scores[1 - player_idx]

                            elif response.get("status") == "turn_timeout":
                                current_turn = response["next_turn"]
                                turn_start_time = pygame.time.get_ticks()
                                chat_log.append("SYSTEM: Czas minął! Zmiana tury.")

                            elif response.get("status") == "game_over":
                                game_over = True
                                winner_name = response.get("winner")
                                if "final_scores" in response:
                                    f_scores = response["final_scores"]
                                    my_score = f_scores[player_idx]
                                    enemy_score = f_scores[1 - player_idx]
                                # Wyświetlamy opcjonalną wiadomość systemową (np. o poddaniu się)
                                if response.get("message"):
                                    chat_log.append(f"SYSTEM: {response.get('message')}")

                            elif response.get("status") == "rematch_requested":
                                opponent_requested_rematch = True
                                chat_log.append("SYSTEM: Przeciwnik prosi o rewanż!")

                            elif response.get("status") == "rematch_start":
                                chat_log.append("SYSTEM: Rozpoczynanie rewanżu!")
                                net.client.setblocking(True)
                                return play_game(screen, p1_name, p2_name, net, background)

                            elif response.get("status") == "opponent_disconnected":
                                net.client.setblocking(True)
                                return "MENU"
                        except json.JSONDecodeError:
                            break
                    else:
                        net_buffer = net_buffer[end_idx:]
        except BlockingIOError:
            pass

        for effect in persistent_effects:
            effect.update()
            effect.draw(display_surface)

        for anim in active_animations[:]:
            anim.update()
            anim.draw(display_surface)
            if anim.finished:
                active_animations.remove(anim)

        if is_paused and not game_over:
            display_surface.blit(pause_overlay, (0, 0))
            btn_pause_resume.draw(display_surface)
            btn_pause_options.draw(display_surface)
            btn_pause_quit.draw(display_surface)

        if game_over:
            display_surface.blit(game_over_overlay, (0, 0))

            if game_over != last_game_over_state:
                last_game_over_state = game_over
                res_text = f"ZWYCIĘZCA: {winner_name}"
                res_color = (255, 215, 0) if winner_name == p1_name else (200, 50, 50)
                res_surf = font_title.render(res_text, True, res_color)
                res_rect = res_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

                score_text = f"Twoje punkty: {my_score} | Przeciwnik ({p2_name}): {enemy_score}"
                score_surf = font_ui.render(score_text, True, TEXT_COLOR)
                score_rect = score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            
            display_surface.blit(res_surf, res_rect)
            if score_surf:
                display_surface.blit(score_surf, score_rect)

            btn_rematch.draw(display_surface)
            btn_back_to_menu.draw(display_surface)

        screen.blit(display_surface, (render_offset[0], render_offset[1]))

        pygame.display.update()
        clock.tick(options.current_fps)