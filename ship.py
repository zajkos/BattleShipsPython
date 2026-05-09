# ship.py
import pygame
from settings import *

class Ship:
    def __init__(self, length, color=(100, 100, 100)):
        self.length = length
        self.color = color
        self.horizontal = True
        self.cell_size = 80
        
        # Initial size for tray (50%)
        self.rect = pygame.Rect(0, 0, self.length * (self.cell_size // 2), self.cell_size // 2)
        
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        
        self.grid_pos = None
        self.initial_pos = (0, 0)

        # Image loading
        self.image_raw = None
        try:
            self.image_raw = pygame.image.load(f"ship_{self.length}.png").convert_alpha()
        except Exception:
            # Fallback if image not found
            self.image_raw = None
        
        self.image = None

    def rotate(self):
        """Standardowe przełączenie orientacji (zamiana szerokości i wysokości)."""
        self.horizontal = not self.horizontal
        self.rect.width, self.rect.height = self.rect.height, self.rect.width
        self._update_image()

    def _update_image(self):
        if self.image_raw:
            # Pobieramy wymiary oryginalnego obrazka
            img_w, img_h = self.image_raw.get_size()
            is_img_horizontal = img_w > img_h
            
            # Przygotowujemy bazowy obrazek - jeśli orientacja pliku nie pasuje do stanu statku, obracamy o 90 stopni
            # Robimy to PRZED skalowaniem, żeby uniknąć rozciągnięcia (stretching)
            if self.horizontal != is_img_horizontal:
                base_image = pygame.transform.rotate(self.image_raw, 90)
            else:
                base_image = self.image_raw
            
            # Teraz skalujemy już poprawnie zorientowany obrazek do wymiarów prostokąta statku
            self.image = pygame.transform.scale(base_image, (self.rect.width, self.rect.height))

    def draw(self, surface):
        if self.image:
            if self.dragging:
                # Efekt półprzezroczystości przy przeciąganiu
                temp_surface = self.image.copy()
                temp_surface.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(temp_surface, self.rect)
            else:
                surface.blit(self.image, self.rect)
        else:
            draw_color = (170, 170, 170) if self.dragging else self.color
            pygame.draw.rect(surface, draw_color, self.rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)

    def get_grid_cells(self, col, row):
        cells = []
        for i in range(self.length):
            if self.horizontal:
                cells.append((col + i, row))
            else:
                cells.append((col, row + i))
        return cells

    def update_to_grid_size(self, new_cell_size=80):
        self.cell_size = new_cell_size
        if self.horizontal:
            self.rect.width = self.length * self.cell_size
            self.rect.height = self.cell_size
        else:
            self.rect.width = self.cell_size
            self.rect.height = self.length * self.cell_size
        self._update_image()

    def update_to_tray_size(self):
        self.horizontal = True # Zawsze poziomo w zasobniku
        self.rect.width = self.length * (self.cell_size // 2)
        self.rect.height = self.cell_size // 2
        self._update_image()
