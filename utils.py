from __future__ import annotations
import pygame
import os
import json
from core.settings import TILE_SIZE, COLOR_NEON_YELLOW, COLOR_PANEL_BG, COLOR_SHADOW
from typing import Any, Dict, List, Tuple

# --- Folders & Paths ---
CURRENT_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(CURRENT_DIR)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LEVELS_DIR = os.path.join(ASSETS_DIR, "levels")
TILES_DIR = os.path.join(ASSETS_DIR, "tiles")
PLAYER_DIR = os.path.join(ASSETS_DIR, "player")
TRAPS_DIR = os.path.join(ASSETS_DIR, "traps")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

SAVE_FILE = "save_data.json"

# --- UI Helpers ---

def draw_text_with_shadow(
    surface: pygame.Surface,
    text: Any,
    font: pygame.font.Font,
    pos: Tuple[int, int],
    color: Tuple[int, int, int],
    /, *,
    shadow_color: Tuple[int, int, int] = COLOR_SHADOW,
    offset: Tuple[int, int] = (2, 2),
    align: str = "center"
) -> pygame.Rect:
    """Draws text with a simple shadow and alignment support."""

    def apply_formatting():
        """Auto-capitalize specific UI keywords and clean the string."""
        nonlocal text
        system_keywords = ["EQUIPPED", "OWNED", "SHOP", "PAUSED", "GAME OVER"]
        text_str = str(text)

        if any(key in text_str.upper() for key in system_keywords):
            text = text_str.upper()
        text = text.strip()

    apply_formatting()
    shadow_surf = font.render(text, True, shadow_color)
    text_surf = font.render(text, True, color)

    rect = text_surf.get_rect()
    if align == "center":
        rect.center = pos
    elif align == "topleft":
        rect.topleft = pos
    elif align == "midright":
        rect.midright = pos

    shadow_rect = rect.copy()
    shadow_rect.x += offset[0]
    shadow_rect.y += offset[1]

    surface.blit(shadow_surf, shadow_rect)
    surface.blit(text_surf, rect)
    return rect

def draw_neon_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    is_selected: bool,
    color_active: Tuple[int, int, int] = COLOR_NEON_YELLOW,
    color_inactive: Tuple[int, int, int] = (100, 80, 120)
) -> None:
    """Draws a styled button that changes color when selected."""
    # Button shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    pygame.draw.rect(surface, (20, 10, 30), shadow_rect, border_radius=15)

    # Pick colors based on selection state
    bg_color = color_active if is_selected else COLOR_PANEL_BG
    border_color = color_active if is_selected else color_inactive

    # Main button body
    pygame.draw.rect(surface, bg_color if is_selected else COLOR_PANEL_BG, rect, border_radius=15)
    pygame.draw.rect(surface, border_color, rect, 3, border_radius=15)

    text_color = (20, 10, 30) if is_selected else (200, 200, 200)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

# --- Asset Loading ---

def load_sound(filename):
    """Loads a sound file or returns a dummy object if not found to prevent crashes."""
    path = os.path.join(SOUNDS_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: Sound file not found: {filename}")

        class DummySound:
            def play(self, *args, **kwargs): pass
            def set_volume(self, v): pass
            def stop(self): pass

        return DummySound()
    return pygame.mixer.Sound(path)

def load_image(filename):
    """Loads an image; returns a magenta square if the file is missing."""
    path = os.path.join(TILES_DIR, filename)
    if not os.path.exists(path):
        path = filename
    if not os.path.exists(path):
        s = pygame.Surface((32, 32))
        s.fill((255, 0, 255))
        return s
    return pygame.image.load(path).convert_alpha()

def load_player_sprite(filename):
    path = os.path.join(PLAYER_DIR, filename)
    if not os.path.exists(path): return None
    return pygame.image.load(path).convert_alpha()

def load_trap_sprite(filename):
    """Loads a trap image and scales it to TILE_SIZE."""
    path = os.path.join(TRAPS_DIR, filename)
    if not os.path.exists(path): return None
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

def load_level(level_name: str = "level1") -> List[str]:
    """Reads level layout from a text file."""
    path = os.path.join(LEVELS_DIR, f"{level_name}.txt")
    if not os.path.exists(path): return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]

# --- Save & Load System ---

def load_game_data() -> Dict[str, Any]:
    """Loads progress from JSON or returns default values."""
    default_data = {
        "level_index": 0, "coins": 0, "bought_items": ["travel_boy"],
        "current_skin": "travel_boy", "level_stars": {}
    }
    if not os.path.exists(SAVE_FILE): return default_data
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            merged = default_data.copy()
            merged.update(data)
            return merged
    except:
        return default_data

def save_game_data(data):
    """Saves current game state to a JSON file."""
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)