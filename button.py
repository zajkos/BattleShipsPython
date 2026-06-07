# button.py
import pygame
from settings import *

class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False
        # Cache wyrenderowanego tekstu
        self.text_surf = self.font.render(self.text, True, TEXT_COLOR)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        # Jeśli zmieniamy tekst, odświeżamy cache powierzchni
        if name == "text" and hasattr(self, 'font'):
            self.text_surf = self.font.render(self.text, True, TEXT_COLOR)
            self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, surface):
        # Wybór koloru w zależności od tego, czy myszka najechała na przycisk
        color = BUTTON_HOVER_COLOR if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=10)

        # Renderowanie tekstu na środku przycisku używając zbuforowanej powierzchni
        surface.blit(self.text_surf, self.text_rect)

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

class ImageButton:
    def __init__(self, x, y, image_path, width=None, height=None, scale=1.0):
        try:
            original_image = pygame.image.load(image_path).convert_alpha()
            # Zautomatyzowane przycięcie pustej, przezroczystej przestrzeni dookoła obrazka
            bounding_rect = original_image.get_bounding_rect()
            if bounding_rect.width > 0 and bounding_rect.height > 0:
                original_image = original_image.subsurface(bounding_rect)
        except:
            print(f"Błąd ładowania obrazu: {image_path}")
            original_image = pygame.Surface((200, 60))
            original_image.fill((255, 0, 0))
            
        if width is not None and height is not None:
            final_w, final_h = width, height
        elif width is not None:
            ratio = width / original_image.get_width()
            final_w, final_h = width, int(original_image.get_height() * ratio)
        elif height is not None:
            ratio = height / original_image.get_height()
            final_w, final_h = int(original_image.get_width() * ratio), height
        else:
            final_w, final_h = int(original_image.get_width() * scale), int(original_image.get_height() * scale)
            
        self.image = pygame.transform.smoothscale(original_image, (final_w, final_h))
        
        # Jaśniejsza wersja dla hover
        self.hover_image = self.image.copy()
        self.hover_image.fill((50, 50, 50, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.is_hovered = False

    def draw(self, surface):
        if self.is_hovered:
            surface.blit(self.hover_image, (self.rect.x, self.rect.y))
        else:
            surface.blit(self.image, (self.rect.x, self.rect.y))

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                from audio_manager import play_sfx
                play_sfx('click')
                return True
        return False
