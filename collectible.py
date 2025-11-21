# collectible.py

import pygame
from settings import TILE_SIZE


class Collectible:
    def __init__(self, tile_x, tile_y, ctype="coin"):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.ctype = ctype

        # позиция в пикселях (верхний левый угол клетки)
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

        self.collected = False
        self.value = 1  # сколько монет даёт

        # размеры монетки (меньше клетки)
        self.radius = TILE_SIZE // 4
        self.color = (255, 215, 0)  # золотистый

    @property
    def center(self):
        return (
            self.x + TILE_SIZE // 2,
            self.y + TILE_SIZE // 2,
        )

    def collect(self):
        """Помечаем как собранную."""
        self.collected = True

    def draw(self, surface, offset_y=0):
        if self.collected:
            return

        cx, cy = self.center
        cy += offset_y
        pygame.draw.circle(surface, self.color, (cx, cy), self.radius)
