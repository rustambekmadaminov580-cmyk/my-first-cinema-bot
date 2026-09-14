"""
keyboards.py — Bot uchun barcha reply va inline klaviaturalar.
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ---------------------------------------------------------------------------
# Reply keyboardlar
# ---------------------------------------------------------------------------

BTN_UPLOAD = "🎬 Kino yuklash"
BTN_UPLOAD_SERIAL = "📺 Serial qo'shish"
BTN_LIST = "📋 Kinolar ro'yxati"
BTN_SERIAL_LIST = "📺 Seriallar ro'yxati"
BTN_SEARCH = "🔎 Kino qidirish"
BTN_DELETE = "🗑 Kino o'chirish"
BTN_STATS = "📊 Statistika"
BTN_EXIT = "🚪 Admin paneldan chiqish"


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin panel uchun asosiy reply klaviatura."""
    keyboard = [
        [KeyboardButton(text=BTN_UPLOAD), KeyboardButton(text=BTN_UPLOAD_SERIAL)],
        [KeyboardButton(text=BTN_LIST), KeyboardButton(text=BTN_SERIAL_LIST)],
        [KeyboardButton(text=BTN_SEARCH)],
        [KeyboardButton(text=BTN_DELETE), KeyboardButton(text=BTN_STATS)],
        [KeyboardButton(text=BTN_EXIT)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardMarkup:
    """Reply klaviaturani olib tashlash uchun bo'sh klaviatura."""
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()


# ---------------------------------------------------------------------------
# Inline keyboardlar
# ---------------------------------------------------------------------------

def confirm_delete_keyboard(movie_id: str) -> InlineKeyboardMarkup:
    """Kino o'chirishni tasdiqlash uchun inline klaviatura."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"delete_confirm:{movie_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="delete_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def pagination_keyboard(current_offset: int, limit: int, total: int) -> InlineKeyboardMarkup | None:
    """Kinolar ro'yxati uchun sahifalash (pagination) klaviaturasi."""
    buttons = []
    row = []

    if current_offset > 0:
        prev_offset = max(0, current_offset - limit)
        row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"movies_page:{prev_offset}"))

    if current_offset + limit < total:
        next_offset = current_offset + limit
        row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"movies_page:{next_offset}"))

    if not row:
        return None

    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def serial_episodes_keyboard(serial_id: str, episodes: list) -> InlineKeyboardMarkup:
    """Foydalanuvchiga serial qismlarini tanlash klaviaturasi."""
    buttons = [
        [InlineKeyboardButton(
            text=f"{episode['episode_number']}-qism",
            callback_data=f"serial_episode:{serial_id}:{episode['episode_number']}",
        )]
        for episode in episodes
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rating_keyboard(content_type: str, content_id: str) -> InlineKeyboardMarkup:
    """Kino yoki serial uchun 1-5 yulduzli reyting klaviaturasi."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"{rating}⭐",
            callback_data=f"rate:{content_type}:{content_id}:{rating}",
        )
        for rating in range(1, 6)
    ]])
