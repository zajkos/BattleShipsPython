import pygame
import sys
from settings import *
from button import Button, ImageButton
import options


def show_credits(screen, clock, background=None):
    """Wyświetla ekran twórców z przewijającym się tekstem."""

    # Czcionki
    font_header = pygame.font.SysFont("arial", 60, bold=True)
    font_text = pygame.font.SysFont("arial", 35)

    # Lista twórców
    credits_lines = [
        "GRA STATKI",
        "",
        "PROJECT MANAGER:",
        "Wiktor",
        "GŁÓWNI PROGRAMIŚCI:",
        "Bartosz",
        "Jakub",
        "",

        "Dziękujemy za grę!"
    ]

    # Ustawienia przycisku "Powrót"
    btn_width, btn_height = 250, 60
    btn_back = ImageButton(WIDTH // 2 - btn_width // 2, HEIGHT - 100, "powrót.png", width=btn_width)

    # Zmienna odpowiedzialna za pozycję Y tekstu (zaczyna pod dolną krawędzią ekranu)
    text_y_start = HEIGHT
    scroll_speed = 1.5

    # Optymalizacja: Pre-renderowanie linijek tekstu (eliminacja dropów FPS)
    rendered_lines = []
    for line in credits_lines:
        if line == "GRA STATKI":
            surf = font_header.render(line, True, TEXT_COLOR)
        else:
            surf = font_text.render(line, True, TEXT_COLOR)
        rendered_lines.append(surf)

    running = True
    while running:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()

        # 1. Obsługa zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Jeśli klikniemy powrót, przerywamy pętlę ekranu twórców
            if btn_back.handle_event(event):
                running = False

        # 2. Rysowanie i przewijanie tekstu
        current_y = text_y_start
        for surf in rendered_lines:
            text_rect = surf.get_rect(center=(WIDTH // 2, current_y))
            screen.blit(surf, text_rect)
            # Odstęp między linijkami
            current_y += 50
            # Aktualizacja pozycji Y (przewijanie w górę)
        text_y_start -= scroll_speed

        # Opcjonalnie: Zresetowanie pozycji, gdy tekst wyjedzie całkowicie za ekran
        if current_y < 0:
            text_y_start = HEIGHT

        # 3. Rysowanie przycisku powrotu (jest rysowany na końcu, by przykrywał tekst)
        btn_back.check_hover(mouse_pos)
        btn_back.draw(screen)

        pygame.display.update()
        clock.tick(options.current_fps)