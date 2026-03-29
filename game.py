# game.py
import pygame
import sys
from settings import *


def draw_grid(surface, x_offset, y_offset, size=800):  # Zwiększony rozmiar domyślny
    """Rysuje siatkę 10x10 wraz z oznaczeniami A-J oraz 1-10."""
    cell_size = size // 10
    font_labels = pygame.font.SysFont("arial", 30, bold=True)

    # Litery dla kolumn i Cyfry dla wierszy
    letters = "ABCDEFGHIJ"

    for i in range(10):
        # Rysowanie liter (kolumny) - nad siatką
        let_surf = font_labels.render(letters[i], True, TEXT_COLOR)
        let_rect = let_surf.get_rect(center=(x_offset + i * cell_size + cell_size // 2, y_offset - 30))
        surface.blit(let_surf, let_rect)

        # Rysowanie cyfr (wiersze) - po lewej stronie siatki
        num_surf = font_labels.render(str(i + 1), True, TEXT_COLOR)
        num_rect = num_surf.get_rect(center=(x_offset - 40, y_offset + i * cell_size + cell_size // 2))
        surface.blit(num_surf, num_rect)

    # Rysowanie linii siatki
    for i in range(11):
        # Linie poziome
        pygame.draw.line(surface, GRID_COLOR, (x_offset, y_offset + i * cell_size),
                         (x_offset + size, y_offset + i * cell_size), 2)
        # Linie pionowe
        pygame.draw.line(surface, GRID_COLOR, (x_offset + i * cell_size, y_offset),
                         (x_offset + i * cell_size, y_offset + size), 2)


def get_player_names(screen, background):
    """Ekran wpisywania nicków przez graczy."""
    font_input = pygame.font.SysFont("arial", 70)
    font_desc = pygame.font.SysFont("arial", 40)
    names = ["", ""]
    current_player = 0
    clock = pygame.time.Clock()

    while current_player < 2:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        prompt = f"Gracz {current_player + 1}: Podaj swoje imię"
        prompt_surf = font_desc.render(prompt, True, TEXT_COLOR)
        screen.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))

        input_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 40, 600, 80)
        pygame.draw.rect(screen, BUTTON_COLOR, input_rect, border_radius=15)

        name_surf = font_input.render(names[current_player], True, TEXT_COLOR)
        screen.blit(name_surf, name_surf.get_rect(center=input_rect.center))

        instruction = "Naciśnij ENTER aby zatwierdzić | ESC aby wrócić"
        inst_surf = font_desc.render(instruction, True, (200, 200, 200))
        screen.blit(inst_surf, inst_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_RETURN and names[current_player].strip():
                    current_player += 1
                elif event.key == pygame.K_BACKSPACE:
                    names[current_player] = names[current_player][:-1]
                else:
                    if len(names[current_player]) < 12 and event.unicode.isprintable():
                        names[current_player] += event.unicode

        pygame.display.update()
        clock.tick(FPS)
    return names


def play_game(screen, p1_name, p2_name):
    """Główny ekran fali rozstawiania."""
    font_ui = pygame.font.SysFont("arial", 40)
    clock = pygame.time.Clock()

    # Parametry układu
    grid_size = 800  # Plansza jest teraz znacznie większa
    grid_x = 180  # Przesunięta lekko w prawo, by zrobić miejsce na numery wierszy
    grid_y = 160

    # Zmniejszony placeholder na statki (Zasobnik)
    ship_tray_rect = pygame.Rect(WIDTH - 550, 160, 450, 800)

    while True:
        # Tło jednolite (brak zdjęcia)
        screen.fill(BG_COLOR)

        # Nagłówek fazy
        title_font = pygame.font.SysFont("arial", 50, bold=True)
        title_surf = title_font.render(f"Faza Rozstawiania: {p1_name}", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))

        # Rysowanie dużej planszy z opisami
        draw_grid(screen, grid_x, grid_y, grid_size)

        # Podpis pod planszą
        p1_label = font_ui.render(f"Twoja Flota: {p1_name}", True, TEXT_COLOR)
        screen.blit(p1_label, p1_label.get_rect(center=(grid_x + grid_size // 2, grid_y + grid_size + 40)))

        # Rysowanie mniejszego zasobnika na statki
        pygame.draw.rect(screen, (50, 50, 70), ship_tray_rect, border_radius=15)
        pygame.draw.rect(screen, GRID_COLOR, ship_tray_rect, width=2, border_radius=15)

        tray_label = font_ui.render("STATKI DO ROZSTAWIENIA", True, TEXT_COLOR)
        # Umieszczenie tekstu na górze zasobnika
        screen.blit(tray_label, tray_label.get_rect(center=(ship_tray_rect.centerx, ship_tray_rect.top + 50)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        pygame.display.update()
        clock.tick(FPS)