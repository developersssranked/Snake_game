"""Модель уровня и его сохранение/загрузка.

Уровень хранит расположение стен и стартовую позицию змейки.
Сохраняется в JSON-файл в папке levels/.
"""

import json
import os

from . import settings
from .wall import Wall


class Level:
    """Описание уровня: стены + точка старта змейки."""

    def __init__(self, name="Без названия", walls=None, start_pos=None):
        self.name = name
        # Множество клеток со стенами: {(col, row), ...}
        self.wall_cells = set(walls) if walls else set()
        self.start_pos = start_pos or (settings.GRID_COLS // 2, settings.GRID_ROWS // 2)

    # --- Работа со стенами (используется редактором) ---
    def toggle_wall(self, cell):
        """Поставить стену в клетке или убрать, если она уже там."""
        if cell in self.wall_cells:
            self.wall_cells.discard(cell)
        else:
            self.wall_cells.add(cell)

    def build_walls(self):
        """Создать объекты Wall из набора клеток."""
        return [Wall(cell) for cell in self.wall_cells]

    # --- Сохранение и загрузка ---
    def to_dict(self):
        return {
            "name": self.name,
            "start_pos": list(self.start_pos),
            "walls": [list(c) for c in sorted(self.wall_cells)],
        }

    def save(self, directory=settings.LEVELS_DIR):
        """Сохранить уровень. Уровень всегда один: новое сохранение
        перезаписывает (replace) предыдущий файл, а не добавляет новый."""
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, settings.LEVEL_FILE)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Оставляем только клетки в пределах сетки — на случай, если уровень
        # сохранён при другом (большем) размере поля.
        def in_bounds(cell):
            c, r = cell
            return 0 <= c < settings.GRID_COLS and 0 <= r < settings.GRID_ROWS

        walls = {tuple(c) for c in data.get("walls", []) if in_bounds(tuple(c))}
        default_start = (settings.GRID_COLS // 2, settings.GRID_ROWS // 2)
        start = tuple(data.get("start_pos", default_start))
        if not in_bounds(start):
            start = default_start
        return cls(name=data.get("name", "Свой уровень"), walls=walls, start_pos=start)

    @classmethod
    def load_last(cls, directory=settings.LEVELS_DIR):
        """Загрузить последний созданный уровень.

        Если файла нет — вернуть пустую карту («Классика»).
        """
        path = os.path.join(directory, settings.LEVEL_FILE)
        if os.path.isfile(path):
            return cls.load(path)
        return cls(name="Классика")
