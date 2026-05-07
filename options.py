import pygame
import sys
from settings import *
from button import Button

current_volume = 0.5  # Głośność muzyki (0.0 do 1.0)
sfx_enabled = True  # Czy efekty dźwiękowe są włączone


def show_options(screen, clock):
    global current_volume, sfx_enabled

    font_header = pygame.font.SysFont("arial", 80, bold=True)
    font_text = pygame.font.SysFont("arial", 45)
    font_small = pygame.font.SysFont("arial", 30)

    # Przyciski do regulacji głośności (+ i -)
    btn_vol_minus = Button(WIDTH // 2 - 180, 350, 80, 80, "-", font_header)
    btn_vol_plus = Button(WIDTH // 2 + 100, 350, 80, 80, "+", font_header)

    # Przycisk do włączania/wyłączania SFX
    btn_sfx = Button(WIDTH // 2 - 200, 550, 400, 80, "WYŁĄCZ/WŁĄCZ", font_text)

    # Przycisk powrotu
    btn_back = Button(WIDTH // 2 - 200, HEIGHT - 150, 400, 80, "Powrót", font_text)

    running = True
    while running:
        screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        # 1. Rysowanie Nagłówka
        header_surf = font_header.render("OPCJE GRY", True, TEXT_COLOR)
        screen.blit(header_surf, header_surf.get_rect(center=(WIDTH // 2, 150)))

        # 2. Rysowanie sekcji Głośności Muzyki
        vol_text = f"Głośność Muzyki: {int(current_volume * 100)}%"
        vol_surf = font_text.render(vol_text, True, TEXT_COLOR)
        screen.blit(vol_surf, vol_surf.get_rect(center=(WIDTH // 2, 280)))

        # 3. Rysowanie sekcji Efektów Dźwiękowych
        sfx_status = "WŁĄCZONE" if sfx_enabled else "WYŁĄCZONE"
        sfx_color = (50, 205, 50) if sfx_enabled else (200, 50, 50)  # Zielony / Czerwony

        sfx_label_surf = font_text.render("Efekty Dźwiękowe (SFX):", True, TEXT_COLOR)
        screen.blit(sfx_label_surf, sfx_label_surf.get_rect(center=(WIDTH // 2, 480)))

        sfx_status_surf = font_text.render(sfx_status, True, sfx_color)
        screen.blit(sfx_status_surf, sfx_status_surf.get_rect(center=(WIDTH // 2, 530)))

        # 4. Obsługa Zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if btn_back.handle_event(event):
                running = False

            # Zmniejszanie głośności (zabezpieczenie min = 0.0)
            if btn_vol_minus.handle_event(event):
                current_volume = max(0.0, current_volume - 0.1)
                pygame.mixer.music.set_volume(current_volume)  # Aktualizuje na żywo w Pygame

            # Zwiększanie głośności (zabezpieczenie max = 1.0)
            if btn_vol_plus.handle_event(event):
                current_volume = min(1.0, current_volume + 0.1)
                pygame.mixer.music.set_volume(current_volume)  # Aktualizuje na żywo w Pygame

            # Przełączanie SFX
            if btn_sfx.handle_event(event):
                sfx_enabled = not sfx_enabled

        # 5. Aktualizacja i rysowanie przycisków
        btn_vol_minus.check_hover(mouse_pos)
        btn_vol_minus.draw(screen)

        btn_vol_plus.check_hover(mouse_pos)
        btn_vol_plus.draw(screen)

        btn_sfx.check_hover(mouse_pos)
        btn_sfx.draw(screen)

        btn_back.check_hover(mouse_pos)
        btn_back.draw(screen)

        pygame.display.update()
        clock.tick(FPS)