import pygame
import sys
import re
import hashlib
from settings import *
import options
from button import Button, ImageButton


class InputBox:
    def __init__(self, x, y, w, h, text='', is_password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100, 100, 100)
        self.color_active = BUTTON_HOVER_COLOR
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
                elif event.unicode.isalnum() and len(self.text) < 20:
                    self.text += event.unicode

                # Renderowanie tekstu (gwiazdki jeśli to hasło)
                display_text = '*' * len(self.text) if self.is_password else self.text
                self.txt_surface = self.font.render(display_text, True, TEXT_COLOR)

    def draw(self, screen):
        # Rysowanie tekstu
        screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 10))
        # Rysowanie ramki
        pygame.draw.rect(screen, self.color, self.rect, 5, border_radius=5)


def check_password_strength(password):
    if len(password) < 8:
        return False, "Hasło musi mieć min. 8 znaków."
    if not re.search(r"[a-z]", password):
        return False, "Hasło musi mieć min. 1 małą literę."
    if not re.search(r"[A-Z]", password):
        return False, "Hasło musi mieć min. 1 dużą literę."
    if not re.search(r"\d", password):
        return False, "Hasło musi mieć min. 1 cyfrę."
    if not re.search(r"[!@#$%^&*()\-_\=+\[\]\{\}\\\|\;\:\'\"\,\.\<\>\/\?]", password):
        return False, "Hasło musi mieć min. 1 znak specjalny."
    return True, ""


def show_auth_screen(screen, clock, net, background=None):
    font_header = pygame.font.SysFont("arial", 60, bold=True)
    font_msg = pygame.font.SysFont("arial", 30)
    font_label = pygame.font.SysFont("arial", 30, bold=True)

    input_login = InputBox(WIDTH // 2 - 200, 320, 400, 60)
    input_password = InputBox(WIDTH // 2 - 200, 450, 400, 60, is_password=True)

    # Fokus na Login
    input_login.active = True
    input_login.color = input_login.color_active

    # Przywrócenie ImageButtonów
    bw = 240
    btn_login = ImageButton(WIDTH // 2 - bw // 2, 580, "zaloguj.png", width=bw)
    btn_register = ImageButton(WIDTH // 2 - bw // 2, 700, "zarejestruj.png", width=bw)
    btn_exit = ImageButton(WIDTH // 2 - bw // 2, 820, "wyjście.png", width=bw)

    message = ""
    message_color = TEXT_COLOR

    try:
        header_img = pygame.image.load("logowanie duże.png").convert_alpha()
        # Przycięcie przezroczystości i skalowanie
        header_rect_img = header_img.get_bounding_rect()
        if header_rect_img.width > 0 and header_rect_img.height > 0:
            header_img = header_img.subsurface(header_rect_img)
        # Skalowanie do rozsądnej szerokości, np. 500px
        target_w = 500
        ratio = target_w / header_img.get_width()
        header_img = pygame.transform.smoothscale(header_img, (target_w, int(header_img.get_height() * ratio)))
        header_rect = header_img.get_rect(center=(WIDTH // 2, 150))
    except:
        header_img = font_header.render("LOGOWANIE", True, TEXT_COLOR)
        header_rect = header_img.get_rect(center=(WIDTH // 2, 150))

    login_label = font_label.render("Login:", True, TEXT_COLOR)
    password_label = font_label.render("Hasło:", True, TEXT_COLOR)

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()

        if isinstance(header_img, pygame.Surface):
            screen.blit(header_img, header_rect)
        else:
            screen.blit(header_img, header_rect)
        screen.blit(login_label, (WIDTH // 2 - 200, 280))
        screen.blit(password_label, (WIDTH // 2 - 200, 410))

        if message:
            msg_surf = font_msg.render(message, True, message_color)
            screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 980)))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                input_login.active = not input_login.active
                input_password.active = not input_password.active
                input_login.color = input_login.color_active if input_login.active else input_login.color_inactive
                input_password.color = input_password.color_active if input_password.active else input_password.color_inactive
                continue

            input_login.handle_event(event)
            input_password.handle_event(event)

            if btn_exit.handle_event(event):
                pygame.quit(); sys.exit()

            if btn_login.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                if not input_login.text or not input_password.text:
                    message, message_color = "Wypełnij oba pola!", (200, 50, 50)
                else:
                    response = net.send({"action": "login", "username": input_login.text, "password": input_password.text})
                    if response and response.get("status") in ["success", "reconnected"]:
                        return input_login.text, response
                    elif response:
                        message, message_color = response.get("message", "Błąd logowania!"), (200, 50, 50)
                    else:
                        message, message_color = "Błąd: Brak połączenia z serwerem!", (200, 50, 50)

            if btn_register.handle_event(event):
                if not input_login.text or not input_password.text:
                    message, message_color = "Wypełnij oba pola!", (200, 50, 50)
                else:
                    is_strong, err_msg = check_password_strength(input_password.text)
                    if not is_strong:
                        message, message_color = err_msg, (200, 50, 50)
                    else:
                        response = net.send({"action": "register", "username": input_login.text, "password": input_password.text})
                    if response and response.get("status") == "success":
                        message, message_color = "Rejestracja udana!", (50, 205, 50)
                    elif response:
                        message, message_color = response.get("message", "Użytkownik już istnieje!"), (200, 50, 50)
                    else:
                        message, message_color = "Błąd: Brak połączenia z serwerem!", (200, 50, 50)

        input_login.draw(screen)
        input_password.draw(screen)

        for btn in [btn_login, btn_register, btn_exit]:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(options.current_fps)
