from __future__ import annotations
from typing import Tuple, TYPE_CHECKING
import pygame
import math
import random
from core.settings import (TILE_SIZE, PLAYER_SPEED, COLOR_WALL_DUST)
from utils.utils import load_player_sprite, load_trap_sprite, load_image

if TYPE_CHECKING:
    from core.game import Game
    from world.tilemap import TileMap
import math
import pygame

# --- Animation Settings ---
# Default speed for blinking effects
COMMON_BLINK_SPEED = 0.01


class BlinkingMixin:
    """Helper for blinking animations and color fading."""

    def get_blink_value(self, speed=COMMON_BLINK_SPEED):
        """Returns a value between 0.0 and 1.0 based on a sine wave."""
        return (math.sin(pygame.time.get_ticks() * speed) + 1) / 2

    def get_blink_color(self, color_a, color_b, speed=COMMON_BLINK_SPEED):
        """Smoothly fades (lerps) between two colors."""
        t = self.get_blink_value(speed)
        return color_a.lerp(color_b, t)


class SoundEmitterMixin:
    """Helper for playing sounds with a cooldown to prevent overlapping."""

    def __init__(self):
        self._last_sound_time = 0

    def play_sound_effect(self, sound, cooldown=0.1):
        """Plays a sound only if the cooldown time has passed."""
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self._last_sound_time > cooldown:
            if sound:
                sound.play()
                self._last_sound_time = current_time

