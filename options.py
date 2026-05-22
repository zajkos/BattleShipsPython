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

    font_huge = pygame.font.SysFont("arial", 90, bold=True)
    font_header = pygame.font.SysFont("arial", 45, bold=True)
    font_text = pygame.font.SysFont("arial", 32)
    font_btn = pygame.font.SysFont("arial", 28, bold=True)

    # --- ELEMENTY INTERFEJSU ---
    
    # Kolumny i Panele
    panel_width = 600
    panel_height = 650
    panel_y = 200
    
    left_panel_x = WIDTH // 2 - panel_width - 20
    right_panel_x = WIDTH // 2 + 20
    
    # Przycisk powrotu na samym dole, wyśrodkowany
    btn_back = Button(WIDTH // 2 - 200, HEIGHT - 100, 400, 70, "ZAPISZ I WRÓĆ", font_header)

    # Przyciski LEWY PANEL (DŹWIĘK)
    btn_vol_minus = Button(left_panel_x + 100, panel_y + 150, 80, 60, "-", font_huge)
    btn_vol_plus = Button(left_panel_x + panel_width - 180, panel_y + 150, 80, 60, "+", font_huge)
    btn_sfx = Button(left_panel_x + 100, panel_y + 350, 400, 60, "PRZEŁĄCZ SFX", font_btn)

    # Przyciski PRAWY PANEL (GRAFIKA)
    btn_toggle_exp = Button(right_panel_x + 100, panel_y + 120, 400, 50, "WYBUCHY", font_btn)
    btn_toggle_spl = Button(right_panel_x + 100, panel_y + 220, 400, 50, "PLUSKI WODY", font_btn)
    btn_toggle_smo = Button(right_panel_x + 100, panel_y + 320, 400, 50, "DYM", font_btn)
    btn_fps = Button(right_panel_x + 100, panel_y + 480, 400, 60, "ZMIEŃ LIMIT FPS", font_btn)

    # --- PRE-RENDERING STATYCZNY ---
    title_surf = font_huge.render("USTAWIENIA", True, (255, 215, 0))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 90))

    audio_header = font_header.render("AUDIO", True, (0, 255, 255))
    graphics_header = font_header.render("GRAFIKA", True, (0, 255, 255))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    running = True
    while running:
        if background:
            screen.blit(background, (0, 0))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()

        # Rysowanie paneli (efekt szklanych kart)
        for px in [left_panel_x, right_panel_x]:
            # Cień/Tło
            pygame.draw.rect(screen, (40, 40, 60), (px, panel_y, panel_width, panel_height), border_radius=20)
            # Ramka świecąca
            pygame.draw.rect(screen, (0, 255, 255, 80), (px, panel_y, panel_width, panel_height), width=2, border_radius=20)

        screen.blit(title_surf, title_rect)
        
        # Nagłówki sekcji
        screen.blit(audio_header, audio_header.get_rect(center=(left_panel_x + panel_width // 2, panel_y + 40)))
        screen.blit(graphics_header, graphics_header.get_rect(center=(right_panel_x + panel_width // 2, panel_y + 40)))

        # --- LEWA KOLUMNA (AUDIO) ---
        vol_label = font_text.render(f"Głośność Muzyki: {int(current_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(vol_label, vol_label.get_rect(center=(left_panel_x + panel_width // 2, panel_y + 120)))
        
        # Pasek głośności (wizualny)
        bar_x = left_panel_x + 100
        bar_y = panel_y + 230
        bar_w = panel_width - 200
        pygame.draw.rect(screen, (20, 20, 40), (bar_x, bar_y, bar_w, 20), border_radius=10)
        pygame.draw.rect(screen, (0, 255, 255), (bar_x, bar_y, int(bar_w * current_volume), 20), border_radius=10)

        sfx_status = "AKTYWNE" if sfx_enabled else "WYCISZONE"
        sfx_color = (100, 255, 100) if sfx_enabled else (255, 100, 100)
        sfx_label = font_text.render(f"Efekty SFX: {sfx_status}", True, sfx_color)
        screen.blit(sfx_label, sfx_label.get_rect(center=(left_panel_x + panel_width // 2, panel_y + 320)))

        # --- PRAWA KOLUMNA (GRAFIKA) ---
        def draw_toggle_stat(label, val, y):
            color = (100, 255, 100) if val else (255, 100, 100)
            txt = font_text.render(f"{label}: {'ON' if val else 'OFF'}", True, color)
            screen.blit(txt, (right_panel_x + 50, y))

        draw_toggle_stat("Wybuchy", explosions_enabled, panel_y + 125)
        draw_toggle_stat("Pluski", splash_enabled, panel_y + 225)
        draw_toggle_stat("Dym", smoke_enabled, panel_y + 325)
        
        fps_label = font_text.render(f"Limit Klatek: {current_fps} FPS", True, (255, 255, 100))
        screen.blit(fps_label, fps_label.get_rect(center=(right_panel_x + panel_width // 2, panel_y + 440)))

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
        all_buttons = [btn_vol_minus, btn_vol_plus, btn_sfx, btn_toggle_exp, btn_toggle_spl, btn_toggle_smo, btn_fps, btn_back]
        for btn in all_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen)

        pygame.display.update()
        clock.tick(current_fps)
