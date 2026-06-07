# main.py
import pygame
import sys
import os

# Obsługa ścieżek dla PyInstallera
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

from settings import *
from button import Button, ImageButton
import game
from credits import show_credits
from options import show_options
from auth_screen import show_auth_screen
from audio_manager import init_audio
from network import Network
from high_scores import show_high_scores
from ship import Ship
import options

# Inicjalizacja Pygame
pygame.init()

# Inicjalizacja Dźwięków i Muzyki w tle
init_audio()

# Otwarcie w trybie pełnoekranowym z natywną rozdzielczością 1920x1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Statki - Menu Główne")
clock = pygame.time.Clock()

def preload_assets(screen):
    """Pre-load ciężkich zasobów, aby uniknąć przycięć w trakcie gry."""
    font_loading = pygame.font.SysFont("arial", 30)
    
    def show_progress(text):
        screen.fill((20, 20, 30))
        txt = font_loading.render(text, True, (200, 200, 200))
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()

    show_progress("Ładowanie floty...")
    for length in [1, 2, 3, 4]:
        Ship(length) # To wywoła ładowanie do _image_cache w klasie Ship

    show_progress("Przygotowywanie animacji...")
    # Pre-renderowanie animacji w standardowych rozmiarach (z game.py)
    cell_size = 68
    explosion_anim_size = (int(cell_size * 1.8), int(cell_size * 1.8))
    splash_anim_size = (int(cell_size * 1.0), int(cell_size * 1.0))
    smoke_anim_size = (int(cell_size * 1.0), int(cell_size * 1.0))
    
    game.load_spritesheet("wybuch.png", 6, 8, explosion_anim_size)
    game.load_spritesheet("plusk2.png", 6, 8, splash_anim_size)
    game.load_spritesheet("smoke.png", 6, 8, smoke_anim_size, start_frame=16, end_frame=40)

# Preload przed wejściem do menu
preload_assets(screen)

font_title = pygame.font.SysFont("arial", 120, bold=True)
font_button = pygame.font.SysFont("arial", 50)


def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)


def main_menu(player_name, net, background_image):
    """Główne menu uruchamiane po pomyślnym zalogowaniu."""
    btn_width = 320
    start_x = WIDTH // 2 - btn_width // 2
    start_y = 400
    spacing = 110

    btn_play = ImageButton(start_x, start_y, "graj.png", width=btn_width)
    btn_scores = ImageButton(start_x, start_y + spacing, "top wyniki.png", width=btn_width)
    btn_options = ImageButton(WIDTH // 2 - 310 // 2, start_y + spacing * 2.2, "opcje.png", width=310, height=95)
    btn_credits = ImageButton(start_x, start_y + spacing * 3, "tworcy.png", width=btn_width)
    # Proporcjonalny przycisk wyjścia
    btn_exit = ImageButton(WIDTH // 2 - 110, start_y + spacing * 4.3, "wyjście.png", width=220)

    buttons = [btn_play, btn_scores, btn_options, btn_credits, btn_exit]

    # Ładowanie loga PNG zamiast tekstu
    try:
        title_img = pygame.image.load("Gra Statki.png").convert_alpha()
        target_width = 700
        ratio = target_width / title_img.get_width()
        title_img = pygame.transform.smoothscale(title_img, (target_width, int(title_img.get_height() * ratio)))
        title_rect = title_img.get_rect(center=(WIDTH // 2, 200))
    except Exception as e:
        print(f"Błąd ładowania logo: {e}")
        title_img = None

    while True:
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BG_COLOR)

        if title_img:
            screen.blit(title_img, title_rect)
        else:
            draw_text('GRA STATKI', font_title, TEXT_COLOR, screen, WIDTH // 2, 200)

        # Powitanie zalogowanego gracza w menu
        welcome_surf = pygame.font.SysFont("arial", 40).render(f"Zalogowano jako: {player_name}", True, (150, 200, 255))
        screen.blit(welcome_surf, (20, 20))

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

            if btn_play.handle_event(event):
                match_choice = game.matchmaking_menu(screen, background_image)
                if match_choice:
                    try:
                        response = net.send(match_choice)
                        if response and response.get("status") in ["waiting", "room_created"]:
                            r_code = response.get("room_code")
                            msg = "Szukanie przeciwnika..." if not r_code else "Oczekiwanie na znajomego..."
                            opponent = game.waiting_screen(screen, background_image, net, msg, r_code)
                            if opponent:
                                game.play_game(screen, player_name, opponent, net, background_image)
                        elif response and response.get("status") == "game_start":
                            game.play_game(screen, player_name, response.get("opponent"), net, background_image)
                    except Exception as e:
                        print(f"Błąd sieci: {e}")

            if btn_scores.handle_event(event):
                show_high_scores(screen, clock, net, background_image)
            if btn_options.handle_event(event):
                show_options(screen, clock, background_image)
            if btn_credits.handle_event(event):
                show_credits(screen, clock, background_image)
            if btn_exit.handle_event(event):
                pygame.quit(); sys.exit()

        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(options.current_fps)


if __name__ == "__main__":
    try:
        global_net = Network()
    except Exception as e:
        print("Nie można połączyć z serwerem.")
        sys.exit()

    try:
        background_image_raw = pygame.image.load(BACKGROUND_IMAGE_FILENAME).convert()
        background_image = pygame.transform.scale(background_image_raw, (WIDTH, HEIGHT))
    except:
        background_image = None

    logged_player_data = show_auth_screen(screen, clock, global_net, background_image)
    if logged_player_data:
        player_name, response = logged_player_data
        if response.get("status") == "reconnected":
            # Gracz wrócił do gry
            game.play_game(screen, player_name, response.get("opponent"), global_net, background_image, reconnect_data=response)
        else:
            main_menu(player_name, global_net, background_image)
