"""Редактор уровней: расстановка стен и точки старта змейки."""

import pygame

from . import settings, ui
from .level import Level


class LevelEditor:
    """Сцена редактора. Управление:

    - ЛКМ            — поставить/убрать стену
    - ПКМ            — задать стартовую позицию змейки
    - C              — очистить все стены
    - S              — сохранить уровень (ввести имя)
    - ESC            — выйти в меню
    """

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        # Открываем последний сохранённый уровень, чтобы его можно было
        # доработать. Если уровня нет — пустая карта.
        self.level = Level.load_last()
        self.level.name = "Свой уровень"

    def run(self):
        running = True
        while running:
            self.clock.tick(settings.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_c:
                        self.level.wall_cells.clear()
                    elif event.key == pygame.K_s:
                        path = self.level.save()       # replace: уровень всегда один
                        self._show_message(f"Уровень сохранён (заменён): {path}")
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cell = self._cell_at(event.pos)
                    if cell is not None:
                        if event.button == 1:            # ЛКМ — стена
                            self.level.toggle_wall(cell)
                        elif event.button == 3:          # ПКМ — старт
                            if cell not in self.level.wall_cells:
                                self.level.start_pos = cell

            self._draw()
            pygame.display.flip()

    def _cell_at(self, pos):
        """Перевести координаты мыши в клетку поля или None."""
        x, y = pos
        y -= settings.TOP_PANEL
        if y < 0:
            return None
        col, row = x // settings.CELL_SIZE, y // settings.CELL_SIZE
        if 0 <= col < settings.GRID_COLS and 0 <= row < settings.GRID_ROWS:
            return (col, row)
        return None

    def _draw(self):
        ui.draw_background(self.screen)

        # Сетка
        for c in range(settings.GRID_COLS + 1):
            x = c * settings.CELL_SIZE
            pygame.draw.line(self.screen, settings.COLOR_GRID,
                             (x, settings.TOP_PANEL), (x, settings.SCREEN_HEIGHT))
        for r in range(settings.GRID_ROWS + 1):
            y = r * settings.CELL_SIZE + settings.TOP_PANEL
            pygame.draw.line(self.screen, settings.COLOR_GRID,
                             (0, y), (settings.PLAY_WIDTH, y))

        # Стены
        for wall in self.level.build_walls():
            wall.draw(self.screen)

        # Точка старта змейки
        col, row = self.level.start_pos
        rect = pygame.Rect(col * settings.CELL_SIZE,
                           row * settings.CELL_SIZE + settings.TOP_PANEL,
                           settings.CELL_SIZE, settings.CELL_SIZE)
        pygame.draw.rect(self.screen, settings.COLOR_SNAKE_HEAD, rect, border_radius=6)

        # Панель-подсказка
        pygame.draw.rect(self.screen, settings.COLOR_PANEL,
                         pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.TOP_PANEL))
        ui.draw_text(self.screen, "Редактор уровней", 24, (16, 6),
                     color=settings.COLOR_ACCENT)
        ui.draw_text(self.screen,
                     "ЛКМ стена · ПКМ старт · C очистить · S сохранить · ESC выход",
                     14, (16, 38), color=settings.COLOR_TEXT_DIM)

    def _show_message(self, text):
        """Короткое сообщение на пару секунд."""
        for _ in range(int(settings.FPS * 1.5)):
            self.clock.tick(settings.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            ui.draw_background(self.screen)
            ui.draw_text(self.screen, text, 22,
                         (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2),
                         color=settings.COLOR_ACCENT, center=True)
            pygame.display.flip()
