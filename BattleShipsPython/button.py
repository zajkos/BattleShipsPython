# button.py
import pygame
from settings import *

class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False

    def draw(self, surface):
        # Wybór koloru w zależności od tego, czy myszka najechała na przycisk
        color = BUTTON_HOVER_COLOR if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=10)

        # Renderowanie tekstu na środku przycisku
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        """Sprawdza, czy myszka znajduje się nad przyciskiem."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        """Sprawdza, czy przycisk został kliknięty. Zwraca True/False."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 1 = lewy przycisk
            if self.is_hovered:
                # --- DODANO IMPORT I DŹWIĘK KLIKNIĘCIA ---
                from audio_manager import play_sfx
                play_sfx('click')
                return True
        return False