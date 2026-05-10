# audio_manager.py
import pygame
import random
import os
import options

# Ścieżka do folderu z dźwiękami
AUDIO_DIR = "audio"

# Słownik przechowujący listy wczytanych dźwięków
sounds = {
    'click': [],
    'drop': [],
    'hit': [],
    'miss': [],
    'win': []
}


def load_sound_safe(filename):
    """Bezpiecznie wczytuje dźwięk z folderu audio. Jeśli pliku nie ma, zwraca None."""
    filepath = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(filepath):
        return pygame.mixer.Sound(filepath)
    else:
        print(f"[AUDIO OSTRZEŻENIE] Brak pliku: {filepath}")
        return None


def init_audio():
    """Inicjalizuje mixer i ładuje wszystkie pliki dźwiękowe do pamięci."""
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    # --- POJEDYNCZE DŹWIĘKI ---
    s_click = load_sound_safe('click.mp3')
    if s_click: sounds['click'].append(s_click)

    s_drop = load_sound_safe('drop.mp3')
    if s_drop: sounds['drop'].append(s_drop)

    # --- LOSOWE DŹWIĘKI ---
    # Dodaj więcej plików do folderu "audio" i dopisz ich nazwy do list poniżej
    for f in ['hit1.mp3', 'hit2.mp3', 'hit3.mp3', 'hit4.mp3', 'hit5.mp3', 'hit6.mp3', 'hit7.mp3', 'hit8.mp3']:
        s = load_sound_safe(f)
        if s: sounds['hit'].append(s)

    for f in ['miss1.mp3', 'miss2.mp3', 'miss3.mp3', 'miss4.mp3', 'miss5.mp3', 'miss6.mp3', 'miss7.mp3', 'miss8.mp3', 'miss9.mp3', 'miss10.mp3']:
        s = load_sound_safe(f)
        if s: sounds['miss'].append(s)

    for f in ['win1.mp3', 'win2.mp3', 'win3.mp3', 'win4.mp3', 'win5.mp3']:
        s = load_sound_safe(f)
        if s: sounds['win'].append(s)

    # --- MUZYKA W TLE ---
    music_path = os.path.join(AUDIO_DIR, 'music.mp3')
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(options.current_volume)
        pygame.mixer.music.play(-1)  # -1 oznacza zapętlenie muzyki w nieskończoność
    else:
        print(f"[AUDIO OSTRZEŻENIE] Brak pliku z muzyką: {music_path}")


def play_sfx(sound_type):
    """Odtwarza losowy dźwięk z kategorii, sprawdzając ustawienia z options.py."""
    if options.sfx_enabled and sound_type in sounds and sounds[sound_type]:
        sound_to_play = random.choice(sounds[sound_type])
        sound_to_play.set_volume(options.current_volume)
        sound_to_play.play()