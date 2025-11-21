import pygame
from settings import *
from game import Game


def main():
    pygame.init()
    pygame.display.set_caption("Tomb of the Mask — Prototype")

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        fps = clock.get_fps()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        game.update(dt, events, fps)
        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()