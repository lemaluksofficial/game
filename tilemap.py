from __future__ import annotations
import pygame
from core.settings import TILE_SIZE
from utils.utils import load_level, load_image, load_trap_sprite


class TileMap:
    """
    Handles level loading, tile rendering, and collision data.
    """
    def __init__(self, level_name: str = "level1") -> None:
        self.level_name = level_name
        self.level_data = load_level(level_name)

        if not self.level_data:
            self.width = 0
            self.height = 0
        else:
            self.width = max(len(row) for row in self.level_data)
            self.height = len(self.level_data)
            # Normalize row lengths to ensure a consistent rectangular grid
            for i in range(len(self.level_data)):
                if len(self.level_data[i]) < self.width:
                    self.level_data[i] += " " * (self.width - len(self.level_data[i]))

        self.tiles = {}
        # Categorize tile types for collision and rendering logic
        self.connectable_tiles = {"#", "T"}  # Tiles that trigger adjacency rendering
        self.solid_tiles = {"#"}             # Tiles with physical collision

        self.load_tiles()

        # Pre-render level surface to optimize draw calls
        self.full_map_surface = None
        self.render_entire_level()

    def __len__(self):
        """Returns the total number of rows (height) in the map."""
        return self.height

    def __getitem__(self, index):
        """Provides direct access to map rows via indexing."""
        if 0 <= index < self.height:
            return self.level_data[index]
        raise IndexError("Row index out of bounds")

    def __str__(self):
        return f"Level: {self.level_name} | Resolution: {self.width}x{self.height}"

    def load_tiles(self):
        """Loads and scales textures for all tile types."""
        wall_img = load_image("wall2.png")
        self.tiles["#"] = pygame.transform.scale(wall_img, (TILE_SIZE, TILE_SIZE))

        trap_img = load_trap_sprite("trap.png")
        if trap_img:
            self.tiles["T"] = pygame.transform.scale(trap_img, (TILE_SIZE, TILE_SIZE))
        else:
            # Fallback for missing trap assets
            self.tiles["T"] = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.tiles["T"].fill((255, 0, 0))

        floor_img = load_image("floor.png")
        self.tiles["."] = pygame.transform.scale(floor_img, (TILE_SIZE, TILE_SIZE))

        # Map interactive or decorative entities to the base floor texture
        for char in ["P", "*", "E", "S"]:
            self.tiles[char] = self.tiles["."]

    def get_tile(self, x: int, y: int) -> str:
        """Safe retrieval of tile character at specific coordinates."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.level_data[y][x]
        return " "

    def is_connectable(self, x, y):
        """Checks if a tile at the given coordinates should connect to neighbors."""
        tile = self.get_tile(x, y)
        return tile in self.connectable_tiles

    def render_entire_level(self):
        """
        Bakes the entire level into a single static surface.
        Calculates 'smart' connections for walls and traps to improve visual depth.
        """
        map_width_px = self.width * TILE_SIZE
        map_height_px = self.height * TILE_SIZE

        self.full_map_surface = pygame.Surface((map_width_px, map_height_px), pygame.SRCALPHA)

        THICKNESS = int(TILE_SIZE * 1)
        MARGIN = (TILE_SIZE - THICKNESS) // 2

        for y in range(self.height):
            for x in range(self.width):
                char = self.level_data[y][x]
                if char == " ": continue

                img = self.tiles.get(char, self.tiles["."])
                draw_x = x * TILE_SIZE
                draw_y = y * TILE_SIZE

                # Procedural adjacency rendering for structural tiles
                if char in ["#", "T"]:
                    up = self.is_connectable(x, y - 1)
                    down = self.is_connectable(x, y + 1)
                    left = self.is_connectable(x - 1, y)
                    right = self.is_connectable(x + 1, y)

                    # Draw core tile center
                    center_area = pygame.Rect(MARGIN, MARGIN, THICKNESS, THICKNESS)
                    self.full_map_surface.blit(img, (draw_x + MARGIN, draw_y + MARGIN), area=center_area)

                    # Render directional extensions based on neighbors
                    if up:
                        area_up = pygame.Rect(MARGIN, 0, THICKNESS, MARGIN)
                        self.full_map_surface.blit(img, (draw_x + MARGIN, draw_y), area=area_up)
                    if down:
                        area_down = pygame.Rect(MARGIN, MARGIN + THICKNESS, THICKNESS, MARGIN)
                        self.full_map_surface.blit(img, (draw_x + MARGIN, draw_y + MARGIN + THICKNESS), area=area_down)
                    if left:
                        area_left = pygame.Rect(0, MARGIN, MARGIN, THICKNESS)
                        self.full_map_surface.blit(img, (draw_x, draw_y + MARGIN), area=area_left)
                    if right:
                        area_right = pygame.Rect(MARGIN + THICKNESS, MARGIN, MARGIN, THICKNESS)
                        self.full_map_surface.blit(img, (draw_x + MARGIN + THICKNESS, draw_y + MARGIN), area=area_right)

                else:
                    # Standard blit for floor and non-connectable tiles
                    self.full_map_surface.blit(img, (draw_x, draw_y))

    def find_player_spawn(self):
        """Locates the 'P' character in level data to determine spawn point."""
        for y, row in enumerate(self.level_data):
            for x, ch in enumerate(row):
                if ch == "P":
                    return x, y
        else:
            print("Warning: No player spawn point 'P' found in level data!")
            return 1, 1

    def is_solid(self, x: int, y: int) -> bool:
        """Collision check based on grid coordinates."""
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        return self.get_tile(x, y) in self.solid_tiles

    def draw(self, surface, offset=(0, 0)):
        """
        Renders the pre-calculated map surface to the target display.
        Offset is applied for camera positioning.
        """
        ox, oy = offset
        surface.blit(self.full_map_surface, (-ox, -oy))