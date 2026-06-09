"""Главное меню и экран таблицы рейтинга."""

import math

import pygame

from . import assets, settings, ui
from .database import ScoreDatabase
from .editor import LevelEditor
from .game import GameScene
from .level import Level


class Menu:
    """Корневая сцена приложения: связывает игру, редактор и рейтинг."""

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.db = ScoreDatabase()
        self._running = True
        self._time = 0.0

        cx = settings.SCREEN_WIDTH // 2
        w, h = 340, 58
        gap = 74
        top = 250
        self.buttons = [
            ui.Button((cx - w // 2, top, w, h), "Играть", self._play, primary=True),
            ui.Button((cx - w // 2, top + gap, w, h), "Редактор уровней", self._open_editor),
            ui.Button((cx - w // 2, top + gap * 2, w, h), "Таблица рейтинга", self._show_scores),
            ui.Button((cx - w // 2, top + gap * 3, w, h), "Выход", self._quit),
        ]

    def run(self):
        while self._running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self._time += dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                for button in self.buttons:
                    button.handle_event(event)

            self._draw()
            pygame.display.flip()

    def _draw(self):
        ui.draw_background(self.screen)

        cx = settings.SCREEN_WIDTH // 2
        # Декоративные иконки слева/справа от заголовка
        bob = int(6 * math.sin(self._time * 2))
        apple = assets.image("apple_red.png", 56)
        star = assets.image("star.png", 48)
        if apple:
            self.screen.blit(apple, apple.get_rect(center=(cx - 170, 110 + bob)))
        if star:
            self.screen.blit(star, star.get_rect(center=(cx + 170, 110 - bob)))

        ui.draw_text(self.screen, "ЗМЕЙКА", 66, (cx, 110),
                     color=settings.COLOR_ACCENT, center=True, bold=True)
        ui.draw_text(self.screen, "курсовая работа", 22, (cx, 165),
                     color=settings.COLOR_TEXT_DIM, center=True)

        for button in self.buttons:
            button.draw(self.screen)

        ui.draw_text(self.screen,
                     "Стрелки / WASD — движение     •     ассеты: Twemoji (CC-BY 4.0)",
                     16, (cx, settings.SCREEN_HEIGHT - 28),
                     color=settings.COLOR_TEXT_DIM, center=True)

    # --- Действия кнопок ---
    def _play(self):
        """Играть на последнем созданном уровне (или на пустой карте)."""
        level = Level.load_last()
        GameScene(self.screen, self.clock, level=level, db=self.db).run()

    def _open_editor(self):
        LevelEditor(self.screen, self.clock).run()

    def _quit(self):
        self._running = False

    # --- Таблица рейтинга ---
    def _show_scores(self):
        rows = self.db.top_scores(limit=10)
        active = True
        while active:
            self.clock.tick(settings.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    active = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    active = False

            ui.draw_background(self.screen)
            cx = settings.SCREEN_WIDTH // 2
            ui.draw_text(self.screen, "Таблица рейтинга", 44, (cx, 60),
                         color=settings.COLOR_ACCENT, center=True, bold=True)

            # Заголовки колонок
            head_y = 130
            ui.draw_text(self.screen, "#", 20, (44, head_y), color=settings.COLOR_TEXT_DIM)
            ui.draw_text(self.screen, "Игрок", 20, (96, head_y), color=settings.COLOR_TEXT_DIM)
            ui.draw_text(self.screen, "Очки", 20, (300, head_y), color=settings.COLOR_TEXT_DIM)
            ui.draw_text(self.screen, "Уровень", 20, (392, head_y), color=settings.COLOR_TEXT_DIM)

            if not rows:
                ui.draw_text(self.screen, "Результатов пока нет.", 24, (cx, 260),
                             color=settings.COLOR_TEXT_DIM, center=True)

            medals = {1: (255, 215, 0), 2: (200, 200, 210), 3: (205, 140, 90)}
            for i, (player, score, level, length, played_at) in enumerate(rows, start=1):
                y = head_y + 24 + i * 38
                # Подложка строки
                row_rect = pygame.Rect(28, y - 6, settings.SCREEN_WIDTH - 56, 34)
                bg = (30, 34, 48) if i % 2 == 0 else (24, 27, 39)
                pygame.draw.rect(self.screen, bg, row_rect, border_radius=8)

                num_color = medals.get(i, settings.COLOR_TEXT)
                ui.draw_text(self.screen, str(i), 22, (44, y), color=num_color, bold=i <= 3)
                ui.draw_text(self.screen, player[:14], 22, (96, y))
                ui.draw_text(self.screen, str(score), 22, (300, y),
                             color=settings.COLOR_ACCENT, bold=True)
                ui.draw_text(self.screen, str(level)[:12], 20, (392, y),
                             color=settings.COLOR_TEXT_DIM)

            ui.draw_text(self.screen, "ESC / клик — назад", 18,
                         (cx, settings.SCREEN_HEIGHT - 32),
                         color=settings.COLOR_TEXT_DIM, center=True)
            pygame.display.flip()
