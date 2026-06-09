"""Вспомогательные элементы интерфейса: кнопки и текст.

Вынесено отдельно, чтобы меню, редактор и экран рейтинга не дублировали
один и тот же код отрисовки.
"""

import pygame

from . import settings


_font_cache = {}


def get_font(size, bold=False):
    """Системный шрифт с поддержкой кириллицы (с кэшированием)."""
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("segoeui,arial", size, bold=bold)
    return _font_cache[key]


def draw_vertical_gradient(surface, top_color, bottom_color, rect=None):
    """Залить прямоугольник вертикальным градиентом."""
    rect = rect or surface.get_rect()
    h = max(1, rect.height)
    for y in range(h):
        t = y / h
        color = tuple(int(a + (b - a) * t) for a, b in zip(top_color, bottom_color))
        pygame.draw.line(surface, color, (rect.left, rect.top + y), (rect.right, rect.top + y))


def draw_background(surface):
    """Фон-градиент для всех экранов."""
    draw_vertical_gradient(surface, settings.COLOR_BG_TOP, settings.COLOR_BG_BOTTOM)


def draw_text(surface, text, size, pos, color=settings.COLOR_TEXT, center=False, bold=False):
    """Нарисовать строку. `pos` — левый верх или центр (если center=True)."""
    font = get_font(size, bold=bold)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(img, rect)
    return rect


class Button:
    """Кликабельная кнопка с плавной анимацией наведения."""

    def __init__(self, rect, label, action=None, primary=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action          # функция без аргументов
        self.primary = primary        # главная кнопка — подсвечена акцентом
        self._hovered = False
        self._t = 0.0                 # 0..1, плавность подсветки

    def handle_event(self, event):
        """Обработать событие мыши. Возвращает True, если кнопку нажали."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()
                return True
        return False

    def draw(self, surface):
        # Плавное приближение _t к цели (наведение)
        target = 1.0 if self._hovered else 0.0
        self._t += (target - self._t) * 0.25

        base = settings.COLOR_BUTTON
        hi = settings.COLOR_BUTTON_HOVER
        fill = tuple(int(a + (b - a) * self._t) for a, b in zip(base, hi))

        # Лёгкое «приподнятие» при наведении
        rect = self.rect.inflate(int(6 * self._t), int(6 * self._t))

        # Тень
        shadow = rect.move(0, 4)
        sh = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 90), sh.get_rect(), border_radius=12)
        surface.blit(sh, shadow.topleft)

        pygame.draw.rect(surface, fill, rect, border_radius=12)
        border = settings.COLOR_ACCENT if self.primary else settings.COLOR_ACCENT_DIM
        width = 3 if self.primary else 2
        pygame.draw.rect(surface, border, rect, width=width, border_radius=12)

        text_color = settings.COLOR_ACCENT if self.primary else settings.COLOR_BUTTON_TEXT
        draw_text(surface, self.label, 27, rect.center,
                  color=text_color, center=True, bold=self.primary)
