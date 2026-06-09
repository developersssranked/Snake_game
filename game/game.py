"""Игровая сцена: основной игровой цикл «Змейки»."""

import math
import random

import pygame

from . import settings, ui
from .apples import NormalApple, GoldenApple, PoisonApple
from .database import ScoreDatabase
from .level import Level
from .snake import Snake


class GameScene:
    """Одна партия игры на заданном уровне."""

    # Веса появления яблок: обычные — часто, отравленные — реже, золотые — редко
    APPLE_WEIGHTS = [
        (NormalApple, 60),
        (PoisonApple, 30),
        (GoldenApple, 10),
    ]

    def __init__(self, screen, clock, level=None, db=None):
        self.screen = screen
        self.clock = clock
        self.level = level or Level(name="Классика")
        self.db = db or ScoreDatabase()

        self.snake = Snake(self.level.start_pos)
        self.walls = self.level.build_walls()
        self.apples = []          # яблоки, лежащие на поле прямо сейчас
        self.score = 0
        self.move_timer = 0.0
        self._anim = 0.0          # общее время для анимаций
        self.spawn_apples()

    # --- Вспомогательное ---
    def occupied_cells(self):
        """Все занятые клетки: тело змейки + стены + лежащие яблоки."""
        cells = set(self.snake.body)
        cells |= self.level.wall_cells
        cells |= {apple.position for apple in self.apples}
        return cells

    def _place_apple(self, apple_class):
        """Положить яблоко заданного типа в случайную свободную клетку."""
        free = [
            (c, r)
            for c in range(settings.GRID_COLS)
            for r in range(settings.GRID_ROWS)
            if (c, r) not in self.occupied_cells()
        ]
        if not free:
            return
        self.apples.append(apple_class(random.choice(free)))

    def spawn_apples(self):
        """Создать новую «порцию» яблок.

        Тип выбирается по весу. Если выпало отравленное, рядом сразу
        кладётся обычное — чтобы игрок не был обязан есть отравленное.
        Съедание любого яблока очищает всю порцию (см. _step), поэтому
        «парное» обычное исчезает вместе с отравленным, и наоборот.
        """
        self.apples = []

        # Полиморфное создание: выбираем класс по весу
        classes, weights = zip(*self.APPLE_WEIGHTS)
        chosen = random.choices(classes, weights=weights, k=1)[0]
        self._place_apple(chosen)

        if chosen is PoisonApple:
            self._place_apple(NormalApple)  # безопасная альтернатива

    # --- Основной цикл ---
    def run(self):
        """Запустить партию. Возвращает финальный счёт."""
        running = True
        game_over = False

        while running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self._anim += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif not game_over:
                        self._handle_direction(event.key)

            if not game_over:
                self.move_timer += dt
                if self.move_timer >= settings.MOVE_EVERY:
                    self.move_timer = 0.0
                    game_over = self._step()

            self._draw(game_over)
            pygame.display.flip()

            if game_over:
                # Небольшая пауза, затем экран ввода имени и сохранение
                self._game_over_sequence()
                running = False

        return self.score

    def _handle_direction(self, key):
        mapping = {
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
        }
        if key in mapping:
            self.snake.set_direction(mapping[key])

    def _step(self):
        """Один шаг логики. Возвращает True, если партия окончена."""
        self.snake.update(self)

        # Столкновения со стеной поля, собой или препятствием
        if (
            self.snake.hits_wall_bounds()
            or self.snake.hits_self()
            or self.snake.head in self.level.wall_cells
        ):
            return True

        # Съедено ли какое-то яблоко из порции? Вызов apply_effect —
        # пример полиморфизма: код одинаков для любого типа яблока.
        for apple in self.apples:
            if self.snake.head == apple.position:
                self.score += apple.apply_effect(self.snake, self)
                self.score = max(0, self.score)
                # Очищаем всю порцию: «парное» яблоко исчезает вместе
                # со съеденным, затем кладём новую порцию.
                self.spawn_apples()
                break

        return False

    # --- Отрисовка ---
    def _draw(self, game_over):
        # Фон поля — лёгкий градиент только под игровым полем
        ui.draw_background(self.screen)
        self._draw_grid()

        for wall in self.walls:
            wall.draw(self.screen)
        for apple in self.apples:
            apple.draw(self.screen, pulse=self._anim * 4)
        self.snake.draw(self.screen)

        self._draw_panel()

        if game_over:
            self._draw_overlay("Игра окончена")

    def _draw_grid(self):
        for c in range(settings.GRID_COLS + 1):
            x = c * settings.CELL_SIZE
            pygame.draw.line(
                self.screen, settings.COLOR_GRID,
                (x, settings.TOP_PANEL), (x, settings.SCREEN_HEIGHT),
            )
        for r in range(settings.GRID_ROWS + 1):
            y = r * settings.CELL_SIZE + settings.TOP_PANEL
            pygame.draw.line(
                self.screen, settings.COLOR_GRID,
                (0, y), (settings.PLAY_WIDTH, y),
            )

    def _draw_panel(self):
        ui.draw_vertical_gradient(
            self.screen, (28, 31, 46), settings.COLOR_PANEL,
            pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.TOP_PANEL),
        )
        pygame.draw.line(self.screen, settings.COLOR_ACCENT_DIM,
                         (0, settings.TOP_PANEL - 1),
                         (settings.SCREEN_WIDTH, settings.TOP_PANEL - 1), 2)

        ui.draw_text(self.screen, f"Счёт: {self.score}", 28, (16, 10),
                     color=settings.COLOR_ACCENT, bold=True)
        ui.draw_text(self.screen, f"Длина: {self.snake.length}", 20, (16, 38),
                     color=settings.COLOR_TEXT_DIM)

        # Название уровня выровнено по правому краю
        text = f"Уровень: {self.level.name}"
        w = ui.get_font(20).size(text)[0]
        ui.draw_text(self.screen, text, 20, (settings.SCREEN_WIDTH - 16 - w, 22),
                     color=settings.COLOR_TEXT_DIM)

    def _draw_overlay(self, text):
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 11, 18, 200))
        self.screen.blit(overlay, (0, 0))
        ui.draw_text(self.screen, text, 48,
                     (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 20),
                     color=settings.COLOR_NORMAL_APPLE, center=True, bold=True)

    def _game_over_sequence(self):
        """Показать экран окончания, спросить имя и сохранить результат."""
        name = self._ask_name()
        if name:
            self.db.add_score(name, self.score, self.level.name, self.snake.length)

    def _ask_name(self):
        """Простой ввод имени игрока с клавиатуры."""
        name = ""
        active = True
        while active:
            self.clock.tick(settings.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        active = False
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.unicode and len(name) < 16 and event.unicode.isprintable():
                        name += event.unicode

            cx = settings.SCREEN_WIDTH // 2
            ui.draw_background(self.screen)
            ui.draw_text(self.screen, "Игра окончена!", 46, (cx, 120),
                         color=settings.COLOR_NORMAL_APPLE, center=True, bold=True)
            ui.draw_text(self.screen, f"Ваш счёт: {self.score}", 34, (cx, 185),
                         color=settings.COLOR_ACCENT, center=True, bold=True)
            ui.draw_text(self.screen, f"Длина змейки: {self.snake.length}", 22, (cx, 230),
                         color=settings.COLOR_TEXT_DIM, center=True)
            ui.draw_text(self.screen, "Введите имя и нажмите Enter:", 24, (cx, 290),
                         color=settings.COLOR_TEXT_DIM, center=True)

            box = pygame.Rect(0, 0, 340, 52)
            box.center = (cx, 340)
            pygame.draw.rect(self.screen, settings.COLOR_BUTTON, box, border_radius=10)
            pygame.draw.rect(self.screen, settings.COLOR_ACCENT, box, width=2, border_radius=10)
            caret = "|" if int(self._anim * 2) % 2 == 0 else " "
            ui.draw_text(self.screen, name + caret, 28, box.center,
                         color=settings.COLOR_TEXT, center=True)

            pygame.display.flip()
            self._anim += 1.0 / settings.FPS

        return name.strip() or "Игрок"
