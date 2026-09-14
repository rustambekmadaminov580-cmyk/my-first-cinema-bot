"""
states.py — Admin va foydalanuvchi uchun FSM holatlari (states).
"""

from aiogram.fsm.state import State, StatesGroup


class AdminAuth(StatesGroup):
    """Admin panelga kirish uchun parol so'rash holati."""
    waiting_password = State()


class UploadMovie(StatesGroup):
    """Kino yuklash bosqichlari."""
    waiting_video = State()
    waiting_title = State()
    waiting_movie_id = State()


class UploadSerial(StatesGroup):
    """Serial va uning qismlarini yuklash bosqichlari."""
    waiting_title = State()
    waiting_serial_id = State()
    waiting_episode = State()


class DeleteMovie(StatesGroup):
    """Kino o'chirish bosqichi."""
    waiting_movie_id = State()


class SearchMovie(StatesGroup):
    """Kino qidirish bosqichi."""
    waiting_query = State()
