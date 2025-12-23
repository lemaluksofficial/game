import pygame
from core.settings import *
from utils.utils import load_player_sprite, draw_text_with_shadow, draw_neon_button


class Shop:
    """
    Handles the skin shop: buying items, equipping skins, and drawing the UI.
    """

    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font_big = game.font_big
        self.font_small = game.font_small

        # Sort skins by price (cheapest first)
        self.items = sorted(SKINS, key=lambda item: item["price"])
        self.selected_index = 0

        # --- Load Preview Images ---
        # Pre-load and scale images now to keep the shop scrolling smooth
        self.preview_images = {}
        preview_size = (128, 128)
        for item in self.items:
            img = load_player_sprite(item["file"])
            if img:
                img = pygame.transform.scale(img, preview_size)
                self.preview_images[item["key"]] = img
            else:
                # Fallback to magenta square if image is missing
                s = pygame.Surface(preview_size)
                s.fill((255, 0, 255))
                self.preview_images[item["key"]] = s

    def update(self, events):
        """
        Handle mouse clicks and keyboard navigation.
        """
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.sfx_click.play()
                    self.game.state = "menu"
                    self.game.menu_state = "main"

                elif event.key == pygame.K_LEFT:
                    self.game.sfx_button.play()
                    self.selected_index = (self.selected_index - 1) % len(self.items)

                elif event.key == pygame.K_RIGHT:
                    self.game.sfx_button.play()
                    self.selected_index = (self.selected_index + 1) % len(self.items)

                elif event.key == pygame.K_RETURN:
                    self.action_item()

        # --- Back Button ---
        back_btn_rect = pygame.Rect(20, 20, 120, 50)
        if back_btn_rect.collidepoint(mouse_pos) and mouse_clicked:
            self.game.sfx_click.play()
            self.game.state = "menu"
            self.game.menu_state = "main"

        # --- Item Selection ---
        card_w, card_h = 220, 320
        gap = 40

        # Center the cards horizontally
        total_w = len(self.items) * card_w + (len(self.items) - 1) * gap
        start_x = (WINDOW_WIDTH - total_w) // 2
        center_y = WINDOW_HEIGHT // 2 + 20

        for i, item in enumerate(self.items):
            x = start_x + i * (card_w + gap)
            y = center_y - card_h // 2
            rect = pygame.Rect(x, y, card_w, card_h)

            if rect.collidepoint(mouse_pos):
                # Hover to select
                if self.selected_index != i:
                    self.game.sfx_button.play()
                    self.selected_index = i

                if mouse_clicked:
                    self.action_item()

    def action_item(self):
        """
        Buy the skin or equip it if already owned.
        """
        item = self.items[self.selected_index]
        key = item["key"]
        price = item["price"]

        if key in self.game.bought_items:
            # Already owned: just equip
            self.game.current_skin = key
            self.game.save_data()
            self.game.sfx_click.play()
        else:
            # Not owned: check coins and buy
            if self.game.global_coins >= price:
                self.game.global_coins -= price
                self.game.bought_items.append(key)
                self.game.current_skin = key
                self.game.save_data()
                self.game.sfx_buy.play()
            else:
                # Not enough money
                self.game.sfx_click.play()

    def draw(self):
        """
        Draw the shop UI: header, coins, back button, and skin cards.
        """
        self.game.draw_scrolling_bg()

        # Title and Coins
        draw_text_with_shadow(self.screen, "SHOP", self.font_big, (WINDOW_WIDTH // 2, 50), COLOR_NEON_CYAN)

        coins_text = f"Coins: {self.game.global_coins}"
        draw_text_with_shadow(self.screen, coins_text, self.font_small,
                              (WINDOW_WIDTH - 100, 50), COLOR_NEON_YELLOW)

        # Back button
        mouse_pos = pygame.mouse.get_pos()
        back_btn_rect = pygame.Rect(20, 20, 120, 50)
        is_hovered = back_btn_rect.collidepoint(mouse_pos)
        draw_neon_button(self.screen, back_btn_rect, "BACK", self.font_small, is_hovered,
                         color_active=COLOR_NEON_MAGENTA)

        # Shop cards
        card_w, card_h = 220, 320
        gap = 40
        total_w = len(self.items) * card_w + (len(self.items) - 1) * gap
        start_x = (WINDOW_WIDTH - total_w) // 2
        center_y = WINDOW_HEIGHT // 2 + 20

        for i, item in enumerate(self.items):
            x = start_x + i * (card_w + gap)
            y = center_y - card_h // 2
            rect = pygame.Rect(x, y, card_w, card_h)

            is_selected = (i == self.selected_index)
            is_owned = item["key"] in self.game.bought_items
            is_equipped = (item["key"] == self.game.current_skin)

            # Card background and border
            bg_color = (60, 40, 80) if is_selected else (30, 20, 40)
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=20)

            border_c = COLOR_NEON_YELLOW if is_selected else (60, 50, 80)
            pygame.draw.rect(self.screen, border_c, rect, 4 if is_selected else 2, border_radius=20)

            # Skin preview image
            img = self.preview_images.get(item["key"])
            img_rect = img.get_rect(center=(rect.centerx, rect.top + 100))
            self.screen.blit(img, img_rect)

            # Skin name
            draw_text_with_shadow(self.screen, item["name"], self.font_small,
                                  (rect.centerx, rect.top + 180), COLOR_WHITE)

            # Set status text (Equipped / Owned / Price)
            if is_equipped:
                status = "EQUIPPED"
                color = COLOR_NEON_CYAN
            elif is_owned:
                status = "OWNED"
                color = (100, 255, 100)
            else:
                status = f"${item['price']}"
                color = COLOR_NEON_YELLOW if self.game.global_coins >= item["price"] else (255, 80, 80)

            # Draw status label
            status_rect = pygame.Rect(rect.left + 20, rect.bottom - 60, rect.width - 40, 40)
            pygame.draw.rect(self.screen, (20, 10, 30), status_rect, border_radius=10)
            draw_text_with_shadow(self.screen, status, self.font_small, status_rect.center, color)

        # Skin description at the bottom
        sel_item = self.items[self.selected_index]
        desc = sel_item["desc"]
        draw_text_with_shadow(self.screen, desc, self.font_small,
                              (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 60), (200, 200, 255))