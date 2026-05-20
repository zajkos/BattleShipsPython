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

    def rotate(self):
        """Standardowe przełączenie orientacji (zamiana szerokości i wysokości)."""
        self.horizontal = not self.horizontal
        self.rect.width, self.rect.height = self.rect.height, self.rect.width

    def draw(self, surface):
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

    def update_to_grid_size(self):
        if self.horizontal:
            self.rect.width = self.length * self.cell_size
            self.rect.height = self.cell_size
        else:
            self.rect.width = self.cell_size
            self.rect.height = self.length * self.cell_size

    def update_to_tray_size(self):
        self.horizontal = True # Zawsze poziomo w zasobniku
        self.rect.width = self.length * (self.cell_size // 2)
        self.rect.height = self.cell_size // 2