# --- PLAYER ENTITY ---
class Player:
    """
    Handles player movement, collisions, and animations.
    """

    def __init__(
            self,
            game: Game,
            tilemap: TileMap,
            spawn_tile_x: int,
            spawn_tile_y: int,
            skin_filename: str = "travel_boy.png"
    ) -> None:
        self.game = game
        self.tilemap = tilemap
        self.spawn_tile_x = spawn_tile_x
        self.spawn_tile_y = spawn_tile_y

        # Initial position on the grid
        self.x = spawn_tile_x * TILE_SIZE
        self.y = spawn_tile_y * TILE_SIZE

        self.size = TILE_SIZE
        self.visual_size = TILE_SIZE
        self.speed = PLAYER_SPEED

        # Load and scale player sprite
        self.image = load_player_sprite(skin_filename)
        if self.image:
            self.image = pygame.transform.scale(self.image, (self.visual_size, self.visual_size))
        else:
            self.image = None

        # Movement and direction
        self.moving = False
        self.dir_x = 0
        self.dir_y = 0
        self.target_x = self.x
        self.target_y = self.y

        # Rotation settings
        self.rotation_angle = 0
        self.target_rotation = 0

        # Sound effects
        self.land_sound = None
        self.jump_sound = None

        # Gameplay stats and timers
        self.score = 0
        self.alive = True
        self._death_timer = 0.0
        self._move_cooldown = 0.0  # Prevents moving too fast

        # VFX: Trails and particles
        self.prev_x = self.x
        self.prev_y = self.y
        self.trail_fade = 0.0
        self.trail_lifetime = 0.01
        self.MAX_TRAIL_LENGTH = TILE_SIZE * 1.5

        self.dust_particles = []
        self.skin_name = skin_filename

    @property
    def death_timer(self):
        """Time left in the death state."""
        return self._death_timer

    @property
    def move_cooldown(self):
        """Time until the player can move again."""
        return self._move_cooldown

    @property
    def rect(self):
        """Returns the collision box."""
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def __str__(self):
        status = "Moving" if self.moving else "Idle"
        return f"Player(Skin: {self.skin_name}, Pos: ({int(self.x)}, {int(self.y)}), State: {status})"

    def __repr__(self):
        return f"<Player object: x={self.x}, y={self.y}, alive={self.alive}>"

    def handle_input(self, events):
        """Checks for key presses and starts moving if possible."""
        if self.moving or not self.alive or self._move_cooldown > 0: return
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        # Pick movement direction
        if keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_RIGHT]:
            dx = 1
        elif keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_DOWN]:
            dy = 1

        if dx != 0 or dy != 0:
            self.start_move(dx, dy)

    import random

    def start_move(self, dx, dy):
        """Calculates the target position based on tile collisions."""
        # Update rotation based on move direction
        if dx > 0:
            self.rotation_angle = 90
            self.target_rotation = 90
        elif dx < 0:
            self.rotation_angle = -90
            self.target_rotation = -90
        elif dy < 0:
            self.rotation_angle = 180
            self.target_rotation = 180
        elif dy > 0:
            self.rotation_angle = 0
            self.target_rotation = 0

        # Look ahead to find the last free tile before a wall
        tile_x = int(self.x // TILE_SIZE)
        tile_y = int(self.y // TILE_SIZE)
        last_free_x, last_free_y = tile_x, tile_y

        while True:
            next_x = last_free_x + dx
            next_y = last_free_y + dy
            if self.tilemap.is_solid(next_x, next_y):
                break
            last_free_x, last_free_y = next_x, next_y

        # If the path is blocked immediately, play 'hit' effects
        if last_free_x == tile_x and last_free_y == tile_y:
            self.dir_x = dx
            self.dir_y = dy

            if self.land_sound:
                self.land_sound.play()

            # Visual feedback for hitting a wall
            self.spawn_landing_dust()
            self.game.add_screen_shake(1)
            self._move_cooldown = 0.2
            return

        # Start moving toward the destination
        if self.jump_sound:
            self.jump_sound.play()

        self.prev_x = self.x
        self.prev_y = self.y
        self.target_x = last_free_x * TILE_SIZE
        self.target_y = last_free_y * TILE_SIZE
        self.dir_x = dx
        self.dir_y = dy
        self.moving = True

    def spawn_landing_dust(self):
        """Spawns dust particles when hitting a wall."""
        count = random.randint(10, 15)

        for _ in range(count):
            spawn_x, spawn_y = self.x + self.size // 2, self.y + self.size // 2
            p_dx, p_dy = 0, 0
            speed_var = random.uniform(50, 100)
            spread = random.uniform(-80, 80)

            # Shoot particles in the opposite direction of the impact
            if self.dir_x > 0:
                spawn_x = self.rect.right
                p_dx = -speed_var
                p_dy = spread
            elif self.dir_x < 0:
                spawn_x = self.rect.left
                p_dx = speed_var
                p_dy = spread
            elif self.dir_y > 0:
                spawn_y = self.rect.bottom
                p_dy = -speed_var
                p_dx = spread
            elif self.dir_y < 0:
                spawn_y = self.rect.top
                p_dy = speed_var
                p_dx = spread

            self.dust_particles.append(DustParticle(spawn_x, spawn_y, p_dx, p_dy, COLOR_WALL_DUST))

    def update(self, dt: float) -> None:
        """Updates movement, timers, and particles."""
        if self._move_cooldown > 0:
            self._move_cooldown -= dt

        if not self.alive:
            if self._death_timer > 0: self._death_timer -= dt
            return

        # Handle trail transparency
        if self.moving:
            self.trail_fade = min(1.0, self.trail_fade + 5 * dt)
        elif self.trail_fade > 0:
            self.trail_fade = max(0.0, self.trail_fade - 3 * dt)

        # Update and clean up particles
        for p in self.dust_particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.dust_particles.remove(p)

        if not self.moving: return

        # Calculate distance and step for movement
        vec_x = self.target_x - self.x
        vec_y = self.target_y - self.y
        dist = (vec_x ** 2 + vec_y ** 2) ** 0.5
        step = self.speed * dt

        if dist <= step:
            # Snap to target and stop
            self.x = self.target_x
            self.y = self.target_y

            if self.moving:
                if self.land_sound:
                    self.land_sound.play()
                self.spawn_landing_dust()

            self.moving = False
            self.prev_x = self.x
            self.prev_y = self.y
        else:
            # Apply movement toward target
            self.x += (vec_x / dist) * step
            self.y += (vec_y / dist) * step

    def draw_trident(self, surface, ox, oy):
        """Draws the three-line trail effect when moving."""
        if self.trail_fade <= 0.01 or (self.x == self.prev_x and self.y == self.prev_y):
            return

        T_WIDTH_OUTER = 2
        T_WIDTH_CENTER = 4
        T_GAP = 3
        L_MULT_CENTER = 1.0
        L_MULT_OUTER = 0.85
        alpha = int(255 * self.trail_fade)
        trident_color = (255, 255, 0, alpha)

        px_current = self.x + self.size / 2
        py_current = self.y + self.size / 2
        actual_length = math.sqrt((self.prev_x - self.x) ** 2 + (self.prev_y - self.y) ** 2)
        base_length = min(actual_length, self.MAX_TRAIL_LENGTH)

        if base_length == 0: return

        # Draw horizontal trail
        if self.dir_x != 0:
            y_center = py_current
            segments = [
                {'w': T_WIDTH_CENTER, 'y_off': 0, 'len_mult': L_MULT_CENTER},
                {'w': T_WIDTH_OUTER, 'y_off': -(T_GAP + T_WIDTH_OUTER), 'len_mult': L_MULT_OUTER},
                {'w': T_WIDTH_OUTER, 'y_off': T_GAP + T_WIDTH_OUTER, 'len_mult': L_MULT_OUTER}
            ]
            for seg in segments:
                length = base_length * seg['len_mult']
                x_draw_start = min(px_current, px_current - (length * self.dir_x))
                s = pygame.Surface((length, seg['w']), pygame.SRCALPHA)
                s.fill(trident_color)
                surface.blit(s, (x_draw_start - ox, y_center - seg['w'] / 2 + seg['y_off'] - oy),
                             special_flags=pygame.BLEND_ADD)

        # Draw vertical trail
        elif self.dir_y != 0:
            x_center = px_current
            segments = [
                {'w': T_WIDTH_CENTER, 'x_off': 0, 'len_mult': L_MULT_CENTER},
                {'w': T_WIDTH_OUTER, 'x_off': -(T_GAP + T_WIDTH_OUTER), 'len_mult': L_MULT_OUTER},
                {'w': T_WIDTH_OUTER, 'x_off': T_GAP + T_WIDTH_OUTER, 'len_mult': L_MULT_OUTER}
            ]
            for seg in segments:
                length = base_length * seg['len_mult']
                y_draw_start = min(py_current, py_current - (length * self.dir_y))
                s = pygame.Surface((seg['w'], length), pygame.SRCALPHA)
                s.fill(trident_color)
                surface.blit(s, (x_center - seg['w'] / 2 + seg['x_off'] - ox, y_draw_start - oy),
                             special_flags=pygame.BLEND_ADD)

    def draw(self, surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
        """Draws everything: trails, particles, and the player sprite."""
        ox, oy = offset
        self.draw_trident(surface, ox, oy)
        for p in self.dust_particles:
            p.draw(surface, offset)

        draw_x = self.x - ox
        draw_y = self.y - oy
        center_x = draw_x + self.size // 2
        center_y = draw_y + self.size // 2

        if not self.alive:
            # Simple red box for death state
            pygame.draw.rect(surface, (255, 50, 50), (draw_x, draw_y, self.visual_size, self.visual_size))
        elif self.moving:
            # Squash and stretch effect while in motion
            long_axis = int(self.size * 0.18)
            short_axis = int(self.size * 0.11)
            stretch_x = long_axis if abs(self.dir_x) > 0 else short_axis
            stretch_y = long_axis if abs(self.dir_y) > 0 else short_axis

            rect_ellipse = pygame.Rect(0, 0, stretch_x * 2, stretch_y * 2)
            rect_ellipse.center = (center_x, center_y)

            # Draw outer glow
            glow_radius = max(stretch_x, stretch_y) + 4
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 0, 100), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (center_x - glow_radius, center_y - glow_radius), special_flags=pygame.BLEND_ADD)

            pygame.draw.ellipse(surface, (255, 255, 0), rect_ellipse)
            pygame.draw.ellipse(surface, (255, 255, 220), rect_ellipse.inflate(-4, -4))
        else:
            # Idle 'breathing' animation
            if self.image:
                anim_speed = 0.01
                current_time = pygame.time.get_ticks()
                squash = math.sin(current_time * anim_speed) * 0.05

                # Scale slightly to simulate breathing
                new_width = int(self.visual_size * (1.0 - squash))
                new_height = int(self.visual_size * (1.0 + squash))

                anim_img = pygame.transform.scale(self.image, (new_width, new_height))
                rotated_image = pygame.transform.rotate(anim_img, self.rotation_angle)
                rotated_rect = rotated_image.get_rect(center=(center_x, center_y))

                surface.blit(rotated_image, rotated_rect)
            else:
                pygame.draw.rect(surface, (255, 230, 0), (draw_x, draw_y, self.size, self.size))

    def get_tile_pos(self):
        """Returns current player position in grid coordinates."""
        return int((self.x + TILE_SIZE // 2) // TILE_SIZE), int((self.y + TILE_SIZE // 2) // TILE_SIZE)

    def kill(self, death_duration=0.0):
        """Kills the player and resets state."""
        self.alive = False
        self._death_timer = death_duration
        self.moving = False

    def reset_to_start(self):
        """Resets the player to their starting position and clears active effects."""
        # Move back to spawn coordinates
        self.x = self.spawn_tile_x * TILE_SIZE
        self.y = self.spawn_tile_y * TILE_SIZE
        self.target_x = self.x
        self.target_y = self.y

        # Reset movement and life state
        self.moving = False
        self.alive = True
        self._death_timer = 0.0

        # Reset visual state and particles
        self.prev_x = self.x
        self.prev_y = self.y
        self.rotation_angle = 0
        self.target_rotation = 0
        self.dust_particles = []


# --- COLLECTIBLE ENTITIES ---
class Dot(BlinkingMixin):
    """
    A small point for the player to collect.
    Uses BlinkingMixin for the color pulsing effect.
    """

    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        # Position based on the grid
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.collected = False

        # Colors for the pulse animation
        self.base_color = pygame.Color(255, 255, 0)
        self.pulse_color = pygame.Color("#C706D8")

        # Load and scale the dot image
        self.image = load_image("Dots.png")
        self.size = TILE_SIZE // 6
        self.original_image = pygame.transform.scale(self.image, (self.size, self.size))

    @property
    def rect(self) -> pygame.Rect:
        """Returns the collision hitbox, centered in the tile."""
        center_offset = (TILE_SIZE - self.size) // 2
        return pygame.Rect(self.x + center_offset, self.y + center_offset, self.size, self.size)

    def draw(self, surface, offset=(0, 0)):
        """Draws the dot with a pulsing color effect, adjusted for camera offset."""
        if self.collected: return
        ox, oy = offset

        # Get current pulse color from the mixin
        current_color = self.get_blink_color(self.base_color, self.pulse_color)

        # Apply the color to the image
        img_to_draw = self.original_image.copy()
        img_to_draw.fill(current_color, special_flags=pygame.BLEND_RGBA_MULT)

        center_offset = (TILE_SIZE - self.size) // 2
        surface.blit(img_to_draw, (self.x + center_offset - ox, self.y + center_offset - oy))


# --- COLLECTIBLE SYSTEM ---
class Collectible:
    """
    Base class for items like coins with spinning and color animations.
    """

    def __init__(self, tile_x, tile_y, ctype="coin"):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.ctype = ctype

        # Position on the grid
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.collected = False

        # Animation colors
        self.base_color = pygame.Color(255, 255, 0)
        self.pulse_color = pygame.Color("#C706D8")

        # Load and scale the asset
        self.image = load_image("coin.png")
        self.size = TILE_SIZE // 2
        self.original_image = pygame.transform.scale(self.image, (self.size, self.size))

    def __repr__(self):
        return f"<Collectible type={self.ctype} at ({self.tile_x}, {self.tile_y})>"

    def collect(self):
        """Marks the item as collected."""
        self.collected = True

    def draw(self, surface, offset=(0, 0)):
        """Draws the item with color fading and a horizontal spin effect."""
        if self.collected: return
        ox, oy = offset
        current_time = pygame.time.get_ticks()

        # Update color over time
        t_color = (math.sin(current_time * COMMON_BLINK_SPEED) + 1) / 2
        current_color = self.base_color.lerp(self.pulse_color, t_color)

        # Apply color tint
        img_colored = self.original_image.copy()
        img_colored.fill(current_color, special_flags=pygame.BLEND_RGBA_MULT)

        # --- Spinning Animation ---
        # Simulates rotation by scaling the width using a sine wave
        animation_speed = 0.005
        scale_x = abs(math.sin(current_time * animation_speed))
        new_width = max(1, int(self.size * scale_x))
        transformed_image = pygame.transform.scale(img_colored, (new_width, self.size))

        # Re-center the image after scaling
        center_offset_x = (TILE_SIZE - new_width) // 2
        center_offset_y = (TILE_SIZE - self.size) // 2
        draw_x = self.x + center_offset_x - ox
        draw_y = self.y + center_offset_y - oy

        surface.blit(transformed_image, (draw_x, draw_y))

# --- SPECIAL COLLECTIBLES ---
class Star:
    """
    A rare collectible that pulses with color.
    """

    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        # Position on the level grid
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.collected = False

        # --- Animation Settings ---
        self.base_color = pygame.Color(255, 255, 0)
        self.pulse_color = pygame.Color("#C706D8")

        # Load and scale asset
        self.image = load_image("star.png")
        self.size = int(TILE_SIZE * 0.7)
        self.original_image = pygame.transform.scale(self.image, (self.size, self.size))

    @property
    def rect(self):
        """Returns the hitbox, centered in the tile."""
        center_offset = (TILE_SIZE - self.size) // 2
        return pygame.Rect(self.x + center_offset, self.y + center_offset, self.size, self.size)

    def __repr__(self):
        """Debug representation of the Star."""
        return f"<Star at ({self.tile_x}, {self.tile_y}), collected={self.collected}>"

    def draw(self, surface, offset=(0, 0)):
        """Draws the star with a pulsing color effect."""
        if self.collected: return
        ox, oy = offset
        current_time = pygame.time.get_ticks()

        # Update color pulse over time
        t = (math.sin(current_time * COMMON_BLINK_SPEED) + 1) / 2
        current_color = self.base_color.lerp(self.pulse_color, t)

        # Tint the image with the current pulse color
        img_to_draw = self.original_image.copy()
        img_to_draw.fill(current_color, special_flags=pygame.BLEND_RGBA_MULT)

        # Center and draw on screen
        center_offset = (TILE_SIZE - self.size) // 2
        draw_x = self.x + center_offset - ox
        draw_y = self.y + center_offset - oy
        surface.blit(img_to_draw, (draw_x, draw_y))


# --- HAZARD ENTITIES ---
class Trap:
    """
    Base class for traps and other hazards.
    """

    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

        # Position on the grid
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.active = True

        # Use a slightly smaller hitbox for fairer gameplay
        padding = 6
        self.rect = pygame.Rect(self.x + padding, self.y + padding,
                                TILE_SIZE - padding * 2, TILE_SIZE - padding * 2)

    def update(self, dt):
        """Placeholder for custom trap logic."""
        pass

    def check_hit(self, player_rect):
        """Checks if the player touched the trap."""
        if not self.active: return False
        return self.rect.colliderect(player_rect)

    def draw(self, surface, offset=(0, 0)):
        """Placeholder for drawing logic."""
        pass


# --- SPIKE HAZARD ---
class SpikeTrap(Trap, BlinkingMixin):
    """
    Spike trap that blinks between colors.
    """

    def __init__(self, tile_x, tile_y):
        # Setup basic trap settings
        super().__init__(tile_x, tile_y)

        # Adjust hitbox size (35% of tile size) and center it
        SCALE_PCT = 0.35
        trap_size = int(TILE_SIZE * SCALE_PCT)
        padding = (TILE_SIZE - trap_size) // 2
        self.rect = pygame.Rect(self.x + padding, self.y + padding,
                                TILE_SIZE - padding * 2, TILE_SIZE - padding * 2)

        # Colors for the blinking effect
        self.color_normal = pygame.Color(200, 0, 0)
        self.color_active = pygame.Color(255, 100, 0)

    def draw(self, surface, offset=(0, 0)):
        """Draws the spike with a pulsing color effect."""
        ox, oy = offset

        # Get current color from the BlinkingMixin
        color = self.get_blink_color(self.color_normal, self.color_active, speed=0.02)
        pygame.draw.rect(surface, color, (self.rect.x - ox, self.rect.y - oy, self.rect.width, self.rect.height))


# --- PARTICLE EFFECTS ---
class DustParticle:
    """
    A simple dust particle that moves and fades away.
    """

    def __init__(self, x, y, dx, dy, color):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy

        # Randomize size for a more natural look
        self.size = random.randint(3, 5)

        self.color = color
        self.life = 1.0

        # How fast the particle disappears
        self.decay = random.uniform(3.0, 5.0)

    def update(self, dt):
        """Update position and reduce life."""
        self.x += self.dx * dt
        self.y += self.dy * dt
        self.life -= self.decay * dt

    def draw(self, surface, offset=(0, 0)):
        """Draw the particle on screen."""
        if self.life <= 0: return
        ox, oy = offset
        rect = pygame.Rect(self.x - ox, self.y - oy, int(self.size), int(self.size))
        pygame.draw.rect(surface, self.color, rect)


# --- OBJECTIVES ---
class Exit:
    """
    Handles logic and drawing for the level exit.
    """

    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

        # Centered hitbox for the exit
        padding = 4
        self.rect = pygame.Rect(self.x + padding, self.y + padding,
                                TILE_SIZE - padding * 2, TILE_SIZE - padding * 2)

        # Load and scale the exit sprite
        self.image = load_image("exit.png")
        self.base_size = TILE_SIZE
        self.original_image = pygame.transform.scale(self.image, (self.base_size, self.base_size))

        # Colors for the pulse animation
        self.color_normal = pygame.Color(255, 255, 0)
        self.color_glow = pygame.Color("#C706D8")

    def check_hit(self, player_rect):
        """Check if the player has touched the exit."""
        return self.rect.colliderect(player_rect)

    def draw(self, surface, offset=(0, 0)):
        """
        Draw the exit with pulsing color and scale effects.
        """
        ox, oy = offset
        current_time = pygame.time.get_ticks()
        sin_wave = math.sin(current_time * COMMON_BLINK_SPEED)
        t_color = (sin_wave + 1) / 2

        # Calculate pulsing color
        current_color = self.color_normal.lerp(self.color_glow, t_color)

        img_to_draw = self.original_image.copy()
        img_to_draw.fill(current_color, special_flags=pygame.BLEND_RGBA_MULT)

        # Apply pulsing scale (breathing effect)
        scale_factor = 1.0 + (sin_wave * 0.1)
        new_size = int(self.base_size * scale_factor)
        final_img = pygame.transform.scale(img_to_draw, (new_size, new_size))

        # Center the scaled image and draw it
        center_offset = (self.base_size - new_size) // 2
        draw_x = self.x + center_offset - ox
        draw_y = self.y + center_offset - oy
        surface.blit(final_img, (draw_x, draw_y))