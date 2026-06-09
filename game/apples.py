"""Яблоки разных типов.

Ключевой пример ПОЛИМОРФИЗМА в проекте: есть общий абстрактный класс
`Apple`, а конкретные яблоки по-разному реализуют `apply_effect`.
Игра, подбирая яблоко, просто вызывает `apple.apply_effect(...)`
и не знает, какой именно это тип.
"""

import math
from abc import abstractmethod

import pygame

from . import assets, settings
from .base import GameObject


class Apple(GameObject):
    """Абстрактное яблоко — наследник GameObject.

    Подклассы задают цвет, число очков, иконку и эффект при съедании.
    """

    # Имя типа — для отладки и статистики
    title = "Яблоко"
    # Имя файла иконки в папке assets/ (если есть)
    sprite = None

    def __init__(self, position, color, points):
        super().__init__(position, color)
        self._points = points

    @property
    def points(self):
        return self._points

    @abstractmethod
    def apply_effect(self, snake, game):
        """Что произойдёт, когда змейка съест это яблоко.

        Возвращает изменение счёта (может быть и отрицательным).
        """
        raise NotImplementedError

    # Яблоки не имеют собственной пошаговой логики — реализуем «пустой» update
    def update(self, game):
        pass

    def draw(self, surface, pulse=0.0):
        """Нарисовать яблоко: иконкой из ассетов либо кружком (запас).

        `pulse` — фаза анимации (0..2π) для лёгкого «дыхания» и свечения.
        """
        rect = self.rect()
        cx, cy = rect.center

        # Мягкое свечение под объектом
        glow = pygame.Surface((settings.CELL_SIZE * 2, settings.CELL_SIZE * 2), pygame.SRCALPHA)
        radius = int(settings.CELL_SIZE * 0.7 + 2 * math.sin(pulse))
        pygame.draw.circle(glow, (*self._color, 60), glow.get_rect().center, radius)
        surface.blit(glow, (cx - settings.CELL_SIZE, cy - settings.CELL_SIZE))

        sprite = assets.image(self.sprite, settings.CELL_SIZE - 2) if self.sprite else None
        if sprite is not None:
            scale = 1.0 + 0.06 * math.sin(pulse)        # лёгкая пульсация
            size = int((settings.CELL_SIZE - 2) * scale)
            img = pygame.transform.smoothscale(sprite, (size, size))
            surface.blit(img, img.get_rect(center=(cx, cy)))
        else:
            pygame.draw.circle(surface, self._color, (cx, cy), settings.CELL_SIZE // 2 - 3)


class NormalApple(Apple):
    """Обычное яблоко: +1 сегмент и немного очков."""

    title = "Обычное"
    sprite = "apple_red.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_NORMAL_APPLE, points=10)

    def apply_effect(self, snake, game):
        snake.grow(1)
        return self._points


class GoldenApple(Apple):
    """Золотая звезда: редкая, +2 сегмента и много очков."""

    title = "Золотое"
    sprite = "star.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_GOLDEN_APPLE, points=30)

    def apply_effect(self, snake, game):
        snake.grow(2)
        return self._points


class PoisonApple(Apple):
    """Отравленное яблоко (череп): укорачивает змейку и отнимает очки."""

    title = "Отравленное"
    sprite = "skull.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_POISON_APPLE, points=-15)

    def apply_effect(self, snake, game):
        snake.shrink(1)
        return self._points  # отрицательное значение — счёт уменьшится
