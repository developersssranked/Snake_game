"""Глобальные настройки и константы игры.

Все «магические числа» и цвета вынесены сюда, чтобы их было удобно
менять в одном месте.
"""

# --- Размеры игрового поля ---
GRID_COLS = 19          # число клеток по горизонтали
GRID_ROWS = 19          # число клеток по вертикали
CELL_SIZE = 24          # размер одной клетки в пикселях

# Поле занимает основную часть экрана, сверху — панель со счётом
TOP_PANEL = 60
PLAY_WIDTH = GRID_COLS * CELL_SIZE
PLAY_HEIGHT = GRID_ROWS * CELL_SIZE

SCREEN_WIDTH = PLAY_WIDTH
SCREEN_HEIGHT = PLAY_HEIGHT + TOP_PANEL

FPS = 60                # кадров в секунду
MOVE_EVERY = 0.22       # как часто (в секундах) змейка делает шаг (больше = медленнее)

# --- Параметры игры по таймеру ---
START_TIME = 60.0       # стартовый запас времени, сек
CLOCK_BONUS = 15.0      # сколько времени добавляют «часы»

# --- Длительности эффектов (сек) ---
ARMOR_DURATION = 7.0    # сколько змейка остаётся «стальной»
ANTIDOTE_DURATION = 8.0 # сколько действует антидот
POISON_DURATION = 1.6   # визуальный статус отравления
SPEED_DURATION = 4.0    # длительность ускорения/замедления

SPEED_FAST_FACTOR = 0.55  # множитель шага при ускорении (меньше = быстрее)
SPEED_SLOW_FACTOR = 1.9   # множитель шага при замедлении

BOMB_RADIUS = 3         # радиус взрыва бомбы (в клетках)
POOP_COUNT = 5          # сколько какашек роняет отравленная змейка

# --- Цвета (R, G, B) ---
COLOR_BG = (16, 18, 27)
COLOR_BG_TOP = (24, 27, 40)        # верх градиента фона
COLOR_BG_BOTTOM = (12, 13, 20)     # низ градиента фона
COLOR_GRID = (32, 35, 48)
COLOR_PANEL = (20, 22, 33)
COLOR_TEXT = (236, 238, 248)
COLOR_TEXT_DIM = (140, 146, 168)

COLOR_SNAKE_HEAD = (120, 240, 150)
COLOR_SNAKE_BODY = (70, 200, 120)
COLOR_SNAKE_BODY_ALT = (55, 175, 105)  # для «полосок» на теле

# «Стальная» змейка под бронёй и отравленная
COLOR_SNAKE_STEEL = (200, 205, 220)
COLOR_SNAKE_STEEL_ALT = (140, 148, 170)
COLOR_SNAKE_POISON = (170, 110, 210)
COLOR_SNAKE_POISON_ALT = (120, 70, 160)

COLOR_NORMAL_APPLE = (220, 70, 70)
COLOR_POISON_APPLE = (150, 80, 200)
COLOR_GOLDEN_APPLE = (235, 200, 60)
COLOR_BOMB = (60, 60, 70)
COLOR_ARMOR = (120, 170, 230)
COLOR_ANTIDOTE = (90, 210, 200)
COLOR_SPEED = (240, 180, 60)
COLOR_SLOW = (110, 150, 240)
COLOR_CLOCK = (230, 120, 150)
COLOR_POOP = (120, 85, 55)

COLOR_WALL = (90, 90, 110)
COLOR_TIME_LOW = (235, 90, 90)

COLOR_BUTTON = (34, 38, 54)
COLOR_BUTTON_HOVER = (48, 54, 76)
COLOR_BUTTON_TEXT = (236, 238, 248)
COLOR_ACCENT = (120, 240, 150)
COLOR_ACCENT_DIM = (60, 130, 90)

# Заголовок окна
WINDOW_TITLE = "Змейка — курсовая работа"

# Путь к файлу базы данных и папке с уровнями
DB_PATH = "scores.db"
LEVELS_DIR = "levels"
ASSETS_DIR = "assets"
# Единственный пользовательский уровень: новое сохранение заменяет старое
LEVEL_FILE = "level.json"
