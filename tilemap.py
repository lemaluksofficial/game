# tilemap.py

import os
import pygame
from settings import TILE_SIZE
from level_loader import load_level
from utils import load_image

BASE_DIR = os.path.dirname(__file__)
TILES_DIR = os.path.join(BASE_DIR, "assets", "tiles")


class TileMap:
    def __init__(self, level_name="level1"):
        self.level_name = level_name
        self.level_data = load_level(level_name)
        self.width = len(self.level_data[0])
        self.height = len(self.level_data)

        self.tiles = {}
        self.load_tiles()

    def create_big_stone_block(self):
        """Генерирует стену в виде одного цельного каменного блока."""
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))

        # 1. Цвет шва (темный фон, чтобы блоки визуально разделялись)
        gap_color = (20, 15, 10)
        surface.fill(gap_color)

        # Цвета камня (теплый серый/коричневый оттенок)
        base_color = (120, 110, 100)  # Основной цвет
        highlight = (160, 150, 140)  # Свет (верх/лево)
        shadow = (80, 70, 60)  # Тень (низ/право)

        # Отступ от края (margin), чтобы блок был чуть меньше клетки
        m = 1
        block_size = TILE_SIZE - m * 2

        # 2. Рисуем тень (сдвинута вниз-вправо, создает эффект толщины)
        pygame.draw.rect(surface, shadow, (m, m, block_size, block_size))

        # 3. Рисуем основной массив камня (чуть сдвигаем, чтобы тень осталась видна снизу/справа)
        # Уменьшаем высоту и ширину на толщину фаски (например, 3 пикселя)
        bevel = 3
        pygame.draw.rect(surface, base_color,
                         (m, m, block_size - bevel, block_size - bevel))

        # 4. Рисуем светлый блик (сверху и слева)
        # Верхняя полоска
        pygame.draw.rect(surface, highlight, (m, m, block_size - bevel, bevel))
        # Левая полоска
        pygame.draw.rect(surface, highlight, (m, m, bevel, block_size - bevel))

        # 5. (Опционально) Трещинка или деталь в центре, чтобы не было скучно
        center = TILE_SIZE // 2
        pygame.draw.rect(surface, (100, 90, 80), (center - 2, center - 2, 4, 4))

        return surface

    def load_tiles(self):
        """Загружаем тайлы или генерируем их."""

        # Вместо загрузки картинки стены, создаем её сами
        self.tiles["#"] = self.create_big_stone_block()

        floor_path = os.path.join(TILES_DIR, "floor.png")

        # Пол оставляем как есть, либо рисуем простой фон
        if os.path.exists(floor_path):
            floor_img = load_image(floor_path)
            floor_img = pygame.transform.scale(floor_img, (TILE_SIZE, TILE_SIZE))
        else:
            floor_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
            floor_img.fill((0, 0, 0))  # Пол просто черный

        self.tiles["."] = floor_img
        self.tiles["P"] = floor_img
        self.tiles["T"] = floor_img
        self.tiles["*"] = floor_img
        self.tiles["E"] = floor_img

    def find_player_spawn(self):
        """Ищем символ 'P' в карте."""
        for y, row in enumerate(self.level_data):
            for x, ch in enumerate(row):
                if ch == "P":
                    return x, y
        return 1, 1

    def get_tile(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.level_data[y][x]
        return "#"

    def is_solid(self, x, y):
        tile = self.get_tile(x, y)
        return tile == "#"

    def draw(self, surface, offset_y=0):
        """Рисуем уровень."""
        for y, row in enumerate(self.level_data):
            for x, char in enumerate(row):
                img = None

                if char == "#":
                    img = self.tiles["#"]
                elif char == ".":
                    img = self.tiles["."]
                # Под объектами (ловушки, игрок, монеты) тоже рисуем пол
                elif char in ("T", "*", "E", "P"):
                    img = self.tiles["."]

                if img:
                    surface.blit(img, (x * TILE_SIZE, y * TILE_SIZE + offset_y))

    def draw_grid(self, surface, color=(50, 50, 50), offset_y=0):
        """Отладочная сетка."""
        width_px = self.width * TILE_SIZE
        height_px = self.height * TILE_SIZE

        for x in range(self.width + 1):
            px = x * TILE_SIZE
            pygame.draw.line(surface, color, (px, offset_y), (px, offset_y + height_px))

        for y in range(self.height + 1):
            py = y * TILE_SIZE + offset_y
            pygame.draw.line(surface, color, (0, py), (width_px, py))