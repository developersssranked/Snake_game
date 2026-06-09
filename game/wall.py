"""Класс стены — препятствие, расставляемое в редакторе уровней."""

import pygame

from . import settings
from .base import GameObject


class Wall(GameObject):
    """Неподвижное препятствие. Столкновение с ним — конец игры."""

    def __init__(self, position):
        super().__init__(position, settings.COLOR_WALL)

    def update(self, game):
        pass  # стена статична

    def draw(self, surface):
        pygame.draw.rect(surface, self._color, self.rect(), border_radius=3)
