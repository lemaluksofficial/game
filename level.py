import pygame
from pygame import Rect, Surface

from entities import Coin, Enemy, Player, RisingHazard, Spike, Wall
from settings import (
    BG_COLOR,
    HAZARD_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
    FONT_NAME,
)


class Level:
    def __init__(self, map_path):
        self.map_path = map_path
        self.walls = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.spikes = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.player = None
        self.score = 0
        self.font = pygame.font.SysFont(FONT_NAME, 22)
        self.level_height = 0
        self.camera_offset = 0
        self.hazard = None

    def load(self):
        with open(self.map_path) as file:
            lines = [line.rstrip('\n') for line in file.readlines()]
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                pos = (x * TILE_SIZE, y * TILE_SIZE)
                if char == '#':
                    wall = Wall(pos)
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                elif char == '.':
                    coin = Coin(pos)
                    self.coins.add(coin)
                    self.all_sprites.add(coin)
                elif char == 'S':
                    spike = Spike(pos)
                    self.spikes.add(spike)
                    self.all_sprites.add(spike)
                elif char == 'E':
                    enemy = Enemy(pos, self.walls)
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
                elif char == 'P':
                    self.player = Player(pos, self.walls)
                    self.all_sprites.add(self.player)
        self.level_height = len(lines) * TILE_SIZE
        self.hazard = RisingHazard(self.level_height, HAZARD_SPEED)

    def update(self, dt):
        self.all_sprites.update()
        collected = pygame.sprite.spritecollide(self.player, self.coins, True)
        self.score += len(collected)

        if pygame.sprite.spritecollideany(self.player, self.spikes):
            self.player.alive = False
        if pygame.sprite.spritecollideany(self.player, self.enemies):
            self.player.alive = False

        self.hazard.update(dt)
        if self.player.rect.bottom >= self.hazard.y:
            self.player.alive = False

        # Scroll camera to follow player upwards
        self.camera_offset = max(0, int(self.player.rect.centery - (SCREEN_HEIGHT // 2)))

    def draw(self, surface):
        surface.fill(BG_COLOR)
        for sprite in self.all_sprites:
            rect = sprite.rect.move(0, -self.camera_offset)
            surface.blit(sprite.image, rect)
        self.hazard.draw(surface, self.camera_offset)
        self.draw_hud(surface)

    def draw_hud(self, surface):
        text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        height = self.font.render(f"Height: {max(0, self.level_height - self.player.rect.centery)}", True, (255, 255, 255))
        surface.blit(text, (10, 10))
        surface.blit(height, (10, 40))

    def restart(self):
        self.__init__(self.map_path)
        self.load()
