# ship.py
import pygame
from settings import *

class Ship:
    # Statyczny cache dla obrazków (wspólny dla wszystkich instancji)
    _image_cache = {}

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

        # Pobieramy obrazek z cache lub ładujemy jeśli go nie ma
        self.image_raw = self._get_base_image()
        self.image = None
        self.dragging_image = None
        
        # Inicjalne przygotowanie grafiki
        if self.image_raw:
            self._update_image()

    def _get_base_image(self):
        cache_key = f"ship_{self.length}"
        if cache_key not in Ship._image_cache:
            try:
                # Ładowanie z dysku tylko RAZ dla danego typu statku
                img = pygame.image.load(f"ship_{self.length}.png").convert_alpha()
                Ship._image_cache[cache_key] = img
            except Exception:
                Ship._image_cache[cache_key] = None
        return Ship._image_cache[cache_key]

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
            if self.horizontal != is_img_horizontal:
                base_image = pygame.transform.rotate(self.image_raw, 90)
            else:
                base_image = self.image_raw
            
            # Skalujemy obrazek do wymiarów prostokąta statku
            self.image = pygame.transform.scale(base_image, (self.rect.width, self.rect.height))
            # Cache dla przeciągania
            self.dragging_image = self.image.copy()
            self.dragging_image.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)

    def draw(self, surface):
        if self.image:
            if self.dragging:
                surface.blit(self.dragging_image, self.rect)
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
        # Sprawdzamy czy zmiana jest konieczna
        target_w = self.length * new_cell_size if self.horizontal else new_cell_size
        target_h = new_cell_size if self.horizontal else self.length * new_cell_size
        
        if self.rect.width == target_w and self.rect.height == target_h and self.cell_size == new_cell_size:
            return

        self.cell_size = new_cell_size
        self.rect.width = target_w
        self.rect.height = target_h
        self._update_image()

    def update_to_tray_size(self, scale=0.8):
        target_w = int(self.length * (self.cell_size * scale))
        target_h = int(self.cell_size * scale)
        
        self.horizontal = True # Zawsze poziomo w zasobniku
        self.rect.width = target_w
        self.rect.height = target_h
        self._update_image()
