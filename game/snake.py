"""Класс змейки."""

import pygame

from . import settings
from .base import GameObject


class Snake(GameObject):
    """Змейка — наследник GameObject.

    Хранит тело как список клеток (голова — первый элемент) и направление
    движения. Демонстрирует переопределение метода `draw` и инкапсуляцию
    состояния через свойства.
    """

    def __init__(self, start_pos):
        super().__init__(start_pos, settings.COLOR_SNAKE_HEAD)
        # Тело из трёх сегментов, растёт влево от головы
        col, row = start_pos
        self._body = [(col, row), (col - 1, row), (col - 2, row)]
        self._direction = (1, 0)        # двигаемся вправо
        self._next_direction = (1, 0)   # буфер ввода до следующего шага
        self._grow_pending = 0          # сколько сегментов ещё нарастить
        # Временные эффекты: имя -> остаток времени в секундах
        self._status = {}
        # Клетка, которую освободил хвост на последнем шаге (для какашек)
        self.last_tail = None

    # --- Свойства ---
    @property
    def head(self):
        return self._body[0]

    @property
    def body(self):
        return self._body

    @property
    def length(self):
        return len(self._body)

    @property
    def position(self):
        # Для змейки «позиция» — это голова
        return self._body[0]

    def set_direction(self, direction):
        """Сменить направление, запретив разворот на 180°."""
        dx, dy = direction
        cur_dx, cur_dy = self._direction
        if (dx, dy) == (-cur_dx, -cur_dy):
            return  # нельзя развернуться в себя
        self._next_direction = direction

    def grow(self, amount=1):
        """Запланировать рост на `amount` сегментов."""
        self._grow_pending += amount

    def shrink(self, amount=1):
        """Укоротить змейку, но оставить минимум один сегмент."""
        for _ in range(amount):
            if len(self._body) > 1:
                self._body.pop()

    # --- Временные эффекты (броня, антидот, отравление, скорость) ---
    def add_status(self, name, duration):
        """Включить эффект на `duration` секунд (продлевает текущий)."""
        self._status[name] = max(self._status.get(name, 0.0), duration)

    def remove_status(self, name):
        self._status.pop(name, None)

    def has_status(self, name):
        return self._status.get(name, 0.0) > 0.0

    def status_remaining(self, name):
        return self._status.get(name, 0.0)

    def tick_statuses(self, dt):
        """Уменьшить таймеры эффектов и убрать истёкшие."""
        for name in list(self._status):
            self._status[name] -= dt
            if self._status[name] <= 0.0:
                del self._status[name]

    def update(self, game):
        """Сделать один шаг: сдвинуть голову в направлении движения."""
        self._direction = self._next_direction
        dx, dy = self._direction
        col, row = self._body[0]
        new_head = (col + dx, row + dy)
        self._body.insert(0, new_head)

        if self._grow_pending > 0:
            self._grow_pending -= 1   # растём — хвост не убираем
            self.last_tail = None
        else:
            self.last_tail = self._body.pop()  # обычный шаг — хвост сдвигается

    def hits_wall_bounds(self):
        """Врезалась ли голова в границу поля."""
        col, row = self._body[0]
        return not (0 <= col < settings.GRID_COLS and 0 <= row < settings.GRID_ROWS)

    def hits_self(self):
        """Врезалась ли голова в собственное тело."""
        return self._body[0] in self._body[1:]

    def _cell_rect(self, cell, inset=2):
        col, row = cell
        return pygame.Rect(
            col * settings.CELL_SIZE + inset,
            row * settings.CELL_SIZE + settings.TOP_PANEL + inset,
            settings.CELL_SIZE - inset * 2,
            settings.CELL_SIZE - inset * 2,
        )

    @staticmethod
    def _lerp(c1, c2, t):
        """Линейная интерполяция цвета: плавный градиент по телу."""
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    def _palette(self):
        """Подобрать цвета тела в зависимости от активного эффекта.

        Возвращает (цвет_головы, цвет_тела, цвет_тела_2). Так отрисовка
        наглядно отражает состояние: броня — стальная, яд — фиолетовая.
        """
        if self.has_status("armor"):
            return (settings.COLOR_SNAKE_STEEL,
                    settings.COLOR_SNAKE_STEEL, settings.COLOR_SNAKE_STEEL_ALT)
        if self.has_status("poison"):
            return (settings.COLOR_SNAKE_POISON,
                    settings.COLOR_SNAKE_POISON, settings.COLOR_SNAKE_POISON_ALT)
        return (settings.COLOR_SNAKE_HEAD,
                settings.COLOR_SNAKE_BODY, settings.COLOR_SNAKE_BODY_ALT)

    def draw(self, surface):
        """Переопределённая отрисовка змейки (ПОЛИМОРФИЗМ).

        Тело рисуется как непрерывная лента с градиентом от головы к
        хвосту, голова — с глазами и языком по направлению движения.
        Цвет зависит от активного эффекта (броня/отравление).
        """
        head_color, body_color, body_alt = self._palette()
        n = len(self._body)

        # 1) Соединительные «перемычки» между соседними сегментами.
        for i in range(n - 1):
            t = i / max(1, n - 1)
            color = self._lerp(body_color, body_alt, t)
            a, b = self._body[i], self._body[i + 1]
            ax = a[0] * settings.CELL_SIZE + settings.CELL_SIZE // 2
            ay = a[1] * settings.CELL_SIZE + settings.CELL_SIZE // 2 + settings.TOP_PANEL
            bx = b[0] * settings.CELL_SIZE + settings.CELL_SIZE // 2
            by = b[1] * settings.CELL_SIZE + settings.CELL_SIZE // 2 + settings.TOP_PANEL
            pygame.draw.line(surface, color, (ax, ay), (bx, by), settings.CELL_SIZE - 4)

        # 2) Сегменты тела (с хвоста к голове, чтобы голова была сверху).
        for index in range(n - 1, 0, -1):
            t = index / max(1, n - 1)
            color = self._lerp(body_color, body_alt, t)
            pygame.draw.rect(surface, color, self._cell_rect(self._body[index]), border_radius=8)

        # 3) Голова.
        head_rect = self._cell_rect(self._body[0], inset=1)
        pygame.draw.rect(surface, head_color, head_rect, border_radius=9)
        self._draw_face(surface, head_rect)

    def _draw_face(self, surface, head_rect):
        """Глаза и язык на голове в зависимости от направления."""
        dx, dy = self._direction
        cx, cy = head_rect.center
        # Смещение глаз перпендикулярно движению
        off = settings.CELL_SIZE // 4
        perp = (-dy, dx)
        forward = (dx, dy)
        eye_r = max(2, settings.CELL_SIZE // 9)

        for sign in (1, -1):
            ex = cx + perp[0] * off * sign + forward[0] * (off // 2)
            ey = cy + perp[1] * off * sign + forward[1] * (off // 2)
            pygame.draw.circle(surface, (245, 245, 250), (ex, ey), eye_r)
            pygame.draw.circle(surface, (20, 20, 30), (ex, ey), max(1, eye_r // 2))

        # Язык — короткая красная линия впереди головы
        tx = cx + forward[0] * (settings.CELL_SIZE // 2)
        ty = cy + forward[1] * (settings.CELL_SIZE // 2)
        pygame.draw.line(surface, (220, 60, 80), (cx, cy), (tx, ty), 2)
