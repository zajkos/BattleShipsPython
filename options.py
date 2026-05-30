import pygame
import sys
import json
import os
from settings import *
from button import Button, ImageButton

SETTINGS_FILE = "settings_save.json"

# Domyślne wartości
current_volume = 0.5
sfx_enabled = True
explosions_enabled = True
splash_enabled = True
smoke_enabled = False
fps_limits = [30, 60, 120, 144, 240, 360, 1000]
fps_labels = ["30", "60", "120", "144", "240", "360", "MAX"]
fps_index = 5  # 360
current_fps = fps_limits[fps_index]

def save_settings():
    """Zapisuje aktualne ustawienia do pliku JSON."""
    data = {
        "volume": current_volume,
        "sfx": sfx_enabled,
        "explosions": explosions_enabled,
        "splash": splash_enabled,
        "smoke": smoke_enabled,
        "fps_index": fps_index
    }
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Błąd zapisu ustawień: {e}")

def load_settings():
    """Wczytuje ustawienia z pliku JSON."""
    global current_volume, sfx_enabled, explosions_enabled, splash_enabled, smoke_enabled, fps_index, current_fps
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                current_volume = data.get("volume", 0.5)
                sfx_enabled = data.get("sfx", True)
                explosions_enabled = data.get("explosions", True)
                splash_enabled = data.get("splash", True)
                smoke_enabled = data.get("smoke", False)
                fps_index = data.get("fps_index", 5)
                if fps_index >= len(fps_limits): fps_index = 1
                current_fps = fps_limits[fps_index]
        except Exception as e:
            print(f"Błąd wczytywania ustawień: {e}")

# Wczytaj ustawienia przy starcie modułu
load_settings()

def show_options(screen, clock, background=None):

    global current_volume, sfx_enabled, explosions_enabled, splash_enabled, smoke_enabled, fps_index, current_fps

    font_header = pygame.font.SysFont("arial", 80, bold=True)
    font_text = pygame.font.SysFont("arial", 45)

    # Przyciski klasyczne (lista pionowa)
    btn_w = 320
    start_x = WIDTH // 2 - btn_w // 2
    start_y = 350 # Przesunięte w górę aby wszystko się zmieściło
    spacing = 110
    
    btn_vol_minus = Button(WIDTH // 2 - 160, 250, 70, 70, "-", font_header)
    btn_vol_plus = Button(WIDTH // 2 + 90, 250, 70, 70, "+", font_header)
    
    btn_sfx = Button(start_x, start_y, btn_w, 70, "SFX: ON/OFF", font_text)
    btn_toggle_exp = Button(start_x, start_y + spacing, btn_w, 70, "Wybuchy: ON/OFF", font_text)
    btn_toggle_spl = Button(start_x, start_y + spacing * 2, btn_w, 70, "Pluski: ON/OFF", font_text)
    btn_toggle_smo = Button(start_x, start_y + spacing * 3, btn_w, 70, "Dym: ON/OFF", font_text)
    btn_fps = Button(start_x, start_y + spacing * 4, btn_w, 70, "Limit FPS: " + fps_labels[fps_index], font_text)
    
    btn_back = ImageButton(WIDTH // 2 - 110, start_y + spacing * 5, "powrót.png", width=220)

    while True:
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        mouse_pos = pygame.mouse.get_pos()

        # Tytuł
        title_surf = font_header.render("OPCJE GRY", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 100)))

        # Głośność Info
        vol_label = font_text.render(f"Głośność Muzyki: {int(current_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(vol_label, vol_label.get_rect(center=(WIDTH // 2, 210)))

        # Statusy (podpowiedzi tekstowe obok przycisków lub wewnątrz)
        btn_sfx.text = f"Dźwięki: {'WŁ.' if sfx_enabled else 'WYŁ.'}"
        btn_toggle_exp.text = f"Wybuchy: {'WŁ.' if explosions_enabled else 'WYŁ.'}"
        btn_toggle_spl.text = f"Pluski: {'WŁ.' if splash_enabled else 'WYŁ.'}"
        btn_toggle_smo.text = f"Dym: {'WŁ.' if smoke_enabled else 'WYŁ.'}"
        btn_fps.text = "FPS: " + (fps_labels[fps_index] if fps_labels[fps_index] != "MAX" else "BEZ LIMITU")
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if btn_back.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return

            if btn_vol_minus.handle_event(event):
                current_volume = max(0.0, current_volume - 0.1)
                pygame.mixer.music.set_volume(current_volume)

            if btn_vol_plus.handle_event(event):
                current_volume = min(1.0, current_volume + 0.1)
                pygame.mixer.music.set_volume(current_volume)

            if btn_sfx.handle_event(event): sfx_enabled = not sfx_enabled
            if btn_toggle_exp.handle_event(event): explosions_enabled = not explosions_enabled
            if btn_toggle_spl.handle_event(event): splash_enabled = not splash_enabled
            if btn_toggle_smo.handle_event(event): smoke_enabled = not smoke_enabled
            
            if btn_fps.handle_event(event):
                fps_index = (fps_index + 1) % len(fps_limits)
                current_fps = fps_limits[fps_index]

        # Rysowanie wszystkich przycisków
        all_btns = [btn_vol_minus, btn_vol_plus, btn_sfx, btn_toggle_exp, btn_toggle_spl, btn_toggle_smo, btn_fps, btn_back]
        for b in all_btns:
            b.check_hover(mouse_pos)
            b.draw(screen)

        pygame.display.update()
        clock.tick(current_fps)
