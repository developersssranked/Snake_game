"""Главное меню и экран таблицы рейтинга."""

import math

import pygame

from . import assets, settings, ui
from .bonuses import LEGEND
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
        w, h = 320, 48
        gap = 58
        top = 150
        self.buttons = [
            ui.Button((cx - w // 2, top, w, h), "Играть", self._play, primary=True),
            ui.Button((cx - w // 2, top + gap, w, h), "Бонусы (справка)", self._show_help),
            ui.Button((cx - w // 2, top + gap * 2, w, h), "Редактор уровней", self._open_editor),
            ui.Button((cx - w // 2, top + gap * 3, w, h), "Таблица рейтинга", self._show_scores),
            ui.Button((cx - w // 2, top + gap * 4, w, h), "Выход", self._quit),
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
        apple = assets.image("apple_red.png", 48)
        star = assets.image("star.png", 42)
        if apple:
            self.screen.blit(apple, apple.get_rect(center=(cx - 140, 70 + bob)))
        if star:
            self.screen.blit(star, star.get_rect(center=(cx + 140, 70 - bob)))

        ui.draw_text(self.screen, "ЗМЕЙКА", 58, (cx, 70),
                     color=settings.COLOR_ACCENT, center=True, bold=True)
        ui.draw_text(self.screen, "курсовая работа", 20, (cx, 112),
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

    # --- Справка по бонусам ---
    def _show_help(self):
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
            ui.draw_text(self.screen, "Бонусы и эффекты", 34, (cx, 34),
                         color=settings.COLOR_ACCENT, center=True, bold=True)

            y = 70
            row_h = 40
            for sprite, title, desc in LEGEND:
                row_rect = pygame.Rect(20, y, settings.SCREEN_WIDTH - 40, row_h - 5)
                pygame.draw.rect(self.screen, (26, 29, 42), row_rect, border_radius=8)
                img = assets.image(sprite, 26)
                if img:
                    self.screen.blit(img, img.get_rect(center=(44, y + (row_h - 5) // 2)))
                ui.draw_text(self.screen, title, 19, (70, y + 3),
                             color=settings.COLOR_TEXT, bold=True)
                ui.draw_text(self.screen, desc, 15, (70, y + 21),
                             color=settings.COLOR_TEXT_DIM)
                y += row_h

            ui.draw_text(self.screen, "ESC / клик — назад", 18,
                         (cx, settings.SCREEN_HEIGHT - 26),
                         color=settings.COLOR_TEXT_DIM, center=True)
            pygame.display.flip()

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
            ui.draw_text(self.screen, "Таблица рейтинга", 38, (cx, 44),
                         color=settings.COLOR_ACCENT, center=True, bold=True)

            # Заголовки колонок
            head_y = 100
            ui.draw_text(self.screen, "#", 18, (38, head_y), color=settings.COLOR_TEXT_DIM)
            ui.draw_text(self.screen, "Игрок", 18, (78, head_y), color=settings.COLOR_TEXT_DIM)
            ui.draw_text(self.screen, "Очки", 18, (250, head_y), color=settings.COLOR_TEXT_DIM)
            ui.draw_text(self.screen, "Уровень", 18, (322, head_y), color=settings.COLOR_TEXT_DIM)

            if not rows:
                ui.draw_text(self.screen, "Результатов пока нет.", 22, (cx, 230),
                             color=settings.COLOR_TEXT_DIM, center=True)

            medals = {1: (255, 215, 0), 2: (200, 200, 210), 3: (205, 140, 90)}
            for i, (player, score, level, length, played_at) in enumerate(rows, start=1):
                y = head_y + 18 + i * 32
                # Подложка строки
                row_rect = pygame.Rect(24, y - 5, settings.SCREEN_WIDTH - 48, 30)
                bg = (30, 34, 48) if i % 2 == 0 else (24, 27, 39)
                pygame.draw.rect(self.screen, bg, row_rect, border_radius=8)

                num_color = medals.get(i, settings.COLOR_TEXT)
                ui.draw_text(self.screen, str(i), 20, (38, y), color=num_color, bold=i <= 3)
                ui.draw_text(self.screen, player[:13], 20, (78, y))
                ui.draw_text(self.screen, str(score), 20, (250, y),
                             color=settings.COLOR_ACCENT, bold=True)
                ui.draw_text(self.screen, str(level)[:10], 18, (322, y),
                             color=settings.COLOR_TEXT_DIM)

            ui.draw_text(self.screen, "ESC / клик — назад", 18,
                         (cx, settings.SCREEN_HEIGHT - 32),
                         color=settings.COLOR_TEXT_DIM, center=True)
            pygame.display.flip()
