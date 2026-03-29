# main.py
import pygame
import sys
from settings import *
from button import Button
import game

# Inicjalizacja Pygame
pygame.init()

# Otwarcie w trybie pełnoekranowym z natywną rozdzielczością 1920x1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Statki - Menu Główne")
clock = pygame.time.Clock()

# Inicjalizacja czcionek - zwiększone rozmiary dla 1080p
font_title = pygame.font.SysFont("arial", 120, bold=True)
font_button = pygame.font.SysFont("arial", 50)


def draw_text(text, font, color, surface, x, y):
    """Renderuje tekst w podanym miejscu."""
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)


def main_menu():
    try:
        background_image_raw = pygame.image.load(BACKGROUND_IMAGE_FILENAME).convert()
        background_image = pygame.transform.scale(background_image_raw, (WIDTH, HEIGHT))
    except pygame.error as e:
        print(f"Nie można załadować obrazu tła: {e}")
        background_image = None


    btn_width, btn_height = 450, 80
    start_x = WIDTH // 2 - btn_width // 2
    start_y = 350
    spacing = 100

    btn_play = Button(start_x, start_y, btn_width, btn_height, "Graj", font_button)
    btn_scores = Button(start_x, start_y + spacing, btn_width, btn_height, "Top Wyniki", font_button)
    btn_options = Button(start_x, start_y + spacing * 2, btn_width, btn_height, "Opcje", font_button)
    btn_credits = Button(start_x, start_y + spacing * 3, btn_width, btn_height, "Twórcy", font_button)
    btn_exit = Button(start_x, start_y + spacing * 4, btn_width, btn_height, "Wyjście", font_button)

    buttons = [btn_play, btn_scores, btn_options, btn_credits, btn_exit]

    while True:
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BG_COLOR)

        draw_text('GRA STATKI', font_title, TEXT_COLOR, screen, WIDTH // 2, 200)

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            # Reakcje na kliknięcia
            if btn_play.handle_event(event):
                player_names = game.get_player_names(screen, background_image)
                if player_names:  # Jeśli gracz nie wyszedł przez ESCAPE
                    game.play_game(screen, player_names[0], player_names[1])

            if btn_scores.handle_event(event):
                print("Otwieranie Top Wyników (KAN-49)")
            if btn_options.handle_event(event):
                print("Otwieranie Menu Opcji (KAN-42)")
            if btn_credits.handle_event(event):
                print("Otwieranie ekranu Twórców (KAN-45)")
            if btn_exit.handle_event(event):
                pygame.quit()
                sys.exit()

        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main_menu()