# --- Window Settings ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Size of a single grid cell
TILE_SIZE = 32

# --- Camera & Scaling ---
# Global scale for rendering assets
GAME_SCALE = 0.62

# --- UI Theme Colors ---
COLOR_BG = (20, 10, 35)
COLOR_PANEL_BG = (45, 25, 60)
COLOR_NEON_YELLOW = (255, 220, 0)
COLOR_NEON_CYAN = (0, 240, 255)
COLOR_NEON_MAGENTA = (255, 0, 150)
COLOR_WHITE = (255, 255, 255)
COLOR_SHADOW = (10, 5, 20)
COLOR_WALL_DUST = (180, 0, 220)

# --- Gameplay Settings ---
COLOR_GAME_BG = (0, 0, 0) # Background color during gameplay

SHOW_GRID = False # Toggle grid visibility for debugging
MAX_LIVES = 1     # Starting lives for the player

# --- Levels & Physics ---
LEVELS = ["level1", "level2", "level3"]
UI_TEXT_COLOR = COLOR_WHITE
UI_HEIGHT = 80        # Height of the top HUD bar
PLAYER_SPEED = 1100   # Horizontal movement speed

# Camera follow speed (higher is smoother/faster)
CAMERA_SMOOTHNESS = 20

# --- Player Skins ---
# List of available characters and their shop properties
SKINS = [
    {"key": "travel_boy", "file": "travel_boy.png", "name": "Travel Boy", "price": 0, "desc": "Ready for adventure!"},
    {"key": "agent",      "file": "agent.png",      "name": "Agent",      "price": 5, "desc": "Secret service style."},
    {"key": "cyclop",     "file": "cyclop.png",     "name": "Cyclop",     "price": 10, "desc": "Eye see you."},
]

# --- Level Configurations ---
# Specific overrides or settings for individual levels
LEVEL_CONFIG = {
    "level1": {},
    "level2": {},
    "level3": {},
}