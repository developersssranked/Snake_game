"""Точка входа в игру «Змейка».

Запуск:  python main.py
"""

import pygame

from game import settings
from game.menu import Menu


def main():
    pygame.init()
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption(settings.WINDOW_TITLE)
    clock = pygame.time.Clock()

    try:
        Menu(screen, clock).run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
