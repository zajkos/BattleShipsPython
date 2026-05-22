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
# 0 oznacza nielimitowane (brak synchronizacji lub bardzo wysoki limit)
fps_limits = [30, 60, 120, 144, 240, 360, 1000]
fps_labels = ["30", "60", "120", "144", "240", "360", "MAX"]
fps_index = 5  # Domyślnie 360
current_fps = fps_limits[fps_index]


def show_options(screen, clock, background=None):
    global current_volume, sfx_enabled, explosions_enabled, splash_enabled, smoke_enabled, fps_index, current_fps

    font_huge = pygame.font.SysFont("arial", 80, bold=True)
    font_header = pygame.font.SysFont("arial", 40, bold=True)
    font_text = pygame.font.SysFont("arial", 30)
    font_fps_val = pygame.font.SysFont("arial", 30, bold=True) # Jeszcze mniejsza czcionka dla wartości FPS
    font_small = pygame.font.SysFont("arial", 22)

    # --- KONFIGURACJA ROZMIESZCZENIA ---
    panel_w, panel_h = 1000, 750
    px = (WIDTH - panel_w) // 2
    py = (HEIGHT - panel_h) // 2

    # Definicje obszarów interaktywnych
    slider_rect = pygame.Rect(px + 100, py + 160, 800, 20)
    dragging_volume = False
    
    # Przycisk powrotu
    btn_back = Button(WIDTH // 2 - 200, py + panel_h - 90, 400, 70, "ZAPISZ I WRÓĆ", font_header)

    # Przyciski sterowania FPS (strzałki) - WYRÓWNANE DO PRAWEJ
    # < na poziomie kolumny statusu, > na poziomie końca przycisków
    btn_fps_prev = Button(px + 450, py + 575, 50, 50, "<", font_header)
    btn_fps_next = Button(px + 750, py + 575, 50, 50, ">", font_header)
    
    # Przyciski przełączające
    btn_toggle_sfx = Button(px + 650, py + 240, 150, 45, "ZMIEŃ", font_small)
    btn_toggle_exp = Button(px + 650, py + 320, 150, 45, "ZMIEŃ", font_small)
    btn_toggle_spl = Button(px + 650, py + 400, 150, 45, "ZMIEŃ", font_small)
    btn_toggle_smo = Button(px + 650, py + 480, 150, 45, "ZMIEŃ", font_small)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))

    running = True
    while running:
        if background:
            screen.blit(background, (0, 0))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()

        # 1. Główny Panel
        pygame.draw.rect(screen, (35, 35, 55), (px, py, panel_w, panel_h), border_radius=30)
        pygame.draw.rect(screen, (0, 200, 255), (px, py, panel_w, panel_h), width=3, border_radius=30)

        # 2. Nagłówek
        title_surf = font_huge.render("USTAWIENIA", True, (255, 215, 0))
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, py + 60)))

        # --- SEKCJA AUDIO ---
        vol_label = font_text.render(f"Głośność Muzyki: {int(current_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(vol_label, (px + 100, py + 120))
        
        pygame.draw.rect(screen, (60, 60, 80), slider_rect, border_radius=10)
        pygame.draw.rect(screen, (0, 255, 255), (slider_rect.x, slider_rect.y, slider_rect.w * current_volume, slider_rect.h), border_radius=10)
        handle_x = slider_rect.x + (slider_rect.w * current_volume)
        pygame.draw.circle(screen, (255, 255, 255), (int(handle_x), slider_rect.centery), 15)

        sfx_label = font_text.render("Efekty Dźwiękowe (SFX):", True, TEXT_COLOR)
        screen.blit(sfx_label, (px + 100, py + 245))
        sfx_status_txt = "WŁĄCZONE" if sfx_enabled else "WYŁĄCZONE"
        sfx_color = (100, 255, 100) if sfx_enabled else (255, 100, 100)
        sfx_val_surf = font_text.render(sfx_status_txt, True, sfx_color)
        screen.blit(sfx_val_surf, (px + 450, py + 245))

        # --- SEKCJA GRAFIKA ---
        def draw_option_row(label, val, y_offset):
            lbl_surf = font_text.render(label, True, TEXT_COLOR)
            screen.blit(lbl_surf, (px + 100, py + y_offset))
            status_txt = "TAK" if val else "NIE"
            status_color = (100, 255, 100) if val else (255, 100, 100)
            val_surf = font_text.render(status_txt, True, status_color)
            screen.blit(val_surf, (px + 450, py + y_offset))

        draw_option_row("Animacje Wybuchów:", explosions_enabled, 325)
        draw_option_row("Animacje Plusków:", splash_enabled, 405)
        draw_option_row("Efekt Dymu:", smoke_enabled, 485)

        # FPS Control - WYRÓWNANE DO KOLUMN POWYŻEJ
        fps_title = font_text.render("Limit Klatek (FPS):", True, TEXT_COLOR)
        screen.blit(fps_title, (px + 100, py + 585))
        
        display_fps = fps_labels[fps_index] if fps_labels[fps_index] != "MAX" else "BEZ LIMITU"
        fps_val_surf = font_fps_val.render(display_fps, True, (255, 255, 100))
        # Centrujemy wartość między strzałkami
        screen.blit(fps_val_surf, fps_val_surf.get_rect(center=(px + 625, py + 600)))

        # Obsługa Zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Kliknięcie w suwak
                    if slider_rect.inflate(20, 40).collidepoint(event.pos):
                        dragging_volume = True
                        # Natychmiastowa aktualizacja
                        rel_x = max(0, min(slider_rect.w, event.pos[0] - slider_rect.x))
                        current_volume = rel_x / slider_rect.w
                        pygame.mixer.music.set_volume(current_volume)

                    # Obsługa przycisków przez ich handle_event
                    if btn_back.handle_event(event): running = False
                    if btn_fps_prev.handle_event(event):
                        fps_index = (fps_index - 1) % len(fps_limits)
                        current_fps = fps_limits[fps_index]
                    if btn_fps_next.handle_event(event):
                        fps_index = (fps_index + 1) % len(fps_limits)
                        current_fps = fps_limits[fps_index]
                    
                    if btn_toggle_sfx.handle_event(event): sfx_enabled = not sfx_enabled
                    if btn_toggle_exp.handle_event(event): explosions_enabled = not explosions_enabled
                    if btn_toggle_spl.handle_event(event): splash_enabled = not splash_enabled
                    if btn_toggle_smo.handle_event(event): smoke_enabled = not smoke_enabled

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_volume = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_volume:
                    rel_x = max(0, min(slider_rect.w, event.pos[0] - slider_rect.x))
                    current_volume = rel_x / slider_rect.w
                    pygame.mixer.music.set_volume(current_volume)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Rysowanie przycisków
        all_btns = [btn_back, btn_fps_prev, btn_fps_next, btn_toggle_sfx, btn_toggle_exp, btn_toggle_spl, btn_toggle_smo]
        for b in all_btns:
            b.check_hover(mouse_pos)
            b.draw(screen)

        pygame.display.update()
        # Menu opcji zawsze płynne, niezależnie od limitu gry (dla responsywności suwaka)
        clock.tick(max(60, current_fps if current_fps < 1000 else 360))
