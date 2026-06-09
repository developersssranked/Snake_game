"""Базовый класс для всех игровых объектов.

`GameObject` — это абстрактный базовый класс (АБСТРАКЦИЯ). От него
наследуются змейка, яблоки и стены (НАСЛЕДОВАНИЕ). Каждый потомок
по-своему реализует метод `update`, а игра работает с любым объектом
одинаково — через общий интерфейс (ПОЛИМОРФИЗМ).
"""

from abc import ABC, abstractmethod

import pygame

from . import settings


class GameObject(ABC):
    """Любой объект на игровом поле: занимает клетку и умеет рисоваться."""

    def __init__(self, position, color):
        # Поля приватные (ИНКАПСУЛЯЦИЯ): снаружи к ним обращаются
        # только через свойства ниже.
        self._position = position      # кортеж (колонка, строка)
        self._color = color

    # --- Свойства: контролируемый доступ к приватным полям ---
    @property
    def position(self):
        """Координаты объекта в клетках: (колонка, строка)."""
        return self._position

    @position.setter
    def position(self, value):
        self._position = value

    @property
    def color(self):
        return self._color

    # --- Абстрактный метод: каждый потомок обязан его реализовать ---
    @abstractmethod
    def update(self, game):
        """Логика объекта за один игровой шаг.

        `game` — ссылка на игру, через неё объект видит остальной мир.
        """
        raise NotImplementedError

    # --- Метод с реализацией по умолчанию (можно переопределить) ---
    def draw(self, surface):
        """Нарисовать объект как залитую клетку. По умолчанию для стен
        и яблок этого достаточно; змейка переопределяет метод."""
        pygame.draw.rect(surface, self._color, self.rect())

    def rect(self):
        """Прямоугольник объекта в пикселях с учётом верхней панели."""
        col, row = self._position
        return pygame.Rect(
            col * settings.CELL_SIZE,
            row * settings.CELL_SIZE + settings.TOP_PANEL,
            settings.CELL_SIZE,
            settings.CELL_SIZE,
        )

    def occupies(self, cell):
        """Проверка: занимает ли объект данную клетку."""
        return self._position == cell
