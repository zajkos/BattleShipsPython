# main.py
import pygame
import sys
from settings import *
from button import Button
import game
from credits import show_credits
from options import show_options
from auth_screen import show_auth_screen
from audio_manager import init_audio
from network import Network

# Inicjalizacja Pygame
pygame.init()

# Inicjalizacja Dźwięków i Muzyki w tle
init_audio()

# Otwarcie w trybie pełnoekranowym z natywną rozdzielczością 1920x1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Statki - Menu Główne")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("arial", 120, bold=True)
font_button = pygame.font.SysFont("arial", 50)


def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)


def main_menu(player_name, net):
    """Główne menu uruchamiane po pomyślnym zalogowaniu."""
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

        # Powitanie zalogowanego gracza w menu
        welcome_surf = pygame.font.SysFont("arial", 40).render(f"Zalogowano jako: {player_name}", True, (150, 200, 255))
        screen.blit(welcome_surf, (20, 20))

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if btn_play.handle_event(event):
                # --- ZMIANA: Skaczemy od razu do matchmakingu, bo logowanie było na starcie! ---
                match_choice = game.matchmaking_menu(screen, background_image)
                if match_choice:
                    try:
                        # Wysyłamy wybrany tryb (Szybka Gra, Stwórz Pokój, Dołącz)
                        response = net.send(match_choice)

                        # Przechodzimy do logiki oczekiwania
                        if response and response.get("status") in ["waiting", "room_created"]:
                            r_code = response.get("room_code")
                            msg = "Szukanie przeciwnika..." if not r_code else "Oczekiwanie na znajomego..."

                            opponent = game.waiting_screen(screen, background_image, net, msg, r_code)
                            if opponent:
                                # Gra wystartowała!
                                status = game.play_game(screen, player_name, opponent, net)
                                if status == "MENU":
                                    print("Rozgrywka zakończona, powrót do menu.")
                            else:
                                print("Wrócono do menu lub przeciwnik uciekł.")

                        elif response and response.get("status") == "game_start":
                            # Znaleziono od razu (dołączono do kogoś)
                            status = game.play_game(screen, player_name, response.get("opponent"), net)
                            if status == "MENU":
                                print("Rozgrywka zakończona, powrót do menu.")
                        elif response:
                            print(f"Błąd dołączania: {response.get('message', 'Nieznany błąd')}")
                        else:
                            print("Błąd sieci: Brak odpowiedzi od serwera.")

                    except Exception as e:
                        print(f"Błąd sieci: {e}")

            if btn_scores.handle_event(event):
                print("Otwieranie Top Wyników (KAN-49)")
            if btn_options.handle_event(event):
                show_options(screen, clock)
            if btn_credits.handle_event(event):
                show_credits(screen, clock)
            if btn_exit.handle_event(event):
                pygame.quit()
                sys.exit()

        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    # --- NOWE FLOW APLIKACJI NA START ---
    try:
        global_net = Network()  # Połączenie nawiązywane tylko raz przy starcie
    except Exception as e:
        print("Nie można połączyć z serwerem. Upewnij się, że serwer jest uruchomiony.")
        sys.exit()

    # Wywołanie ekranu autoryzacji z przekazaniem połączenia sieciowego
    logged_player = show_auth_screen(screen, clock, global_net)

    # Jeśli gracz pomyślnie się zalogował, wchodzi do Menu Głównego
    if logged_player:
        main_menu(logged_player, global_net)