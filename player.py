# player.py

import pygame
from settings import TILE_SIZE, PLAYER_SPEED
from tilemap import TileMap


class Player:
    def __init__(self, tilemap: TileMap, spawn_tile_x: int, spawn_tile_y: int):
        self.tilemap = tilemap

        # запоминаем стартовую клетку
        self.spawn_tile_x = spawn_tile_x
        self.spawn_tile_y = spawn_tile_y

        # стартовая позиция в пикселях
        self.x = spawn_tile_x * TILE_SIZE
        self.y = spawn_tile_y * TILE_SIZE


        self.size = TILE_SIZE // 2
        self.color = (255, 230, 0)

        self.speed = PLAYER_SPEED

        self.moving = False
        self.dir_x = 0
        self.dir_y = 0
        self.target_x = self.x
        self.target_y = self.y

        # счёт монет
        self.score = 0

        # состояние жизни
        self.alive = True
        self.death_timer = 0.0      # время до окончания "смерти"

    @property
    def rect(self):
        return pygame.Rect(
            self.x + TILE_SIZE // 2 - self.size // 2,
            self.y + TILE_SIZE // 2 - self.size // 2,
            self.size,
            self.size
        )

    def handle_input(self, events):
        if self.moving or not self.alive:
            return

        dx, dy = 0, 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            dx, dy = -1, 0
        elif keys[pygame.K_RIGHT]:
            dx, dy = 1, 0
        elif keys[pygame.K_UP]:
            dx, dy = 0, -1
        elif keys[pygame.K_DOWN]:
            dx, dy = 0, 1

        if dx == 0 and dy == 0:
            return

        self.start_move(dx, dy)

    def start_move(self, dx, dy):
        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)

        last_free_x = tile_x
        last_free_y = tile_y

        while True:
            next_x = last_free_x + dx
            next_y = last_free_y + dy

            if self.tilemap.is_solid(next_x, next_y):
                break

            last_free_x = next_x
            last_free_y = next_y

        if last_free_x == tile_x and last_free_y == tile_y:
            return

        self.target_x = last_free_x * TILE_SIZE
        self.target_y = last_free_y * TILE_SIZE
        self.dir_x = dx
        self.dir_y = dy
        self.moving = True

    def update(self, dt):
        # если умерли — просто ждём окончания таймера
        if not self.alive:
            if self.death_timer > 0:
                self.death_timer -= dt
            return

        if not self.moving:
            return

        vec_x = self.target_x - self.x
        vec_y = self.target_y - self.y

        distance_to_target = (vec_x ** 2 + vec_y ** 2) ** 0.5
        step = self.speed * dt

        if distance_to_target <= step:
            self.x = self.target_x
            self.y = self.target_y
            self.moving = False
        else:
            if distance_to_target != 0:
                self.x += (vec_x / distance_to_target) * step
                self.y += (vec_y / distance_to_target) * step

    def draw(self, surface, offset_y=0):
        # красный цвет, если умираем
        color = self.color if self.alive else (255, 80, 80)
        rect = self.rect.move(0, offset_y)
        pygame.draw.rect(surface, color, rect)

    def get_tile_pos(self):
        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)
        return tile_x, tile_y

    # ---- смерть / респаун ----

    def kill(self, death_duration=0.4):
        """Запускаем анимацию смерти."""
        self.alive = False
        self.death_timer = death_duration
        self.moving = False  # стопаем движение

    def reset_to_start(self):
        """Возврат в стартовую клетку и оживление."""
        self.x = self.spawn_tile_x * TILE_SIZE
        self.y = self.spawn_tile_y * TILE_SIZE
        self.target_x = self.x
        self.target_y = self.y
        self.moving = False
        self.alive = True
        self.death_timer = 0.0

