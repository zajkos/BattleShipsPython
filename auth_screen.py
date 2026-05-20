import pygame
import sys
import re
from settings import *
from button import Button


class InputBox:
    def __init__(self, x, y, w, h, text='', is_password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.font = pygame.font.SysFont("arial", 40)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self.is_password = is_password

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Aktywacja po kliknięciu myszką
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    pass  # Zostawiamy do obsługi w głównej pętli
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode.isalnum():  # --- NOWOŚĆ: Blokada znaków specjalnych i spacji ---
                    self.text += event.unicode

                # Renderowanie tekstu (gwiazdki jeśli to hasło)
                display_text = '*' * len(self.text) if self.is_password else self.text
                self.txt_surface = self.font.render(display_text, True, TEXT_COLOR)

    def draw(self, screen):
        # Rysowanie tekstu
        screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 10))
        # Rysowanie ramki
        pygame.draw.rect(screen, self.color, self.rect, 3, border_radius=5)


def check_password_strength(password):
    """Sprawdza siłę hasła (tylko litery i cyfry ze względu na isalnum)."""
    if len(password) < 8:
        return False, "Hasło musi mieć min. 8 znaków."
    if not re.search(r"[A-Z]", password):
        return False, "Hasło musi zawierać wielką literę."
    if not re.search(r"\d", password):
        return False, "Hasło musi zawierać cyfrę."
    return True, "Hasło jest silne."


def show_auth_screen(screen, clock, net):
    font_header = pygame.font.SysFont("arial", 60, bold=True)
    font_msg = pygame.font.SysFont("arial", 30)

    input_login = InputBox(WIDTH // 2 - 200, 200, 400, 60)
    input_password = InputBox(WIDTH // 2 - 200, 300, 400, 60, is_password=True)

    # --- NOWOŚĆ: Fokus od razu na polu Login ---
    input_login.active = True
    input_login.color = input_login.color_active

    btn_login = Button(WIDTH // 2 - 200, 400, 190, 60, "Zaloguj", font_msg)
    btn_register = Button(WIDTH // 2 + 10, 400, 190, 60, "Zarejestruj", font_msg)
    btn_exit = Button(WIDTH // 2 - 100, 500, 200, 60, "Wyjście", font_msg)

    message = ""
    message_color = TEXT_COLOR

    running = True
    while running:
        screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        header_surf = font_header.render("LOGOWANIE", True, TEXT_COLOR)
        screen.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, 100)))

        # Rysowanie etykiet
        screen.blit(font_msg.render("Login:", True, TEXT_COLOR), (WIDTH // 2 - 200, 160))
        screen.blit(font_msg.render("Hasło:", True, TEXT_COLOR), (WIDTH // 2 - 200, 260))

        # Wiadomości systemowe (błędy/sukces)
        if message:
            msg_surf = font_msg.render(message, True, message_color)
            screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 600)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- NOWOŚĆ: Nawigacja klawiszem TAB ---
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                input_login.active = not input_login.active
                input_password.active = not input_password.active

                input_login.color = input_login.color_active if input_login.active else input_login.color_inactive
                input_password.color = input_password.color_active if input_password.active else input_password.color_inactive
                continue  # Przerywamy iterację, żeby TAB nie dodał się jako znak do pola tekstowego

            input_login.handle_event(event)
            input_password.handle_event(event)

            if btn_exit.handle_event(event):
                pygame.quit()
                sys.exit()

            if btn_login.handle_event(event):
                if not input_login.text or not input_password.text:
                    message, message_color = "Wypełnij oba pola!", (200, 50, 50)
                else:
                    response = net.send(
                        {"action": "login", "username": input_login.text, "password": input_password.text})
                    if response.get("status") == "success":
                        return input_login.text  # Zwracamy nick, logowanie udane!
                    else:
                        message, message_color = response.get("message", "Błąd logowania!"), (200, 50, 50)

            if btn_register.handle_event(event):
                if not input_login.text or not input_password.text:
                    message, message_color = "Wypełnij oba pola!", (200, 50, 50)
                else:
                    is_strong, msg = check_password_strength(input_password.text)
                    if not is_strong:
                        message, message_color = msg, (200, 50, 50)
                    else:
                        response = net.send(
                            {"action": "register", "username": input_login.text, "password": input_password.text})
                        if response.get("status") == "success":
                            message, message_color = "Rejestracja udana! Możesz się zalogować.", (50, 205, 50)
                        else:
                            message, message_color = response.get("message", "Użytkownik już istnieje!"), (200, 50, 50)

        # Rysowanie elementów
        input_login.draw(screen)
        input_password.draw(screen)

        for btn in [btn_login, btn_register, btn_exit]:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(FPS)