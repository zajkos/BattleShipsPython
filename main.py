# main.py
import pygame
import sys
from settings import *
from button import Button

# Inicjalizacja Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Statki - Menu Główne")
clock = pygame.time.Clock()

# Inicjalizacja czcionek
font_title = pygame.font.SysFont("arial", 70, bold=True)
font_button = pygame.font.SysFont("arial", 40)


def draw_text(text, font, color, surface, x, y):
    """Renderuje tekst w podanym miejscu."""
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)


def main_menu():
    # Ustawienia rozmiaru i pozycji przycisków
    btn_width, btn_height = 300, 60
    start_x = WIDTH // 2 - btn_width // 2

    # Tworzenie obiektów przycisków
    btn_play = Button(start_x, 200, btn_width, btn_height, "Graj", font_button)
    btn_scores = Button(start_x, 280, btn_width, btn_height, "Top Wyniki", font_button)
    btn_options = Button(start_x, 360, btn_width, btn_height, "Opcje", font_button)
    btn_credits = Button(start_x, 440, btn_width, btn_height, "Twórcy", font_button)
    btn_exit = Button(start_x, 520, btn_width, btn_height, "Wyjście", font_button)

    buttons = [btn_play, btn_scores, btn_options, btn_credits, btn_exit]

    # Główna pętla menu
    while True:
        screen.fill(BG_COLOR)
        draw_text('GRA STATKI', font_title, TEXT_COLOR, screen, WIDTH // 2, 100)

        mouse_pos = pygame.mouse.get_pos()

        # Obsługa zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Reakcje na kliknięcia
            if btn_play.handle_event(event):
                print("Przejście do gry / wpisywania nicku (KAN-11)")
            if btn_scores.handle_event(event):
                print("Otwieranie Top Wyników (KAN-49)")
            if btn_options.handle_event(event):
                print("Otwieranie Menu Opcji (KAN-42)")
            if btn_credits.handle_event(event):
                print("Otwieranie ekranu Twórców (KAN-45)")
            if btn_exit.handle_event(event):
                pygame.quit()
                sys.exit()

        # Aktualizacja stanu i rysowanie przycisków
        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main_menu()