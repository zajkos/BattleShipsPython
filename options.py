import pygame
import sys
from settings import *
from button import Button

current_volume = 0.5  # Głośność muzyki (0.0 do 1.0)
sfx_enabled = True  # Czy efekty dźwiękowe są włączone

# Nowe opcje animacji
explosions_enabled = True
splash_enabled = True
smoke_enabled = False

# Limit FPS
fps_limits = [30, 60, 120, 144, 240, 360]
fps_index = 5  # Domyślnie 360
current_fps = fps_limits[fps_index]


def show_options(screen, clock, background=None):
    global current_volume, sfx_enabled, explosions_enabled, splash_enabled, smoke_enabled, fps_index, current_fps

    font_header = pygame.font.SysFont("arial", 80, bold=True)
    font_text = pygame.font.SysFont("arial", 40)

    # Przyciski do regulacji głośności (+ i -)
    btn_vol_minus = Button(WIDTH // 2 - 180, 220, 80, 60, "-", font_header)
    btn_vol_plus = Button(WIDTH // 2 + 100, 220, 80, 60, "+", font_header)

    # Przycisk do włączania/wyłączania SFX
    btn_sfx = Button(WIDTH // 2 - 200, 330, 400, 50, "Zmień SFX", font_text)

    # Przyciski animacji
    btn_toggle_exp = Button(WIDTH // 2 - 200, 440, 400, 50, "Wybuchy: ON/OFF", font_text)
    btn_toggle_spl = Button(WIDTH // 2 - 200, 530, 400, 50, "Pluski: ON/OFF", font_text)
    btn_toggle_smo = Button(WIDTH // 2 - 200, 620, 400, 50, "Dym: ON/OFF", font_text)
    
    # Przycisk FPS
    btn_fps = Button(WIDTH // 2 - 200, 750, 400, 60, "Zmień Limit FPS", font_text)

    # Przycisk powrotu
    btn_back = Button(WIDTH // 2 - 200, HEIGHT - 100, 400, 70, "Powrót", font_text)

    # Optymalizacja: Pre-renderowanie statycznych napisów
    header_surf = font_header.render("OPCJE GRY", True, TEXT_COLOR)
    header_rect = header_surf.get_rect(center=(WIDTH // 2, 80))

    running = True
    while running:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()

        # 1. Rysowanie Nagłówka
        screen.blit(header_surf, header_rect)

        # 2. Głośność
        vol_text = f"Głośność Muzyki: {int(current_volume * 100)}%"
        vol_surf = font_text.render(vol_text, True, TEXT_COLOR)
        screen.blit(vol_surf, vol_surf.get_rect(center=(WIDTH // 2, 175)))

        # 3. SFX
        sfx_status = "WŁĄCZONE" if sfx_enabled else "WYŁĄCZONE"
        sfx_color = (50, 205, 50) if sfx_enabled else (200, 50, 50)
        sfx_label = font_text.render(f"SFX: {sfx_status}", True, sfx_color)
        screen.blit(sfx_label, sfx_label.get_rect(center=(WIDTH // 2, 300)))

        # 4. Toggles Animacji
        exp_color = (50, 205, 50) if explosions_enabled else (200, 50, 50)
        exp_txt = font_text.render(f"Wybuchy: {'TAK' if explosions_enabled else 'NIE'}", True, exp_color)
        screen.blit(exp_txt, exp_txt.get_rect(center=(WIDTH // 2, 410)))

        spl_color = (50, 205, 50) if splash_enabled else (200, 50, 50)
        spl_txt = font_text.render(f"Pluski: {'TAK' if splash_enabled else 'NIE'}", True, spl_color)
        screen.blit(spl_txt, spl_txt.get_rect(center=(WIDTH // 2, 500)))

        smo_color = (50, 205, 50) if smoke_enabled else (200, 50, 50)
        smo_txt = font_text.render(f"Dym: {'TAK' if smoke_enabled else 'NIE'}", True, smo_color)
        screen.blit(smo_txt, smo_txt.get_rect(center=(WIDTH // 2, 590)))
        
        # 5. FPS Display
        fps_label = font_text.render(f"Limit FPS: {current_fps}", True, (255, 255, 100))
        screen.blit(fps_label, fps_label.get_rect(center=(WIDTH // 2, 710)))

        # Obsługa Zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if btn_back.handle_event(event):
                running = False

            if btn_vol_minus.handle_event(event):
                current_volume = max(0.0, current_volume - 0.1)
                pygame.mixer.music.set_volume(current_volume)

            if btn_vol_plus.handle_event(event):
                current_volume = min(1.0, current_volume + 0.1)
                pygame.mixer.music.set_volume(current_volume)

            if btn_sfx.handle_event(event):
                sfx_enabled = not sfx_enabled
            
            if btn_toggle_exp.handle_event(event):
                explosions_enabled = not explosions_enabled
            
            if btn_toggle_spl.handle_event(event):
                splash_enabled = not splash_enabled
                
            if btn_toggle_smo.handle_event(event):
                smoke_enabled = not smoke_enabled
            
            if btn_fps.handle_event(event):
                fps_index = (fps_index + 1) % len(fps_limits)
                current_fps = fps_limits[fps_index]

        # Rysowanie przycisków
        for btn in [btn_vol_minus, btn_vol_plus, btn_sfx, btn_toggle_exp, btn_toggle_spl, btn_toggle_smo, btn_fps, btn_back]:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(current_fps)