"""Загрузка и кэширование графических ассетов.

Картинки (PNG) лежат в папке assets/. Функция `image()` загружает их
один раз и кэширует масштабированную версию. Если файла нет —
возвращает None, и вызывающий код рисует фигуру вручную (запасной
вариант). Так игра работает даже без ассетов.

Источник иконок: Twemoji (Twitter), лицензия CC-BY 4.0.
"""

import os

import pygame

from . import settings

# Кэш: ключ (имя_файла, размер) -> Surface
_cache = {}


def image(filename, size):
    """Вернуть масштабированную картинку или None, если файла нет."""
    key = (filename, size)
    if key in _cache:
        return _cache[key]

    path = os.path.join(settings.ASSETS_DIR, filename)
    if not os.path.isfile(path):
        _cache[key] = None
        return None

    surface = pygame.image.load(path).convert_alpha()
    surface = pygame.transform.smoothscale(surface, (size, size))
    _cache[key] = surface
    return surface
