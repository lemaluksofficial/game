import math
import array
import pygame
from pygame import Rect, Surface

from settings import (
    TILE_SIZE,
    PLAYER_SPEED,
    WALL_COLOR,
    PLAYER_COLOR,
    COIN_COLOR,
    SPIKE_COLOR,
    ENEMY_COLOR,
    HAZARD_COLOR,
    ENEMY_SPEED,
)


class Wall(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(WALL_COLOR)
        self.rect = self.image.get_rect(topleft=pos)


class Coin(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = Surface((TILE_SIZE // 2, TILE_SIZE // 2))
        self.image.fill(COIN_COLOR)
        self.rect = self.image.get_rect(center=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))


class Spike(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((0, 0, 0))
        pygame.draw.polygon(
            self.image,
            SPIKE_COLOR,
            [
                (0, TILE_SIZE),
                (TILE_SIZE // 2, TILE_SIZE // 3),
                (TILE_SIZE, TILE_SIZE),
            ],
        )
        self.rect = self.image.get_rect(topleft=pos)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, walls):
        super().__init__()
        self.image = Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect(topleft=pos)
        self.velocity = pygame.Vector2()
        self.walls = walls
        self.alive = True

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.velocity.xy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity.y = -PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity.y = PLAYER_SPEED

    def move(self):
        self.rect.x += self.velocity.x
        self._collide('x')
        self.rect.y += self.velocity.y
        self._collide('y')

    def _collide(self, direction):
        for wall in self.walls:
            if self.rect.colliderect(wall.rect):
                if direction == 'x':
                    if self.velocity.x > 0:
                        self.rect.right = wall.rect.left
                    elif self.velocity.x < 0:
                        self.rect.left = wall.rect.right
                else:
                    if self.velocity.y > 0:
                        self.rect.bottom = wall.rect.top
                    elif self.velocity.y < 0:
                        self.rect.top = wall.rect.bottom

    def update(self):
        if not self.alive:
            return
        self.handle_input()
        self.move()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls):
        super().__init__()
        self.image = Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(ENEMY_COLOR)
        self.rect = self.image.get_rect(topleft=pos)
        self.direction = 1
        self.walls = walls

    def update(self):
        self.rect.x += self.direction * ENEMY_SPEED
        for wall in self.walls:
            if self.rect.colliderect(wall.rect):
                if self.direction > 0:
                    self.rect.right = wall.rect.left
                else:
                    self.rect.left = wall.rect.right
                self.direction *= -1
                break


class RisingHazard:
    def __init__(self, level_height, speed):
        self.y = level_height
        self.speed = speed

    def update(self, dt_ms):
        seconds = dt_ms / 1000.0
        self.y -= self.speed * seconds

    def rect(self):
        return Rect(0, int(self.y), TILE_SIZE * 100, TILE_SIZE * 2)

    def draw(self, surface, camera_offset):
        hazard_rect = Rect(0, int(self.y) - camera_offset, surface.get_width(), TILE_SIZE * 2)
        pygame.draw.rect(surface, HAZARD_COLOR, hazard_rect)


def generate_tone(frequency=440, duration_ms=200, volume=0.25):
    sample_rate = 44100
    samples = int(sample_rate * (duration_ms / 1000.0))
    amplitude = int(32767 * volume)
    buffer = array.array("h")
    for i in range(samples):
        sample = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
        buffer.append(sample)
    return pygame.mixer.Sound(buffer=buffer)
