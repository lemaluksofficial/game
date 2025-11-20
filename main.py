import pygame

from entities import generate_tone
from level import Level
from settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_COLOR

MENU, PLAYING, PAUSED, GAME_OVER = "menu", "playing", "paused", "game_over"


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.coin_sound = generate_tone(880, 120)
            self.death_sound = generate_tone(120, 200)
        except pygame.error:
            self.coin_sound = None
            self.death_sound = None

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tomb of the Mask - Pygame Edition")
        self.clock = pygame.time.Clock()
        self.state = MENU
        self.level = Level("data/level1.txt")
        self.level.load()
        self.font = pygame.font.SysFont("arial", 28)
        self.last_score = 0

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.state == MENU and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.start_game()
                    elif self.state == PLAYING and event.key == pygame.K_ESCAPE:
                        self.state = PAUSED
                    elif self.state == PAUSED and event.key == pygame.K_ESCAPE:
                        self.state = PLAYING
                    elif self.state == GAME_OVER and event.key == pygame.K_r:
                        self.start_game()
            self.update(dt)
            self.draw()
        pygame.quit()

    def start_game(self):
        self.level.restart()
        self.state = PLAYING
        self.last_score = 0

    def update(self, dt):
        if self.state == PLAYING:
            self.level.update(dt)
            if self.level.score > self.last_score and self.coin_sound:
                # simple feedback for last collection
                self.coin_sound.play()
            self.last_score = self.level.score
            if not self.level.player.alive:
                if self.death_sound:
                    self.death_sound.play()
                self.state = GAME_OVER

    def draw(self):
        if self.state in (PLAYING, GAME_OVER, PAUSED):
            self.level.draw(self.screen)
        if self.state == MENU:
            self.draw_menu()
        elif self.state == PAUSED:
            self.draw_pause()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        pygame.display.flip()

    def draw_menu(self):
        self.screen.fill((10, 10, 20))
        title = self.font.render("Tomb of the Mask", True, TEXT_COLOR)
        prompt = self.font.render("Press SPACE to start", True, TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        text = self.font.render("Paused - Press ESC to Resume", True, TEXT_COLOR)
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        score_text = self.font.render(f"Game Over - Score {self.level.score}", True, TEXT_COLOR)
        prompt = self.font.render("Press R to Restart", True, TEXT_COLOR)
        self.screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))


if __name__ == "__main__":
    Game().run()
