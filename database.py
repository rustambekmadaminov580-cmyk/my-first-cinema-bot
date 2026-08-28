"""
database.py — SQLite bilan ishlash uchun barcha funksiyalar.

aiosqlite orqali asinxron so'rovlar amalga oshiriladi.
Barcha querylar parametrli (parametrized) bo'lib, SQL injectiondan himoyalangan.
"""

import aiosqlite
from datetime import datetime

from config import config

DB_PATH = config.db_path


async def init_db() -> None:
    """Bazani va kerakli jadvallarni yaratadi (agar mavjud bo'lmasa)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                file_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.commit()


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------

async def add_user(telegram_id: int, username: str | None, first_name: str | None) -> None:
    """Yangi foydalanuvchini bazaga qo'shadi, agar u allaqachon mavjud bo'lmasa."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        existing = await cursor.fetchone()
        if existing is None:
            await db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, datetime.utcnow().isoformat()),
            )
            await db.commit()


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0


# ---------------------------------------------------------------------------
# MOVIES
# ---------------------------------------------------------------------------

async def movie_exists(movie_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM movies WHERE movie_id = ?", (movie_id,)
        )
        row = await cursor.fetchone()
        return row is not None


async def add_movie(movie_id: str, title: str, file_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO movies (movie_id, title, file_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (movie_id, title, file_id, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_movie_by_id(movie_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM movies WHERE movie_id = ?", (movie_id,)
        )
        return await cursor.fetchone()


async def delete_movie(movie_id: str) -> bool:
    """Kinoni o'chiradi. Muvaffaqiyatli bo'lsa True qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM movies WHERE movie_id = ?", (movie_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_movies_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM movies")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_movies_page(offset: int, limit: int) -> list[aiosqlite.Row]:
    """Kinolar ro'yxatini pagination bilan qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM movies
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return await cursor.fetchall()


async def search_movies(query: str) -> list[aiosqlite.Row]:
    """ID yoki nom bo'yicha kino qidiradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        like_query = f"%{query}%"
        cursor = await db.execute(
            """
            SELECT * FROM movies
            WHERE movie_id = ? OR title LIKE ?
            ORDER BY id DESC
            """,
            (query, like_query),
        )
        return await cursor.fetchall()
