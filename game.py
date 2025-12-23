from __future__ import annotations
from typing import List
import pygame
import random
from core.settings import *
from world.tilemap import TileMap
from entities.objects import Player, Collectible, SpikeTrap, Exit, Dot, Star
from utils.utils import (load_game_data, save_game_data, load_image,
                         draw_text_with_shadow, draw_neon_button, load_sound)
from ui.shop import Shop


class Game:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.state = "menu"  # Main game state

        # --- Screen & Scaling ---
        # Virtual resolution for scaling the game world
        self.virt_w = int(WINDOW_WIDTH / GAME_SCALE)
        self.virt_h = int(WINDOW_HEIGHT / GAME_SCALE)
        self.game_surface = pygame.Surface((self.virt_w, self.virt_h))

        # --- Menu Settings ---
        self.menu_state = "main"
        self.menu_options = ["PLAY", "LEVELS", "SHOP", "QUIT"]
        self.selected_index = 0  # Selected item in the main menu

        # Navigation index for pause and game-over screens
        self.overlay_index = 0

        # Menu background particles
        self.bg_scroll_y = 0
        self.menu_particles = []
        for _ in range(30):
            self._spawn_menu_particle()

        # --- Save System ---
        # Load progress, coins, and inventory
        data = load_game_data()
        self.saved_level_index = data["level_index"]
        self._global_coins = data["coins"]
        self.bought_items = data["bought_items"]
        self.current_skin = data.get("current_skin", "travel_boy")
        self.level_stars = data.get("level_stars", {})

        self._lives = MAX_LIVES
        self.current_level_index = 0

        # Visual effects
        self.fade_alpha = 0
        self.fade_speed = 300
        self.screen_shake = 0

        # Load Fonts
        self.font_title = pygame.font.SysFont("arialblack", 60)
        self.font_menu = pygame.font.SysFont("arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20, bold=True)
        self.font_big = pygame.font.SysFont("arialblack", 40)

        # UI Images
        self.ui_coin_img = load_image("all_coins.png")
        self.ui_coin_img = pygame.transform.scale(self.ui_coin_img, (28, 28))

        star_raw = load_image("star.png")
        self.ui_star_full = pygame.transform.scale(star_raw, (28, 28))
        self.ui_star_empty = self.ui_star_full.copy()
        self.ui_star_empty.fill((80, 50, 100), special_flags=pygame.BLEND_RGBA_MULT)

        self.ui_star_menu_full = pygame.transform.scale(star_raw, (18, 18))
        self.ui_star_menu_empty = self.ui_star_menu_full.copy()
        self.ui_star_menu_empty.fill((60, 60, 80), special_flags=pygame.BLEND_RGBA_MULT)

        self.ui_pause_img = load_image("pause.png")
        self.ui_pause_img = pygame.transform.scale(self.ui_pause_img, (28, 28))
        self.pause_btn_rect = self.ui_pause_img.get_rect()

        # --- Sound Effects ---
        self.sfx_death = load_sound("death.wav")
        self.sfx_star = load_sound("Star_pick_up.wav")
        self.sfx_start = load_sound("Start.wav")
        self.sfx_win = load_sound("Win.wav")
        self.sfx_dot = load_sound("Dot.wav")
        self.sfx_coin = load_sound("Coin.wav")
        self.sfx_buy = load_sound("Buy.wav")
        self.sfx_jump = load_sound("Jump.wav")
        self.sfx_landing = load_sound("Landing.wav")

        # UI Sounds
        self.sfx_button = load_sound("Button.wav")  # For menu navigation
        self.sfx_click = load_sound("Bat_2.wav")    # For selection/clicks

        # Music & Loops
        self.sfx_menu_bg = load_sound("FromCore_StartScreen_water.wav")
        self.sfx_menu_bg.play(-1)

        self.music_gameplay = load_sound("Tomb_of_the_Mask_OST_-_Groovy_Traps_Gameplay_Extended.wav")
        self.music_gameplay.set_volume(0.5)

        # Initialize Shop and first level
        self.shop = Shop(self)
        self.scroll = [0, 0]
        self.setup_level(play_sound=False)

    # --- Properties & Methods ---

    def __repr__(self):
        """Debug info for the game object."""
        return f"<Game engine: state='{self.state}', level_index={self.current_level_index}, coins={self.global_coins}>"

    @property
    def global_coins(self):
        """Current player money."""
        return self._global_coins

    @global_coins.setter
    def global_coins(self, value):
        self._global_coins = value

    @property
    def lives(self):
        """Current player lives."""
        return self._lives

    @lives.setter
    def lives(self, value):
        self._lives = value

    def save_data(self) -> None:
        """Saves current progress and coins to a file."""
        data = {
            "level_index": self.saved_level_index,
            "coins": self.global_coins,
            "bought_items": self.bought_items,
            "current_skin": self.current_skin,
            "level_stars": self.level_stars
        }
        save_game_data(data)

    def update_level_stars_record(self):
        """Update the best star count for the current level if needed."""
        level_name = LEVELS[self.current_level_index]
        current_record = self.level_stars.get(level_name, 0)
        if self.stars_collected_count > current_record:
            self.level_stars[level_name] = self.stars_collected_count
            self.save_data()

    def _spawn_menu_particle(self):
        """Creates a random particle for the menu background."""
        x = random.randint(0, self.screen.get_width())
        y = random.randint(-50, self.screen.get_height())
        speed = random.uniform(100, 400)
        size = random.randint(4, 12)
        colors = [COLOR_NEON_YELLOW, COLOR_NEON_CYAN, (100, 50, 200)]
        color = random.choice(colors)
        self.menu_particles.append([x, y, speed, size, color])

    # ---------- LEVEL SETUP ----------
    def setup_level(self, play_sound=True):
        """
        Sets up the level: loads tiles, creates objects, and positions the camera.
        """
        level_name = LEVELS[self.current_level_index]
        self.tilemap = TileMap(level_name)
        spawn_x, spawn_y = self.tilemap.find_player_spawn()

        # Get the selected skin and create the player
        skin_data = next(filter(lambda s: s["key"] == self.current_skin, SKINS), SKINS[0])
        self.player = Player(self, self.tilemap, spawn_x, spawn_y, skin_filename=skin_data["file"])
        self.player.jump_sound = self.sfx_jump
        self.player.land_sound = self.sfx_landing

        # Clear objects from the previous level
        self.collectibles = []
        self.traps = []
        self.dots = []
        self.stars = []
        self.exit_portal = None
        self.stars_collected_count = 0

        # Fill the world with objects based on the level map
        for y, row in enumerate(self.tilemap.level_data):
            for x, ch in enumerate(row):
                if ch == "*":
                    self.collectibles.append(Collectible(x, y))
                elif ch == "T":
                    self.traps.append(SpikeTrap(x, y))
                elif ch == "E":
                    self.exit_portal = Exit(x, y)
                elif ch == "S":
                    self.stars.append(Star(x, y))
                if ch == ".": self.dots.append(Dot(x, y))

        # Fallback to ensure an exit exists
        if self.exit_portal is None: self.exit_portal = Exit(1, 1)

        # Set up drawing surface and camera dimensions
        self.virt_w = int(WINDOW_WIDTH / GAME_SCALE)
        self.virt_h = int(WINDOW_HEIGHT / GAME_SCALE)
        if not hasattr(self, 'game_surface') or self.game_surface.get_width() != self.virt_w:
            self.game_surface = pygame.Surface((self.virt_w, self.virt_h))

        # Calculate starting camera position to center on player
        target_x = self.player.rect.centerx - self.virt_w // 2
        target_y = self.player.rect.centery - self.virt_h // 2
        level_w = self.tilemap.width * TILE_SIZE
        level_h = self.tilemap.height * TILE_SIZE

        # Keep the camera within level boundaries
        if level_w > self.virt_w:
            target_x = max(0, min(target_x, level_w - self.virt_w))
        else:
            target_x = (level_w - self.virt_w) // 2

        ui_offset = UI_HEIGHT / GAME_SCALE
        if level_h > self.virt_h:
            target_y = max(0, min(target_y, level_h - self.virt_h + ui_offset))
        else:
            target_y = (level_h - self.virt_h) // 2

        self.scroll = [target_x, target_y]

        if play_sound:
            self.sfx_start.play()

    def restart_game(self):
        """
        Resets the game session and goes back to the main menu.
        """
        self.lives = MAX_LIVES
        self.current_level_index = 0
        self.setup_level(play_sound=False)
        self.music_gameplay.stop()
        self.state = "menu"
        self.sfx_menu_bg.play(-1)
        self.fade_alpha = 0

    def goto_next_level(self):
        """
        Moves progress to the next level and saves it.
        """
        if self.current_level_index < len(LEVELS) - 1:
            self.current_level_index += 1
            if self.current_level_index > self.saved_level_index:
                self.saved_level_index = self.current_level_index
            self.save_data()
            self.setup_level()
            self.music_gameplay.play(-1)
            self.state = "playing"
            self.fade_alpha = 255
        else:
            self.restart_game()

    def add_screen_shake(self, amount):
        """Triggers screen shake with a specific intensity."""
        self.screen_shake = max(self.screen_shake, amount)

    # ---------- UPDATE LOGIC ----------
    def update(self, dt: float, events: List[pygame.event.Event], fps: float) -> None:
        """Main update loop that branches based on game state."""
        self.current_fps = fps

        if self.state == "menu":
            self.update_menu(dt, events)
        elif self.state == "shop":
            self.shop.update(events)
        elif self.state == "playing":
            self.update_playing(dt, events)
        elif self.state == "pause":
            self.update_pause(events)
        elif self.state == "game_over":
            self.update_game_over(events)
        elif self.state == "level_complete":
            self.update_level_complete(events)

    def update_menu(self, dt, events):
        """Handles menu logic: particles, background scrolling, and buttons."""
        # Scroll background
        self.bg_scroll_y += 50 * dt
        if self.bg_scroll_y >= 100: self.bg_scroll_y = 0

        # Update menu particles
        for p in self.menu_particles:
            p[1] += p[2] * dt
            if p[1] > WINDOW_HEIGHT:
                self.menu_particles.remove(p)
                self._spawn_menu_particle()
                self.menu_particles[-1][1] = -20

        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        # Handle events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.sfx_button.play()
                    self.selected_index -= 1
                elif event.key == pygame.K_DOWN:
                    self.sfx_button.play()
                    self.selected_index += 1
                elif event.key == pygame.K_RETURN:
                    if self.menu_state == "main":
                        self.handle_main_menu_selection()
                    elif self.menu_state == "levels":
                        self.handle_level_menu_selection()
                elif event.key == pygame.K_ESCAPE:
                    if self.menu_state == "levels":
                        self.sfx_button.play()
                        self.menu_state = "main"
                        self.selected_index = 0

        # Wraparound for menu navigation
        max_len = len(self.menu_options) if self.menu_state == "main" else len(LEVELS) + 1
        self.selected_index %= max_len

        # Button collision logic
        if self.menu_state == "main":
            items = self.menu_options
        else:
            items = LEVELS + ["BACK"]

        btn_width = 280
        btn_height = 60
        start_y = 260
        gap = 75

        for i, item in enumerate(items):
            center_x = WINDOW_WIDTH // 2
            center_y = start_y + i * gap
            rect = pygame.Rect(0, 0, btn_width, btn_height)
            rect.center = (center_x, center_y)

            if rect.collidepoint(mouse_pos):
                if self.selected_index != i:
                    self.sfx_button.play()
                    self.selected_index = i

                if mouse_clicked:
                    if self.menu_state == "main":
                        self.handle_main_menu_selection()
                    elif self.menu_state == "levels":
                        self.handle_level_menu_selection()

    def handle_main_menu_selection(self):
        """Handle clicks and keyboard selection in the main menu."""
        choice = self.menu_options[self.selected_index]
        if choice == "PLAY":
            # Start game: stop menu music and load the current level
            self.sfx_menu_bg.stop()
            self.music_gameplay.play(-1)
            self.current_level_index = self.saved_level_index
            if self.current_level_index >= len(LEVELS): self.current_level_index = 0
            self.setup_level(play_sound=True)
            self.state = "playing"
            self.fade_alpha = 255
        elif choice == "LEVELS":
            self.sfx_click.play()
            self.menu_state = "levels"
            self.selected_index = 0
        elif choice == "SHOP":
            self.sfx_click.play()
            self.state = "shop"
        elif choice == "QUIT":
            self.sfx_click.play()
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_level_menu_selection(self):
        """Handle level selection in the levels menu."""
        if self.selected_index == len(LEVELS):  # Go back to main menu
            self.sfx_click.play()
            self.menu_state = "main"
            self.selected_index = 1
        else:
            # Start the selected level
            self.sfx_menu_bg.stop()
            self.music_gameplay.play(-1)
            self.current_level_index = self.selected_index
            self.setup_level(play_sound=True)
            self.state = "playing"
            self.fade_alpha = 255

    def update_playing(self, dt, events):
        """Update gameplay: movement, camera, and collisions."""
        # Update screen shake timer
        if self.screen_shake > 0:
            self.screen_shake -= 60 * dt
            if self.screen_shake < 0:
                self.screen_shake = 0

        # Player movement and logic
        self.player.handle_input(events)
        self.player.update(dt)

        # --- Camera Follow ---
        target_x = self.player.rect.centerx - self.virt_w // 2
        target_y = self.player.rect.centery - self.virt_h // 2

        # Smooth camera movement
        self.scroll[0] += (target_x - self.scroll[0]) * CAMERA_SMOOTHNESS * dt
        self.scroll[1] += (target_y - self.scroll[1]) * CAMERA_SMOOTHNESS * dt

        level_w = self.tilemap.width * TILE_SIZE
        level_h = self.tilemap.height * TILE_SIZE

        # Keep camera inside the level boundaries
        if level_w > self.virt_w:
            self.scroll[0] = max(0, min(self.scroll[0], level_w - self.virt_w))

        ui_offset = UI_HEIGHT / GAME_SCALE
        if level_h > self.virt_h:
            self.scroll[1] = max(0, min(self.scroll[1], level_h - self.virt_h + ui_offset))

        # Update world objects
        for trap in self.traps:
            trap.update(dt)

        self.handle_collectibles()
        self.handle_traps()
        self.handle_stars()

        # Check for dot collection
        player_rect = self.player.rect
        for dot in self.dots[:]:
            if dot.rect.colliderect(player_rect):
                self.sfx_dot.play()
                dot.collected = True
                self.dots.remove(dot)

        # Check if player died
        if (not self.player.alive) and self.player.death_timer <= 0:
            self.finish_player_death()

        # Check if player reached the exit
        if self.exit_portal and self.exit_portal.check_hit(self.player.rect):
            self.music_gameplay.stop()
            self.sfx_win.play()
            self.update_level_stars_record()
            self.state = "level_complete"

        # Handle pause input (P key or pause button)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.sfx_click.play()
                self.state = "pause"
                self.overlay_index = 0

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.pause_btn_rect.collidepoint(event.pos):
                    self.sfx_click.play()
                    self.state = "pause"
                    self.overlay_index = 0

        # Screen fade-in effect
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)

        pygame.display.set_caption(f"Tomb Prototype | FPS: {int(self.current_fps)}")

    def update_pause(self, events):
        """Handle navigation and clicks in the pause menu."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        options_count = 3  # Resume, Restart, Menu

        for event in events:
            if event.type == pygame.KEYDOWN:
                # Menu navigation
                if event.key == pygame.K_UP:
                    self.sfx_button.play()
                    self.overlay_index = (self.overlay_index - 1) % options_count
                elif event.key == pygame.K_DOWN:
                    self.sfx_button.play()
                    self.overlay_index = (self.overlay_index + 1) % options_count

                elif event.key == pygame.K_RETURN:
                    self.sfx_click.play()
                    self.handle_pause_action(self.overlay_index)

                # Hotkeys
                elif event.key == pygame.K_p:
                    self.state = "playing"
                elif event.key == pygame.K_r:
                    self.setup_level()
                    self.state = "playing"
                elif event.key == pygame.K_q:
                    self.restart_game()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

        # --- Pause Menu Buttons ---
        card_rect = pygame.Rect(0, 0, 400, 300)
        card_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        start_y = card_rect.top + 130
        gap = 50
        btn_width = 200
        btn_height = 40

        for i in range(options_count):
            center_x = WINDOW_WIDTH // 2
            center_y = start_y + i * gap
            rect = pygame.Rect(0, 0, btn_width, btn_height)
            rect.center = (center_x, center_y)

            # Hover and click logic
            if rect.collidepoint(mouse_pos):
                if self.overlay_index != i:
                    self.sfx_button.play()
                    self.overlay_index = i

                if mouse_clicked:
                    self.sfx_click.play()
                    self.handle_pause_action(i)

    def handle_pause_action(self, index):
        """Actions for pause menu options."""
        if index == 0:  # Resume
            self.state = "playing"
        elif index == 1:  # Restart
            self.setup_level()
            self.state = "playing"
        elif index == 2:  # Menu
            self.restart_game()

    def update_game_over(self, events):
        """Handles inputs and buttons for the game over screen."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        options_count = 2  # Retry, Return to Menu

        for event in events:
            if event.type == pygame.KEYDOWN:
                # Menu navigation
                if event.key == pygame.K_UP:
                    self.sfx_button.play()
                    self.overlay_index = (self.overlay_index - 1) % options_count
                elif event.key == pygame.K_DOWN:
                    self.sfx_button.play()
                    self.overlay_index = (self.overlay_index + 1) % options_count

                elif event.key == pygame.K_RETURN:
                    self.sfx_click.play()
                    self.handle_game_over_action(self.overlay_index)

                # Hotkeys
                elif event.key == pygame.K_r:
                    self.handle_game_over_action(0)
                elif event.key == pygame.K_q:
                    self.restart_game()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

        # --- Game Over Menu Buttons ---
        card_rect = pygame.Rect(0, 0, 400, 300)
        card_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        start_y = card_rect.top + 130
        gap = 60
        btn_width = 220
        btn_height = 45

        for i in range(options_count):
            center_x = WINDOW_WIDTH // 2
            center_y = start_y + i * gap
            rect = pygame.Rect(0, 0, btn_width, btn_height)
            rect.center = (center_x, center_y)

            # Mouse hover and click logic
            if rect.collidepoint(mouse_pos):
                if self.overlay_index != i:
                    self.sfx_button.play()
                    self.overlay_index = i

                if mouse_clicked:
                    self.sfx_click.play()
                    self.handle_game_over_action(i)

    def handle_game_over_action(self, index):
        """Actions for the game over screen."""
        if index == 0:  # Retry level
            self.lives = MAX_LIVES
            self.setup_level()
            self.state = "playing"
            self.fade_alpha = 255
        elif index == 1:  # Return to menu
            self.restart_game()

    def update_level_complete(self, events):
        """Handles logic when the level is finished."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n or event.key == pygame.K_RETURN:
                    self.goto_next_level()
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    self.restart_game()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

        if mouse_clicked:
            self.sfx_click.play()
            self.goto_next_level()

    def handle_collectibles(self):
        """Check for coin collection."""
        px, py = self.player.get_tile_pos()
        for c in self.collectibles:
            if not c.collected and c.tile_x == px and c.tile_y == py:
                self.sfx_coin.play()
                c.collect()
                self.player.score += 1
                self.global_coins += 1
                self.save_data()

    def handle_stars(self):
        """Check for star collection."""
        for star in self.stars:
            if not star.collected and star.rect.colliderect(self.player.rect):
                self.sfx_star.play()
                star.collected = True
                self.stars_collected_count += 1
                break

    def handle_traps(self):
        """Check if the player hit a trap."""
        if not self.player.alive: return
        for trap in self.traps:
            if trap.check_hit(self.player.rect):
                self.sfx_death.play()
                self.player.kill()
                return

    def finish_player_death(self):
        """Handle lives and transitions after player dies."""
        self.lives -= 1
        if self.lives <= 0:
            self.state = "game_over"
            self.overlay_index = 0  # Reset selection for game over screen
        else:
            self.player.reset_to_start()

    # ---------- DRAWING LOGIC ----------

    def draw(self) -> None:
        """Main draw function that calls other drawing methods based on state."""
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "shop":
            self.shop.draw()  # Call shop drawing module
        else:
            # Draw the gameplay world
            self.draw_game()

            # Draw menus on top of the game (overlays)
            if self.state == "pause":
                self.draw_overlay("PAUSED", ["RESUME", "RESTART", "MENU"], self.overlay_index)
            elif self.state == "game_over":
                self.draw_overlay("GAME OVER", ["TRY AGAIN", "MENU"], self.overlay_index, color_title=(255, 50, 50))
            elif self.state == "level_complete":
                self.draw_level_complete_overlay()

        # Draw the screen fade effect if the game is starting
        if self.state == "playing" and self.fade_alpha > 0:
            self.draw_fade()

    def draw_scrolling_bg(self):
        """Draws a scrolling grid background."""
        self.screen.fill(COLOR_BG)
        color_line = (40, 20, 60)
        gap = 100
        offset_y = int(self.bg_scroll_y) % gap

        # Draw grid lines
        for x in range(0, WINDOW_WIDTH, gap):
            pygame.draw.line(self.screen, color_line, (x, 0), (x, WINDOW_HEIGHT), 2)
        for y in range(offset_y - gap, WINDOW_HEIGHT + gap, gap):
            pygame.draw.line(self.screen, color_line, (0, y), (WINDOW_WIDTH, y), 2)

    def draw_menu(self):
        """Draws the main and levels menus."""
        self.draw_scrolling_bg()

        # Draw background particles
        for p in self.menu_particles:
            x, y, _, size, color = p
            pygame.draw.rect(self.screen, color, (x, y, size, size))

        # Titles
        title_text = "TOMB OF THE MASK"
        draw_text_with_shadow(self.screen, title_text, self.font_title,
                              (WINDOW_WIDTH // 2, 120), COLOR_NEON_YELLOW,
                              shadow_color=COLOR_NEON_CYAN, offset=(4, 4))

        sub_text = "PROTOTYPE"
        draw_text_with_shadow(self.screen, sub_text, self.font_menu,
                              (WINDOW_WIDTH // 2, 170), COLOR_WHITE)

        # Choose items based on menu state
        if self.menu_state == "main":
            items = self.menu_options
        else:
            items = LEVELS + ["BACK"]

        btn_width = 280
        btn_height = 60
        start_y = 260
        gap = 75

        for i, item in enumerate(items):
            center_x = WINDOW_WIDTH // 2
            center_y = start_y + i * gap
            rect = pygame.Rect(0, 0, btn_width, btn_height)
            rect.center = (center_x, center_y)

            is_selected = (i == self.selected_index)
            label = item.upper()

            # Draw buttons
            draw_neon_button(self.screen, rect, label, self.font_menu, is_selected)

            # Draw stars for levels in the levels menu
            if self.menu_state == "levels" and item in LEVELS:
                stars_count = self.level_stars.get(item, 0)
                star_start_x = rect.right + 20
                for s in range(3):
                    img = self.ui_star_menu_full if s < stars_count else self.ui_star_menu_empty
                    self.screen.blit(img, (star_start_x + s * 22, rect.centery - 9))

        # Help text at the bottom
        hint = "ARROWS to Select  |  ENTER to Confirm"
        draw_text_with_shadow(self.screen, hint, self.font_small,
                              (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30), (150, 150, 150))

    def draw_game(self):
        """
        Draws the game world to a virtual surface, handles screen shake,
        and then scales everything to fit the window.
        """
        self.game_surface.fill(COLOR_GAME_BG)

        # Calculate screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if self.screen_shake > 0:
            shake_offset_x = random.randint(-int(self.screen_shake), int(self.screen_shake))
            shake_offset_y = random.randint(-int(self.screen_shake), int(self.screen_shake))

        # Camera and UI setup
        scaled_ui_height = int(UI_HEIGHT / GAME_SCALE)
        render_scroll = (int(self.scroll[0] + shake_offset_x),
                         int(self.scroll[1] + shake_offset_y) - scaled_ui_height)

        # Draw all objects and the player
        self.tilemap.draw(self.game_surface, offset=render_scroll)
        for dot in self.dots: dot.draw(self.game_surface, offset=render_scroll)
        if self.exit_portal: self.exit_portal.draw(self.game_surface, offset=render_scroll)
        for s in self.stars: s.draw(self.game_surface, offset=render_scroll)
        for t in self.traps: t.draw(self.game_surface, offset=render_scroll)
        for c in self.collectibles: c.draw(self.game_surface, offset=render_scroll)
        self.player.draw(self.game_surface, offset=render_scroll)

        # Draw the scaled game world to the main screen
        scaled_surface = pygame.transform.scale(self.game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.screen.blit(scaled_surface, (0, 0))

        # Draw the HUD bar
        self.draw_hud()

    def draw_hud(self):
        """Draws the top bar with coins, stars, and the pause button."""
        # Top bar background
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, (0, 0, WINDOW_WIDTH, UI_HEIGHT))
        pygame.draw.line(self.screen, (50, 30, 70), (0, UI_HEIGHT), (WINDOW_WIDTH, UI_HEIGHT), 2)

        # Coin counter
        self.screen.blit(self.ui_coin_img, (20, 26))
        draw_text_with_shadow(self.screen, str(self.global_coins), self.font_menu,
                              (60, 26), COLOR_NEON_YELLOW, align="topleft")

        # Star progress
        star_x = WINDOW_WIDTH // 2 - 40
        for i in range(3):
            img = self.ui_star_full if i < self.stars_collected_count else self.ui_star_empty
            self.screen.blit(img, (star_x + i * 32, 26))

        # Pause button
        pause_x = WINDOW_WIDTH - 60
        self.pause_btn_rect.topleft = (pause_x, 26)
        self.screen.blit(self.ui_pause_img, self.pause_btn_rect)

    # --- MODAL OVERLAYS AND TRANSITIONS ---

    def draw_overlay(self, title, options, selected_idx, color_title=COLOR_NEON_YELLOW):
        """
        Draws a menu overlay on top of the game screen.
        Creates a dark transparent background and a centered menu box.
        """
        # Create and draw the dark background dimming
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 5, 20, 220))
        self.screen.blit(overlay, (0, 0))

        # Define the menu box (card) size and position
        card_rect = pygame.Rect(0, 0, 400, 300)
        card_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, card_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_NEON_CYAN, card_rect, 3, border_radius=20)

        # Draw the menu title
        draw_text_with_shadow(self.screen, title, self.font_big,
                              (WINDOW_WIDTH // 2, card_rect.top + 50), color_title)

        # Calculate button layout based on number of options
        start_y = card_rect.top + 130
        gap = 50 if len(options) > 2 else 60
        btn_width = 200 if len(options) > 2 else 220
        btn_height = 40 if len(options) > 2 else 45

        for i, opt in enumerate(options):
            center_x = WINDOW_WIDTH // 2
            center_y = start_y + i * gap
            rect = pygame.Rect(0, 0, btn_width, btn_height)
            rect.center = (center_x, center_y)

            is_selected = (i == selected_idx)
            # Draw each button
            draw_neon_button(self.screen, rect, opt, self.font_menu, is_selected)

    def draw_level_complete_overlay(self):
        """
        Draws the 'Level Complete' screen with star ratings.
        """
        # Create dark background
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 5, 20, 230))
        self.screen.blit(overlay, (0, 0))

        # Main card dimensions
        card_w, card_h = 500, 350
        card_rect = pygame.Rect((WINDOW_WIDTH - card_w) // 2, (WINDOW_HEIGHT - card_h) // 2, card_w, card_h)

        # Add a decorative glow behind the card
        glow_rect = card_rect.inflate(20, 20)
        pygame.draw.rect(self.screen, (0, 100, 100), glow_rect, border_radius=30)

        pygame.draw.rect(self.screen, COLOR_PANEL_BG, card_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_NEON_YELLOW, card_rect, 4, border_radius=20)

        draw_text_with_shadow(self.screen, "LEVEL COMPLETE", self.font_big,
                              (WINDOW_WIDTH // 2, card_rect.top + 50), COLOR_NEON_YELLOW)

        # Star icons settings
        star_size = 64
        start_x = WINDOW_WIDTH // 2 - (star_size * 1.5 + 10)
        star_y = card_rect.top + 120

        # Scale stars for the victory screen
        big_full = pygame.transform.scale(self.ui_star_full, (star_size, star_size))
        big_empty = pygame.transform.scale(self.ui_star_empty, (star_size, star_size))

        for i in range(3):
            # Pick full or empty star based on level score
            img = big_full if i < self.stars_collected_count else big_empty
            self.screen.blit(img, (start_x + i * (star_size + 10), star_y))

        # Navigation hint
        draw_text_with_shadow(self.screen, "PRESS ENTER TO CONTINUE", self.font_small,
                              (WINDOW_WIDTH // 2, card_rect.bottom - 40), (200, 200, 200))

    def draw_fade(self):
        """
        Draws a full-screen color fade effect for transitions.
        """
        fade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fade.fill(COLOR_BG)
        # Convert internal fade value to alpha (0-255)
        fade.set_alpha(int(self.fade_alpha))
        self.screen.blit(fade, (0, 0))