"""Бонусы (собираемые объекты) и какашки.

Здесь — главный пример ПОЛИМОРФИЗМА в проекте. Все бонусы наследуют
абстрактный класс `Bonus`, но метод `apply_effect` у каждого делает
принципиально РАЗНОЕ: одни растят/укорачивают змейку, другие взрывают
стены, дают броню, травят, ускоряют, добавляют время или мгновенно
заканчивают игру. Игровой цикл вызывает `bonus.apply_effect(snake, game)`
не зная конкретного типа — поведение определяется классом объекта.
"""

import math
from abc import abstractmethod

import pygame

from . import assets, settings
from .base import GameObject


class Bonus(GameObject):
    """Абстрактный собираемый бонус.

    Атрибуты класса задают «паспорт» бонуса: название, иконку и признак
    опасности. Опасные бонусы (`hazard = True`) на поле всегда соседствуют
    с обычным яблоком, чтобы у игрока был безопасный выбор.
    """

    title = "Бонус"
    sprite = None        # имя файла иконки в assets/
    hazard = False       # опасные бонусы спавнятся в паре с яблоком

    def __init__(self, position, color, points=0):
        super().__init__(position, color)
        self._points = points

    @property
    def points(self):
        return self._points

    @abstractmethod
    def apply_effect(self, snake, game):
        """Применить эффект бонуса. Возвращает изменение счёта."""
        raise NotImplementedError

    def update(self, game):
        pass  # бонусы статичны

    def draw(self, surface, pulse=0.0):
        """Иконка из ассетов либо кружок (запас) + мягкое свечение."""
        rect = self.rect()
        cx, cy = rect.center

        glow = pygame.Surface((settings.CELL_SIZE * 2, settings.CELL_SIZE * 2), pygame.SRCALPHA)
        radius = int(settings.CELL_SIZE * 0.7 + 2 * math.sin(pulse))
        pygame.draw.circle(glow, (*self._color, 60), glow.get_rect().center, radius)
        surface.blit(glow, (cx - settings.CELL_SIZE, cy - settings.CELL_SIZE))

        sprite = assets.image(self.sprite, settings.CELL_SIZE - 2) if self.sprite else None
        if sprite is not None:
            scale = 1.0 + 0.06 * math.sin(pulse)
            size = int((settings.CELL_SIZE - 2) * scale)
            img = pygame.transform.smoothscale(sprite, (size, size))
            surface.blit(img, img.get_rect(center=(cx, cy)))
        else:
            pygame.draw.circle(surface, self._color, (cx, cy), settings.CELL_SIZE // 2 - 3)


# --- Еда: рост / золото / яд ---

class NormalApple(Bonus):
    """Обычное яблоко: +1 сегмент."""

    title = "Обычное яблоко"
    sprite = "apple_red.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_NORMAL_APPLE, points=10)

    def apply_effect(self, snake, game):
        snake.grow(1)
        return self._points


class GoldenApple(Bonus):
    """Золотая звезда: +2 сегмента и много очков (редкая)."""

    title = "Золотая звезда"
    sprite = "star.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_GOLDEN_APPLE, points=30)

    def apply_effect(self, snake, game):
        snake.grow(2)
        return self._points


class PoisonApple(Bonus):
    """Отравленное яблоко: травит змейку — какое-то время она роняет
    за собой какашки, и отнимает очки. Антидот делает его безвредным."""

    title = "Отравленное яблоко"
    sprite = "skull.png"
    hazard = True

    def __init__(self, position):
        super().__init__(position, settings.COLOR_POISON_APPLE, points=-15)

    def apply_effect(self, snake, game):
        if snake.has_status("antidote"):
            return 5  # под антидотом — безвредно, маленький бонус
        snake.shrink(1)
        game.poison_snake()
        return self._points


# --- Бонусы, взаимодействующие со стенами ---

class Bomb(Bonus):
    """Бомба: взрывает все стены в радиусе вокруг себя."""

    title = "Бомба"
    sprite = "bomb.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_BOMB, points=20)

    def apply_effect(self, snake, game):
        destroyed = game.explode_walls(self.position, settings.BOMB_RADIUS)
        return self._points + destroyed * 2  # больше стен — больше очков


class Armor(Bonus):
    """Броня: делает змейку «стальной» — она ломает стены, проходя сквозь."""

    title = "Броня"
    sprite = "shield.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_ARMOR, points=15)

    def apply_effect(self, snake, game):
        snake.add_status("armor", settings.ARMOR_DURATION)
        return self._points


# --- Бонусы-статусы и таймер ---

class Antidote(Bonus):
    """Антидот: снимает отравление и позволяет какое-то время есть
    отравленные яблоки и какашки без последствий."""

    title = "Антидот"
    sprite = "pill.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_ANTIDOTE, points=10)

    def apply_effect(self, snake, game):
        snake.add_status("antidote", settings.ANTIDOTE_DURATION)
        snake.remove_status("poison")
        game.stop_poop()
        return self._points


class SpeedUp(Bonus):
    """Ускорение: змейка временно движется быстрее."""

    title = "Ускорение"
    sprite = "fast.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_SPEED, points=5)

    def apply_effect(self, snake, game):
        game.set_speed(settings.SPEED_FAST_FACTOR, settings.SPEED_DURATION)
        return self._points


class SlowDown(Bonus):
    """Замедление: змейка временно движется медленнее (легче управлять)."""

    title = "Замедление"
    sprite = "slow.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_SLOW, points=5)

    def apply_effect(self, snake, game):
        game.set_speed(settings.SPEED_SLOW_FACTOR, settings.SPEED_DURATION)
        return self._points


class Clock(Bonus):
    """Часы: добавляют время на таймере партии."""

    title = "Часы (+время)"
    sprite = "clock.png"

    def __init__(self, position):
        super().__init__(position, settings.COLOR_CLOCK, points=5)

    def apply_effect(self, snake, game):
        game.add_time(settings.CLOCK_BONUS)
        return self._points


# --- Какашка: не бонус, а препятствие (как стена) ---

class Poop(GameObject):
    """След отравленной змейки. Работает как стена: врезался — конец игры.
    Под антидотом её можно безопасно «съесть»."""

    def __init__(self, position):
        super().__init__(position, settings.COLOR_POOP)

    def update(self, game):
        pass

    def draw(self, surface):
        sprite = assets.image("poop.png", settings.CELL_SIZE - 4)
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=self.rect().center))
        else:
            pygame.draw.circle(surface, self._color, self.rect().center,
                               settings.CELL_SIZE // 2 - 4)


# Справочник для экрана «Бонусы»: (иконка, название, описание)
LEGEND = [
    ("apple_red.png", "Обычное яблоко", "+1 длина, +10 очков"),
    ("star.png", "Золотая звезда", "+2 длины, +30 очков (редко)"),
    ("skull.png", "Отравленное яблоко", "травит: змейка роняет какашки, -15"),
    ("poop.png", "Какашка", "след яда; врезался — конец игры"),
    ("pill.png", "Антидот", "снимает яд, какашки и яд безвредны"),
    ("bomb.png", "Бомба", "взрывает стены в радиусе вокруг себя"),
    ("shield.png", "Броня", "змейка стальная — ломает стены собой"),
    ("fast.png", "Ускорение", "временно быстрее"),
    ("slow.png", "Замедление", "временно медленнее"),
    ("clock.png", "Часы", "+время на таймере"),
]
