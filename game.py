# game.py

import pygame
from settings import COLOR_BG, SHOW_GRID, TILE_SIZE, MAX_LIVES, LEVELS, UI_TEXT_COLOR, UI_HEIGHT

from tilemap import TileMap
from player import Player
from collectible import Collectible
from trap import SpikeTrap


class Game:
    def __init__(self, screen):
        self.screen = screen

        # состояния: menu / playing / pause / game_over / level_complete
        self.state = "menu"

        self.lives = MAX_LIVES
        self.current_level_index = 0  # индекс в списке LEVELS

        # fade
        self.fade_alpha = 0
        self.fade_speed = 300

        # шрифты
        self.font_big = pygame.font.SysFont("arial", 48, bold=True)
        self.font_small = pygame.font.SysFont("arial", 24)

        self.current_fps = 0

        # первый уровень
        self.setup_level()

    # ---------- создание / смена уровней ----------

    def setup_level(self):
        level_name = LEVELS[self.current_level_index]
        self.tilemap = TileMap(level_name)

        # ищем стартовую клетку игрока на карте
        spawn_x, spawn_y = self.tilemap.find_player_spawn()

        # создаём игрока в этой клетке
        self.player = Player(self.tilemap, spawn_x, spawn_y)

        self.collectibles = []
        self.traps = []

        for y, row in enumerate(self.tilemap.level_data):
            for x, ch in enumerate(row):
                if ch == "*":
                    self.collectibles.append(Collectible(x, y))
                if ch == "T":
                    self.traps.append(SpikeTrap(x, y, cycle_time=0.7))

    def restart_game(self):
        """Полный рестарт: возвращаемся в меню, первый уровень, жизни восстановлены."""
        self.lives = MAX_LIVES
        self.current_level_index = 0
        self.setup_level()
        self.state = "menu"
        self.fade_alpha = 0

    def goto_next_level(self):
        """Переход на следующий уровень (если есть)."""
        if self.current_level_index < len(LEVELS) - 1:
            self.current_level_index += 1
            self.setup_level()
            self.state = "playing"
            self.fade_alpha = 255
        else:
            # уровни закончились — возвращаемся в меню
            self.restart_game()

    # ---------- UPDATE ----------

    def update(self, dt, events, fps):
        self.current_fps = fps
        if self.state == "menu":
            self.update_menu(events)
        elif self.state == "playing":
            self.update_playing(dt, events)
        elif self.state == "pause":
            self.update_pause(events)
        elif self.state == "game_over":
            self.update_game_over(events)
        elif self.state == "level_complete":
            self.update_level_complete(events)

    def update_menu(self, events):
        """Главное меню + выбор уровня по цифрам."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Enter — начать с текущего выбранного уровня
                if event.key == pygame.K_RETURN:
                    self.state = "playing"
                    self.fade_alpha = 255

                # выбор уровня цифрами 1..N
                if pygame.K_1 <= event.key <= pygame.K_9:
                    num = event.key - pygame.K_1  # 0 для 1, 1 для 2, ...
                    if 0 <= num < len(LEVELS):
                        self.current_level_index = num
                        self.setup_level()
                        print("Selected level:", LEVELS[self.current_level_index])

    def update_playing(self, dt, events):
        self.player.handle_input(events)
        self.player.update(dt)

        for trap in self.traps:
            trap.update(dt)

        self.handle_collectibles()
        self.handle_traps()

        # смерть закончилась
        if (not self.player.alive) and self.player.death_timer <= 0:
            self.finish_player_death()

        # все монеты собраны → уровень пройден
        if self.all_coins_collected():
            self.state = "level_complete"

        # пауза
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.state = "pause"

        # fade-in
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)

        # заголовок
        level_name = LEVELS[self.current_level_index]
        pygame.display.set_caption(
            f"Tomb of the Mask — Prototype | Level: {level_name} | Coins: {self.player.score} | Lives: {self.lives}"
        )

    def update_pause(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.state = "playing"
                elif event.key == pygame.K_q:
                    self.restart_game()

    def update_game_over(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.restart_game()

    def update_level_complete(self, events):
        """Экран окончания уровня."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    self.goto_next_level()
                elif event.key == pygame.K_m:
                    self.restart_game()

    # ---------- столкновения ----------

    def all_coins_collected(self):
        return all(c.collected for c in self.collectibles)

    def handle_collectibles(self):
        px, py = self.player.get_tile_pos()
        for c in self.collectibles:
            if not c.collected and c.tile_x == px and c.tile_y == py:
                c.collect()
                self.player.score += 1

    def handle_traps(self):
        if not self.player.alive:
            return

        px, py = self.player.get_tile_pos()
        for trap in self.traps:
            if trap.check_hit(px, py):
                self.player.kill()
                break

    def finish_player_death(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = "game_over"
        else:
            self.player.reset_to_start()

    # ---------- DRAW ----------

    def draw(self):
        self.screen.fill(COLOR_BG)

        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game()

            if self.state == "pause":
                self.draw_pause_overlay()
            elif self.state == "game_over":
                self.draw_game_over_overlay()
            elif self.state == "level_complete":
                self.draw_level_complete_overlay()

        # fade только в игре
        if self.state == "playing" and self.fade_alpha > 0:
            self.draw_fade()

    def draw_game(self):
        offset_y = UI_HEIGHT

        self.tilemap.draw(self.screen, offset_y=offset_y)

        if SHOW_GRID:
            self.tilemap.draw_grid(self.screen, offset_y=offset_y)

        for trap in self.traps:
            trap.draw(self.screen, offset_y=offset_y)

        for c in self.collectibles:
            c.draw(self.screen, offset_y=offset_y)

        self.player.draw(self.screen, offset_y=offset_y)

        self.draw_hud()  # HUD всегда поверх

    # --- меню ---

    def draw_menu(self):
        title = self.font_big.render("TOMB OF THE MASK", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.screen.get_width() // 2, 150)))

        # подсказки по уровням
        for i, name in enumerate(LEVELS):
            text = self.font_small.render(f"{i+1} - {name}", True, (200, 200, 200))
            self.screen.blit(text, text.get_rect(center=(self.screen.get_width() // 2,
                                                         230 + i * 30)))

        start = self.font_small.render("ENTER - start", True, (255, 255, 255))
        self.screen.blit(start, start.get_rect(center=(self.screen.get_width() // 2, 320)))

    # --- пауза ---

    def draw_pause_overlay(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text1 = self.font_big.render("PAUSED", True, (255, 255, 255))
        text2 = self.font_small.render("P - resume", True, (255, 255, 255))
        text3 = self.font_small.render("Q - quit to menu", True, (255, 255, 255))

        self.screen.blit(text1, text1.get_rect(center=(400, 200)))
        self.screen.blit(text2, text2.get_rect(center=(400, 270)))
        self.screen.blit(text3, text3.get_rect(center=(400, 310)))

    # --- game over ---

    def draw_game_over_overlay(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        text1 = self.font_big.render("GAME OVER", True, (255, 255, 255))
        text2 = self.font_small.render("R - restart", True, (255, 255, 255))

        self.screen.blit(text1, text1.get_rect(center=(400, 220)))
        self.screen.blit(text2, text2.get_rect(center=(400, 280)))

    # --- окончание уровня ---

    def draw_level_complete_overlay(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        text1 = self.font_big.render("LEVEL COMPLETE!", True, (255, 255, 255))
        text2 = self.font_small.render("N - next level", True, (255, 255, 255))
        text3 = self.font_small.render("M - back to menu", True, (255, 255, 255))

        self.screen.blit(text1, text1.get_rect(center=(400, 210)))
        self.screen.blit(text2, text2.get_rect(center=(400, 270)))
        self.screen.blit(text3, text3.get_rect(center=(400, 310)))

    # --- HUD (coins / lives / fps) ---

    def draw_hud(self):
        # Панель слева сверху
        panel_width = 220
        panel_height = 70
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))  # полупрозрачный чёрный
        self.screen.blit(panel, (10, 10))

        # Текст монет
        text_coins = self.font_small.render(
            f"Coins: {self.player.score}", True, UI_TEXT_COLOR
        )
        self.screen.blit(text_coins, (20, 20))

        # Жизни квадратиками (как сердечки)
        life_size = 16
        for i in range(self.lives):
            x = 20 + i * (life_size + 4)
            y = 40
            pygame.draw.rect(
                self.screen,
                (220, 70, 70),
                (x, y, life_size, life_size),
                border_radius=4,
            )

        # FPS — в правом верхнем углу
        fps_int = int(self.current_fps)
        text_fps = self.font_small.render(f"FPS: {fps_int}", True, UI_TEXT_COLOR)
        rect_fps = text_fps.get_rect(topright=(self.screen.get_width() - 10, 10))
        self.screen.blit(text_fps, rect_fps)



    # --- fade ---

    def draw_fade(self):
        fade = pygame.Surface(self.screen.get_size())
        fade.fill((0, 0, 0))
        fade.set_alpha(int(self.fade_alpha))
        self.screen.blit(fade, (0, 0))
