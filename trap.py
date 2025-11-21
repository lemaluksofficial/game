# trap.py

import pygame
from settings import TILE_SIZE


class Trap:
    """Базовый класс ловушки."""

    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

        self.active = True  # активна ли ловушка (наносит урон)

    def update(self, dt: float):
        """Обновление состояния (для анимаций / таймеров)."""
        pass

    def check_hit(self, player_tile_x, player_tile_y) -> bool:
        """True, если игрок в той же клетке и ловушка активна."""
        return self.active and \
            self.tile_x == player_tile_x and \
            self.tile_y == player_tile_y

    def draw(self, surface: pygame.Surface):
        """Рисуем ловушку — реализуется в наследниках."""
        pass


class SpikeTrap(Trap):
    """Шипы, которые периодически включаются/выключаются."""

    def __init__(self, tile_x, tile_y, cycle_time=1.0):
        super().__init__(tile_x, tile_y)
        self.cycle_time = cycle_time  # сколько секунд один шаг (вкл/выкл)
        self.timer = 0.0

    def update(self, dt: float):
        self.timer += dt
        if self.timer >= self.cycle_time:
            self.timer -= self.cycle_time
            self.active = not self.active  # переключаем состояние

    def draw(self, surface: pygame.Surface, offset_y=0):
        color_on = (200, 50, 50)
        color_off = (90, 90, 90)
        color = color_on if self.active else color_off

        padding = 4
        rect = pygame.Rect(
            self.x + padding,
            self.y + padding + offset_y,
            TILE_SIZE - padding * 2,
            TILE_SIZE - padding * 2,
        )
        pygame.draw.rect(surface, color, rect)

