"""
config.py — Bot konfiguratsiyasi.

Barcha maxfiy va muhim sozlamalar .env faylidan o'qiladi.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# .env faylini yuklaymiz
load_dotenv()


def _get_env(name: str, required: bool = True, default: str | None = None) -> str:
    """.env faylidan qiymatni o'qiydi, agar topilmasa xatolik beradi."""
    value = os.getenv(name, default)
    if required and not value:
        raise ValueError(
            f"'{name}' o'zgaruvchisi .env faylida topilmadi! "
            f".env.example faylini nusxalab, .env deb saqlang va qiymatlarni to'ldiring."
        )
    return value


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    admin_password: str
    db_path: str


def load_config() -> Config:
    bot_token = _get_env("BOT_TOKEN")
    admin_id_raw = _get_env("ADMIN_ID")
    admin_password = _get_env("ADMIN_PASSWORD")
    db_path = _get_env("DB_PATH", required=False, default="kino_bot.db")

    try:
        admin_id = int(admin_id_raw)
    except ValueError:
        raise ValueError("ADMIN_ID faqat raqamlardan iborat bo'lishi kerak (Telegram user ID).")

    return Config(
        bot_token=bot_token,
        admin_id=admin_id,
        admin_password=admin_password,
        db_path=db_path,
    )


config = load_config()
