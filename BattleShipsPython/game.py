# game.py
import pygame
import sys
import json
from settings import *
from button import Button


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


def play_game(screen, p1_name, p2_name):
    """Główny ekran fazy rozstawiania statków."""
    font_ui = pygame.font.SysFont("arial", 40)
    clock = pygame.time.Clock()

    grid_size = 800
    grid_x = 180
    grid_y = 160
    ship_tray_rect = pygame.Rect(WIDTH - 550, 160, 450, 800)

    while True:
        screen.fill(BG_COLOR)

        title_font = pygame.font.SysFont("arial", 50, bold=True)
        title_surf = title_font.render(f"Faza Rozstawiania: {p1_name} vs {p2_name}", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))

        draw_grid(screen, grid_x, grid_y, grid_size)

        p1_label = font_ui.render("Twoja Flota", True, TEXT_COLOR)
        screen.blit(p1_label, p1_label.get_rect(center=(grid_x + grid_size // 2, grid_y + grid_size + 40)))

        pygame.draw.rect(screen, (50, 50, 70), ship_tray_rect, border_radius=15)
        pygame.draw.rect(screen, GRID_COLOR, ship_tray_rect, width=2, border_radius=15)

        tray_label = font_ui.render("STATKI DO ROZSTAWIENIA", True, TEXT_COLOR)
        screen.blit(tray_label, tray_label.get_rect(center=(ship_tray_rect.centerx, ship_tray_rect.top + 50)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return  # Powrót do menu / poddanie walki

        pygame.display.update()
        clock.tick(FPS)