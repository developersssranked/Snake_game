"""Локальная база данных результатов на SQLite.

Класс `ScoreDatabase` инкапсулирует всю работу с БД: создание таблицы,
сохранение результата и выборку рейтинга. SQLite входит в стандартную
библиотеку Python — внешних зависимостей не нужно.
"""

import sqlite3
from datetime import datetime

from . import settings


class ScoreDatabase:
    """Обёртка над таблицей результатов."""

    def __init__(self, db_path=settings.DB_PATH):
        self._db_path = db_path
        self._init_table()

    def _connect(self):
        return sqlite3.connect(self._db_path)

    def _init_table(self):
        """Создать таблицу результатов, если её ещё нет."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scores (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    player     TEXT    NOT NULL,
                    score      INTEGER NOT NULL,
                    level      TEXT    NOT NULL,
                    length     INTEGER NOT NULL,
                    played_at  TEXT    NOT NULL
                )
                """
            )

    def add_score(self, player, score, level, length):
        """Сохранить результат партии."""
        played_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO scores (player, score, level, length, played_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (player, int(score), level, int(length), played_at),
            )

    def top_scores(self, limit=10):
        """Вернуть лучшие результаты в виде списка кортежей."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT player, score, level, length, played_at "
                "FROM scores ORDER BY score DESC, id ASC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()
