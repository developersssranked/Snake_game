"""Игровая сцена: основной игровой цикл «Змейки».

Партия идёт по таймеру. На поле появляются разные бонусы — см. модуль
`bonuses`. Игровой цикл вызывает у бонуса полиморфный `apply_effect`,
а конкретное поведение (рост, взрыв стен, броня, яд, время и т.д.)
определяется классом бонуса.
"""

import random

import pygame

from . import assets, settings, ui
from .bonuses import (
    NormalApple, GoldenApple, PoisonApple, Bomb, Armor,
    Antidote, SpeedUp, SlowDown, Clock, Poop,
)
from .database import ScoreDatabase
from .level import Level
from .snake import Snake
from .wall import Wall


class GameScene:
    """Одна партия игры на заданном уровне."""

    # Веса появления бонусов
    BONUS_WEIGHTS = [
        (NormalApple, 42),
        (PoisonApple, 16),
        (GoldenApple, 7),
        (Bomb, 6),
        (Armor, 6),
        (Antidote, 5),
        (SpeedUp, 4),
        (SlowDown, 4),
        (Clock, 4),
    ]

    def __init__(self, screen, clock, level=None, db=None):
        self.screen = screen
        self.clock = clock
        self.level = level or Level(name="Классика")
        self.db = db or ScoreDatabase()

        self.snake = Snake(self.level.start_pos)
        # Стены — рабочая копия: бомба/броня их разрушают, не трогая файл уровня
        self.wall_cells = set(self.level.wall_cells)
        self._rebuild_walls()

        self.apples = []              # бонусы на поле сейчас
        self.poops = []               # какашки (препятствия)
        self.poop_cells = set()
        self.score = 0

        self.move_timer = 0.0
        self._anim = 0.0
        self.time_left = settings.START_TIME

        # Эффект скорости
        self._speed_factor = 1.0
        self._speed_timer = 0.0
        # Сколько ещё какашек уронит отравленная змейка
        self._poop_steps_left = 0
        self._over_reason = ""

        self.spawn_apples()

    # --- Вспомогательное ---
    def _rebuild_walls(self):
        self.walls = [Wall(cell) for cell in self.wall_cells]

    def occupied_cells(self):
        """Все занятые клетки: змейка + стены + какашки + бонусы."""
        cells = set(self.snake.body)
        cells |= self.wall_cells
        cells |= self.poop_cells
        cells |= {apple.position for apple in self.apples}
        return cells

    def _place_apple(self, bonus_class):
        """Положить бонус заданного типа в случайную свободную клетку."""
        free = [
            (c, r)
            for c in range(settings.GRID_COLS)
            for r in range(settings.GRID_ROWS)
            if (c, r) not in self.occupied_cells()
        ]
        if not free:
            return
        self.apples.append(bonus_class(random.choice(free)))

    def spawn_apples(self):
        """Создать новую «порцию» бонусов.

        Тип выбирается по весу. Опасные бонусы (яд, стена-ловушка) кладутся
        вместе с обычным яблоком — у игрока всегда есть безопасный выбор.
        Съедание любого бонуса очищает всю порцию (см. _step).
        """
        self.apples = []

        classes, weights = zip(*self.BONUS_WEIGHTS)
        chosen = random.choices(classes, weights=weights, k=1)[0]
        self._place_apple(chosen)

        if chosen.hazard:
            self._place_apple(NormalApple)  # безопасная альтернатива

    # --- Действия, которые вызывают бонусы (через apply_effect) ---
    def explode_walls(self, center, radius):
        """Убрать стены в радиусе `radius` от центра. Вернуть их число."""
        cx, cy = center
        doomed = {
            (c, r) for (c, r) in self.wall_cells
            if (c - cx) ** 2 + (r - cy) ** 2 <= radius ** 2
        }
        self.wall_cells -= doomed
        self._rebuild_walls()
        return len(doomed)

    def add_time(self, seconds):
        self.time_left += seconds

    def set_speed(self, factor, duration):
        self._speed_factor = factor
        self._speed_timer = duration

    def poison_snake(self):
        """Отравить змейку: включить статус и запустить «дорожку» какашек."""
        self.snake.add_status("poison", settings.POISON_DURATION)
        self._poop_steps_left = settings.POOP_COUNT

    def stop_poop(self):
        self._poop_steps_left = 0

    def _game_over(self, reason):
        self._over_reason = reason
        return True

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
                # Таймеры эффектов и партии
                self.snake.tick_statuses(dt)
                if self._speed_timer > 0:
                    self._speed_timer -= dt
                    if self._speed_timer <= 0:
                        self._speed_factor = 1.0

                self.time_left -= dt
                if self.time_left <= 0:
                    self.time_left = 0
                    game_over = self._game_over("Время вышло")

                if not game_over:
                    self.move_timer += dt
                    interval = settings.MOVE_EVERY * self._speed_factor
                    if self.move_timer >= interval:
                        self.move_timer = 0.0
                        game_over = self._step()

            self._draw(game_over)
            pygame.display.flip()

            if game_over:
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

    def _drop_poop(self):
        """Уронить какашку на освободившейся хвостом клетке."""
        cell = self.snake.last_tail
        if cell is None or cell in self.poop_cells or cell in self.wall_cells:
            return
        self.poops.append(Poop(cell))
        self.poop_cells.add(cell)
        self._poop_steps_left -= 1

    def _step(self):
        """Один шаг логики. Возвращает True, если партия окончена."""
        self.snake.update(self)
        head = self.snake.head

        # Отравленная змейка роняет какашки (если нет антидота)
        if self._poop_steps_left > 0 and not self.snake.has_status("antidote"):
            self._drop_poop()

        # Границы поля и собственное тело — смерть всегда
        if self.snake.hits_wall_bounds():
            return self._game_over("Врезались в границу поля")
        if self.snake.hits_self():
            return self._game_over("Врезались в себя")

        # Стена: под бронёй ломаем её, иначе — смерть
        if head in self.wall_cells:
            if self.snake.has_status("armor"):
                self.wall_cells.discard(head)
                self._rebuild_walls()
            else:
                return self._game_over("Врезались в стену")

        # Какашка: под антидотом безопасно убираем, иначе — смерть
        if head in self.poop_cells:
            if self.snake.has_status("antidote"):
                self.poop_cells.discard(head)
                self.poops = [p for p in self.poops if p.position != head]
            else:
                return self._game_over("Съели какашку")

        # Съеден ли бонус? Полиморфный вызов apply_effect — поведение
        # зависит от конкретного класса бонуса.
        for apple in self.apples:
            if head == apple.position:
                self.score += apple.apply_effect(self.snake, self)
                self.score = max(0, self.score)
                self.spawn_apples()
                break

        return False

    # --- Отрисовка ---
    def _draw(self, game_over):
        ui.draw_background(self.screen)
        self._draw_grid()

        for wall in self.walls:
            wall.draw(self.screen)
        for poop in self.poops:
            poop.draw(self.screen)
        for apple in self.apples:
            apple.draw(self.screen, pulse=self._anim * 4)
        self.snake.draw(self.screen)

        self._draw_panel()

        if game_over:
            self._draw_overlay()

    def _draw_grid(self):
        for c in range(settings.GRID_COLS + 1):
            x = c * settings.CELL_SIZE
            pygame.draw.line(self.screen, settings.COLOR_GRID,
                             (x, settings.TOP_PANEL), (x, settings.SCREEN_HEIGHT))
        for r in range(settings.GRID_ROWS + 1):
            y = r * settings.CELL_SIZE + settings.TOP_PANEL
            pygame.draw.line(self.screen, settings.COLOR_GRID,
                             (0, y), (settings.PLAY_WIDTH, y))

    def _draw_panel(self):
        ui.draw_vertical_gradient(
            self.screen, (28, 31, 46), settings.COLOR_PANEL,
            pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.TOP_PANEL),
        )
        pygame.draw.line(self.screen, settings.COLOR_ACCENT_DIM,
                         (0, settings.TOP_PANEL - 1),
                         (settings.SCREEN_WIDTH, settings.TOP_PANEL - 1), 2)

        ui.draw_text(self.screen, f"Счёт: {self.score}", 26, (16, 8),
                     color=settings.COLOR_ACCENT, bold=True)
        ui.draw_text(self.screen, f"Длина: {self.snake.length}", 18, (16, 38),
                     color=settings.COLOR_TEXT_DIM)

        # Таймер (справа сверху), краснеет под конец
        secs = int(self.time_left)
        time_color = settings.COLOR_TIME_LOW if secs <= 10 else settings.COLOR_TEXT
        time_text = f"Время: {secs}"
        w = ui.get_font(26, bold=True).size(time_text)[0]
        ui.draw_text(self.screen, time_text, 26, (settings.SCREEN_WIDTH - 16 - w, 8),
                     color=time_color, bold=True)

        level_text = f"Уровень: {self.level.name}"
        lw = ui.get_font(18).size(level_text)[0]
        ui.draw_text(self.screen, level_text, 18,
                     (settings.SCREEN_WIDTH - 16 - lw, 40), color=settings.COLOR_TEXT_DIM)

        self._draw_statuses()

    def _draw_statuses(self):
        """Иконки активных эффектов с остатком времени, по центру панели."""
        effects = []
        if self.snake.has_status("armor"):
            effects.append(("shield.png", self.snake.status_remaining("armor")))
        if self.snake.has_status("antidote"):
            effects.append(("pill.png", self.snake.status_remaining("antidote")))
        if self.snake.has_status("poison"):
            effects.append(("skull.png", self.snake.status_remaining("poison")))
        if self._speed_timer > 0:
            icon = "fast.png" if self._speed_factor < 1 else "slow.png"
            effects.append((icon, self._speed_timer))

        if not effects:
            return

        slot = 64
        total = len(effects) * slot
        x = settings.SCREEN_WIDTH // 2 - total // 2
        for icon, remaining in effects:
            img = assets.image(icon, 26)
            if img:
                self.screen.blit(img, img.get_rect(center=(x + 14, 22)))
            ui.draw_text(self.screen, f"{remaining:.0f}s", 16, (x + 30, 14),
                         color=settings.COLOR_TEXT_DIM)
            x += slot

    def _draw_overlay(self):
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 11, 18, 200))
        self.screen.blit(overlay, (0, 0))
        cx = settings.SCREEN_WIDTH // 2
        ui.draw_text(self.screen, "Игра окончена", 48, (cx, settings.SCREEN_HEIGHT // 2 - 30),
                     color=settings.COLOR_NORMAL_APPLE, center=True, bold=True)
        if self._over_reason:
            ui.draw_text(self.screen, self._over_reason, 24,
                         (cx, settings.SCREEN_HEIGHT // 2 + 16),
                         color=settings.COLOR_TEXT_DIM, center=True)

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
            ui.draw_text(self.screen, "Игра окончена!", 46, (cx, 110),
                         color=settings.COLOR_NORMAL_APPLE, center=True, bold=True)
            if self._over_reason:
                ui.draw_text(self.screen, self._over_reason, 22, (cx, 152),
                             color=settings.COLOR_TEXT_DIM, center=True)
            ui.draw_text(self.screen, f"Ваш счёт: {self.score}", 34, (cx, 200),
                         color=settings.COLOR_ACCENT, center=True, bold=True)
            ui.draw_text(self.screen, f"Длина змейки: {self.snake.length}", 22, (cx, 242),
                         color=settings.COLOR_TEXT_DIM, center=True)
            ui.draw_text(self.screen, "Введите имя и нажмите Enter:", 24, (cx, 300),
                         color=settings.COLOR_TEXT_DIM, center=True)

            box = pygame.Rect(0, 0, 340, 52)
            box.center = (cx, 350)
            pygame.draw.rect(self.screen, settings.COLOR_BUTTON, box, border_radius=10)
            pygame.draw.rect(self.screen, settings.COLOR_ACCENT, box, width=2, border_radius=10)
            caret = "|" if int(self._anim * 2) % 2 == 0 else " "
            ui.draw_text(self.screen, name + caret, 28, box.center,
                         color=settings.COLOR_TEXT, center=True)

            pygame.display.flip()
            self._anim += 1.0 / settings.FPS

        return name.strip() or "Игрок"
