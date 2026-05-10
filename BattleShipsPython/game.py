# game.py
import pygame
import sys
import json
from settings import *
from button import Button
from audio_manager import play_sfx  # --- NOWOŚĆ: Import managera dźwięków ---


def draw_grid(surface, x_offset, y_offset, size=800):
    """Rysuje siatkę 10x10 wraz z oznaczeniami A-J oraz 1-10."""
    cell_size = size // 10
    font_labels = pygame.font.SysFont("arial", 30, bold=True)
    letters = "ABCDEFGHIJ"

    for i in range(10):
        let_surf = font_labels.render(letters[i], True, TEXT_COLOR)
        let_rect = let_surf.get_rect(center=(x_offset + i * cell_size + cell_size // 2, y_offset - 30))
        surface.blit(let_surf, let_rect)

        num_surf = font_labels.render(str(i + 1), True, TEXT_COLOR)
        num_rect = num_surf.get_rect(center=(x_offset - 40, y_offset + i * cell_size + cell_size // 2))
        surface.blit(num_surf, num_rect)

    for i in range(11):
        pygame.draw.line(surface, GRID_COLOR, (x_offset, y_offset + i * cell_size),
                         (x_offset + size, y_offset + i * cell_size), 2)
        pygame.draw.line(surface, GRID_COLOR, (x_offset + i * cell_size, y_offset),
                         (x_offset + i * cell_size, y_offset + size), 2)


def get_player_name(screen, background):
    """Ekran wpisywania nicku przez gracza."""
    font_input = pygame.font.SysFont("arial", 70)
    font_desc = pygame.font.SysFont("arial", 40)
    name = ""
    clock = pygame.time.Clock()

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        prompt = "Podaj swój nick:"
        prompt_surf = font_desc.render(prompt, True, TEXT_COLOR)
        screen.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))

        input_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 40, 600, 80)
        pygame.draw.rect(screen, BUTTON_COLOR, input_rect, border_radius=15)

        name_surf = font_input.render(name, True, TEXT_COLOR)
        screen.blit(name_surf, name_surf.get_rect(center=input_rect.center))

        instruction = "Naciśnij ENTER aby zatwierdzić | ESC aby wrócić"
        inst_surf = font_desc.render(instruction, True, (200, 200, 200))
        screen.blit(inst_surf, inst_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))

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
        clock.tick(FPS)


def matchmaking_menu(screen, background):
    """Podmenu wyboru trybu gry po wpisaniu nicku."""
    font_button = pygame.font.SysFont("arial", 50)
    font_title = pygame.font.SysFont("arial", 80, bold=True)
    clock = pygame.time.Clock()

    btn_w, btn_h = 450, 80
    start_x = WIDTH // 2 - btn_w // 2

    btn_random = Button(start_x, 400, btn_w, btn_h, "Szybka Gra", font_button)
    btn_create = Button(start_x, 520, btn_w, btn_h, "Stwórz Pokój", font_button)
    btn_join = Button(start_x, 640, btn_w, btn_h, "Dołącz do Pokoju", font_button)
    btn_back = Button(start_x, 760, btn_w, btn_h, "Powrót", font_button)

    buttons = [btn_random, btn_create, btn_join, btn_back]

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title_surf = font_title.render("Wybierz Tryb Gry", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 200)))

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
        clock.tick(FPS)


def get_room_code_input(screen, background):
    """Pop-up do wpisania 5-znakowego kodu pokoju."""
    font_input = pygame.font.SysFont("arial", 70)
    font_desc = pygame.font.SysFont("arial", 40)
    code = ""
    clock = pygame.time.Clock()

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        prompt_surf = font_desc.render("Wpisz kod pokoju (5 znaków):", True, TEXT_COLOR)
        screen.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))

        input_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 40, 400, 80)
        pygame.draw.rect(screen, BUTTON_COLOR, input_rect, border_radius=15)

        code_surf = font_input.render(code.upper(), True, TEXT_COLOR)
        screen.blit(code_surf, code_surf.get_rect(center=input_rect.center))

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
        clock.tick(FPS)


def waiting_screen(screen, background, net, status_message, room_code=None):
    """Ekran oczekiwania z nieblokującym sprawdzaniem serwera."""
    font_title = pygame.font.SysFont("arial", 70, bold=True)
    font_desc = pygame.font.SysFont("arial", 50)
    clock = pygame.time.Clock()

    # Ustawienie socketa na nieblokujący, aby pętla PyGame mogła się kręcić
    net.client.setblocking(False)

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title_surf = font_title.render(status_message, True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))

        if room_code:
            code_surf = font_desc.render(f"Twój Kod: {room_code}", True, (255, 215, 0))
            screen.blit(code_surf, code_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

        instruction_surf = font_desc.render("Naciśnij ESC aby wyjść", True, (200, 200, 200))
        screen.blit(instruction_surf, instruction_surf.get_rect(center=(WIDTH // 2, HEIGHT - 100)))

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
        clock.tick(FPS)


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
        s.update_to_grid_size()

        placed = False
        attempts = 0
        while not placed and attempts < 200:
            attempts += 1
            s.horizontal = random.choice([True, False])
            s.update_to_grid_size()

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
        self.speed = speed
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


def load_spritesheet(filename, rows, cols, target_size, start_frame=0, end_frame=None):
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
                frame = sheet.subsurface(rect).copy()
                frame.set_colorkey((0, 0, 0))
                frame = pygame.transform.scale(frame, target_size)
                frames.append(frame)
        return frames
    except Exception as e:
        print(f"Błąd ładowania animacji {filename}: {e}")
        return []


def play_game(screen, p1_name, p2_name, net):
    """Ekran fazy rozstawiania statków z mechaniką Drag & Drop i komunikacją z serwerem."""
    font_ui = pygame.font.SysFont("arial", 40)
    font_small = pygame.font.SysFont("arial", 30)
    clock = pygame.time.Clock()

    grid_size = 800
    grid_x = 180
    grid_y = 160
    cell_size = grid_size // 10

    ship_tray_rect = pygame.Rect(WIDTH - 550, 160, 450, 800)

    # Inicjalizacja floty (1x4, 2x3, 2x2, 4x1) -> Łącznie 9 statków
    lengths = [4, 3, 3, 2, 2, 1, 1, 1, 1]
    ships = []

    # Rozmieszczenie statków w zasobniku
    current_y = ship_tray_rect.top + 80
    for length in lengths:
        s = Ship(length, color=(70, 130, 180))
        s.update_to_tray_size()
        s.rect.centerx = ship_tray_rect.centerx
        s.rect.y = current_y
        s.initial_pos = (s.rect.x, s.rect.y)
        ships.append(s)
        current_y += (cell_size // 2) + 20

    dragging_ship = None
    placed_ships = []
    waiting_for_opponent = False

    if net:
        net.client.setblocking(False)

    # Przyciski pomocnicze
    btn_random = Button(WIDTH - 400, HEIGHT - 250, 300, 60, "LOSUJ", font_small)
    btn_clear = Button(WIDTH - 400, HEIGHT - 180, 300, 60, "WYCZYŚĆ", font_small)
    btn_ready = Button(WIDTH - 400, HEIGHT - 100, 300, 70, "START", font_ui)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        title_text = f"Faza Rozstawiania: {p1_name}" if not waiting_for_opponent else "Oczekiwanie na przeciwnika..."
        title_font = pygame.font.SysFont("arial", 50, bold=True)
        title_surf = title_font.render(title_text, True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))

        draw_grid(screen, grid_x, grid_y, grid_size)

        if not waiting_for_opponent:
            # UI Zasobnika
            pygame.draw.rect(screen, (40, 40, 60), ship_tray_rect, border_radius=15)
            pygame.draw.rect(screen, GRID_COLOR, ship_tray_rect, width=2, border_radius=15)
            tray_label = font_ui.render("TWOJA FLOTA", True, TEXT_COLOR)
            screen.blit(tray_label, tray_label.get_rect(center=(ship_tray_rect.centerx, ship_tray_rect.top + 30)))

            btn_random.check_hover(mouse_pos)
            btn_random.draw(screen)
            btn_clear.check_hover(mouse_pos)
            btn_clear.draw(screen)

            if len(placed_ships) == 9:
                btn_ready.check_hover(mouse_pos)
                btn_ready.draw(screen)

            instr = "LPM: Przeciągnij | PPM/R: Obróć | ESC: Wyjście"
            instr_surf = pygame.font.SysFont("arial", 25).render(instr, True, (180, 180, 180))
            screen.blit(instr_surf, (grid_x, grid_y + grid_size + 20))

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
                    waiting_for_opponent = True
                    board_data = []
                    for s in placed_ships:
                        board_data.append({
                            "cells": s.get_grid_cells(s.grid_pos[0], s.grid_pos[1])
                        })
                    if net:
                        net.send_no_wait({"action": "player_ready", "board": board_data})
                    continue

                if btn_random.handle_event(event):
                    randomize_ships(ships, grid_x, grid_y, cell_size, placed_ships)
                    continue

                if btn_clear.handle_event(event):
                    placed_ships.clear()
                    for s in ships:
                        s.grid_pos = None
                        s.update_to_tray_size()
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
                        s.update_to_grid_size()
                        break

            # Rotacja PPM
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and not waiting_for_opponent:
                if dragging_ship:
                    dragging_ship.rotate()
                    dragging_ship.offset_x = dragging_ship.rect.x - mouse_pos[0]
                    dragging_ship.offset_y = dragging_ship.rect.y - mouse_pos[1]
                else:
                    for s in ships:
                        if s.rect.collidepoint(mouse_pos):
                            if s in placed_ships:
                                placed_ships.remove(s)

                            col, row = round((s.rect.x - grid_x) / cell_size), round((s.rect.y - grid_y) / cell_size)
                            s.rotate()
                            s.update_to_grid_size()

                            s.rect.x = grid_x + col * cell_size
                            s.rect.y = grid_y + row * cell_size

                            if is_valid_placement(s, col, row, placed_ships):
                                s.grid_pos = (col, row)
                                placed_ships.append(s)
                                play_sfx('drop')  # --- NOWOŚĆ: Dźwięk położenia rotowanego statku ---
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
                        play_sfx('drop')  # --- NOWOŚĆ: Dźwięk położenia przeciąganego statku ---
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
                    response = json.loads(data)
                    if response.get("status") == "battle_start":
                        print("Faza bitwy uruchomiona!")
                        p_idx = response.get("your_idx", 0)
                        start_turn = response.get("starting_turn", 0)

                        return battle_phase(screen, p1_name, p2_name, net, p_idx, start_turn, placed_ships)
                    elif response.get("status") == "opponent_disconnected":
                        print("Przeciwnik rozłączony w trakcie oczekiwania.")
                        if net: net.client.setblocking(True)
                        return None
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
        clock.tick(FPS)


def battle_phase(screen, p1_name, p2_name, net, player_idx, initial_turn, my_fleet):
    """Główny ekran bitwy. Rysuje dwie plansze, własną flotę i zarządza turami."""
    font_title = pygame.font.SysFont("arial", 60, bold=True)
    font_ui = pygame.font.SysFont("arial", 40)
    font_score = pygame.font.SysFont("arial", 30)
    clock = pygame.time.Clock()

    grid_size = 600
    my_grid_x, my_grid_y = 150, 250
    enemy_grid_x, enemy_grid_y = WIDTH - grid_size - 150, 250
    cell_size = grid_size // 10

    current_turn = initial_turn

    my_shots_hit = set()
    my_shots_miss = set()
    enemy_shots_hit = set()
    enemy_shots_miss = set()

    my_score = 0
    enemy_score = 0

    net.client.setblocking(False)

    anim_size = (int(cell_size * 1.8), int(cell_size * 1.8))
    smoke_anim_size = (int(cell_size * 1.0), int(cell_size * 1.0))

    explosion_frames = load_spritesheet("wybuch.png", 6, 8, anim_size)
    splash_frames = load_spritesheet("plusk.png", 6, 8, anim_size)
    smoke_frames = load_spritesheet("smoke.png", 6, 8, smoke_anim_size, start_frame=16, end_frame=40)
    active_animations = []
    persistent_effects = []

    shake_amount = 0
    shake_timer = 0
    render_offset = [0, 0]

    while True:
        if shake_timer > 0:
            shake_timer -= 1
            render_offset[0] = random.randint(-shake_amount, shake_amount)
            render_offset[1] = random.randint(-shake_amount, shake_amount)
        else:
            render_offset = [0, 0]

        display_surface = pygame.Surface((WIDTH, HEIGHT))
        display_surface.fill(BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()

        is_my_turn = (current_turn == player_idx)
        turn_text = "TWOJA TURA!" if is_my_turn else f"Oczekiwanie na ruch: {p2_name}..."
        turn_color = (50, 205, 50) if is_my_turn else (200, 50, 50)

        turn_surf = font_title.render(turn_text, True, turn_color)
        display_surface.blit(turn_surf, turn_surf.get_rect(center=(WIDTH // 2, 80)))

        my_label = font_ui.render("TWOJA FLOTA", True, TEXT_COLOR)
        display_surface.blit(my_label, my_label.get_rect(center=(my_grid_x + grid_size // 2, my_grid_y - 80)))

        enemy_label = font_ui.render("FLOTA WROGA", True, TEXT_COLOR)
        display_surface.blit(enemy_label,
                             enemy_label.get_rect(center=(enemy_grid_x + grid_size // 2, enemy_grid_y - 80)))

        my_score_surf = font_score.render(f"Punkty: {my_score}", True, (255, 215, 0))
        display_surface.blit(my_score_surf,
                             my_score_surf.get_rect(center=(my_grid_x + grid_size // 2, my_grid_y + grid_size + 40)))

        enemy_score_surf = font_score.render(f"Punkty: {enemy_score}", True, (255, 215, 0))
        display_surface.blit(enemy_score_surf,
                             enemy_score_surf.get_rect(
                                 center=(enemy_grid_x + grid_size // 2, enemy_grid_y + grid_size + 40)))

        draw_grid(display_surface, my_grid_x, my_grid_y, grid_size)
        draw_grid(display_surface, enemy_grid_x, enemy_grid_y, grid_size)

        for ship in my_fleet:
            col, row = ship.grid_pos
            ship.cell_size = cell_size
            ship.update_to_grid_size(cell_size)
            ship.rect.x = my_grid_x + col * cell_size
            ship.rect.y = my_grid_y + row * cell_size
            ship.draw(display_surface)

        for x, y in my_shots_miss:
            pygame.draw.circle(display_surface, (150, 150, 150), (enemy_grid_x + x * cell_size + cell_size // 2,
                                                                  enemy_grid_y + y * cell_size + cell_size // 2),
                               cell_size // 3)

        for x, y in enemy_shots_miss:
            pygame.draw.circle(display_surface, (150, 150, 150),
                               (my_grid_x + x * cell_size + cell_size // 2, my_grid_y + y * cell_size + cell_size // 2),
                               cell_size // 3)

        if is_my_turn:
            if enemy_grid_x <= mouse_pos[0] <= enemy_grid_x + grid_size and enemy_grid_y <= mouse_pos[
                1] <= enemy_grid_y + grid_size:
                hover_x = (mouse_pos[0] - enemy_grid_x) // cell_size
                hover_y = (mouse_pos[1] - enemy_grid_y) // cell_size
                if (hover_x, hover_y) not in my_shots_hit and (hover_x, hover_y) not in my_shots_miss:
                    pygame.draw.rect(display_surface, (255, 255, 255, 100),
                                     (enemy_grid_x + hover_x * cell_size, enemy_grid_y + hover_y * cell_size, cell_size,
                                      cell_size), 3)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                net.client.setblocking(True)
                return "MENU"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and is_my_turn:
                if enemy_grid_x <= mouse_pos[0] <= enemy_grid_x + grid_size and enemy_grid_y <= mouse_pos[
                    1] <= enemy_grid_y + grid_size:
                    click_x = (mouse_pos[0] - enemy_grid_x) // cell_size
                    click_y = (mouse_pos[1] - enemy_grid_y) // cell_size

                    if (click_x, click_y) not in my_shots_hit and (click_x, click_y) not in my_shots_miss:
                        net.send_no_wait({"action": "shoot", "x": click_x, "y": click_y})

        try:
            data = net.client.recv(2048).decode()
            if data:
                messages = data.replace("}{", "}SPLIT{").split("SPLIT")
                for msg in messages:
                    response = json.loads(msg)

                    if response.get("status") == "shot_result":
                        sx, sy = response["x"], response["y"]
                        is_hit = response["hit"]
                        shooter = response["shooter"]
                        current_turn = response["next_turn"]

                        # --- NOWOŚĆ: Odtwarzanie dźwięków w zależności od trafienia ---
                        if is_hit:
                            play_sfx('hit')
                        else:
                            play_sfx('miss')

                        if shooter == player_idx:
                            ax = enemy_grid_x + sx * cell_size + cell_size // 2
                            ay = enemy_grid_y + sy * cell_size + cell_size // 2
                        else:
                            ax = my_grid_x + sx * cell_size + cell_size // 2
                            ay = my_grid_y + sy * cell_size + cell_size // 2

                        target_frames = explosion_frames if is_hit else splash_frames
                        active_animations.append(AnimationEffect(ax, ay, target_frames))

                        if is_hit:
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

                    elif response.get("status") == "opponent_disconnected":
                        net.client.setblocking(True)
                        return "MENU"
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

        screen.blit(display_surface, (render_offset[0], render_offset[1]))

        pygame.display.update()
        clock.tick(FPS)