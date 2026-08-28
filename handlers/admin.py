"""
handlers/admin.py — Admin uchun barcha funksiyalar.

Bu modul quyidagilarni o'z ichiga oladi:
  - /admin orqali parol so'rab, admin panelga kirish
  - Kino yuklash (FSM orqali bosqichma-bosqich)
  - Kinolar ro'yxati (pagination bilan)
  - Kino qidirish
  - Kino o'chirish (tasdiqlash bilan)
  - Statistika
  - Admin paneldan chiqish

MUHIM: Har bir admin funksiyasida foydalanuvchining ADMIN_ID ga
tengligi tekshiriladi. Bu tekshiruv shart, chunki parolni bilgan
har qanday odam emas, faqat .env da ko'rsatilgan ADMIN_ID ga ega
foydalanuvchi admin bo'la oladi.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from config import config
from states import AdminAuth, UploadMovie, DeleteMovie, SearchMovie

router = Router(name="admin")

# Parolni muvaffaqiyatli kiritgan va admin panelda "sessiya" ochiq
# bo'lgan foydalanuvchilarni saqlaydigan xotiradagi to'plam.
# Bot qayta ishga tushsa, bu tozalanadi — bu xavfsizlik uchun yaxshi,
# chunki har safar qayta parol so'raladi.
active_admin_sessions: set[int] = set()

MOVIES_PER_PAGE = 10


def is_admin_user(user_id: int) -> bool:
    """Foydalanuvchi .env da ko'rsatilgan ADMIN_ID ga tengligini tekshiradi."""
    return user_id == config.admin_id


def is_active_admin(user_id: int) -> bool:
    """Foydalanuvchi ADMIN_ID ga teng VA parolni to'g'ri kiritganini tekshiradi."""
    return is_admin_user(user_id) and user_id in active_admin_sessions


# ---------------------------------------------------------------------------
# ADMIN PANELGA KIRISH
# ---------------------------------------------------------------------------

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """/admin buyrug'i — faqat ADMIN_ID uchun parol so'raladi."""
    if not is_admin_user(message.from_user.id):
        # Begona foydalanuvchi /admin buyrug'idan foydalana olmaydi.
        await message.answer("❌ Bu buyruqdan foydalanish uchun ruxsatingiz yo'q.")
        return

    await state.set_state(AdminAuth.waiting_password)
    await message.answer("🔐 Admin panelga kirish uchun parolni kiriting:")


@router.message(AdminAuth.waiting_password, F.text)
async def process_admin_password(message: Message, state: FSMContext) -> None:
    """Kiritilgan parolni tekshiradi."""
    if not is_admin_user(message.from_user.id):
        await state.clear()
        return

    if message.text == config.admin_password:
        active_admin_sessions.add(message.from_user.id)
        await state.clear()
        await message.answer(
            "✅ Admin panelga xush kelibsiz!",
            reply_markup=kb.admin_menu_keyboard(),
        )
    else:
        await message.answer("❌ Parol noto'g'ri!")


# ---------------------------------------------------------------------------
# ADMIN PANELDAN CHIQISH
# ---------------------------------------------------------------------------

@router.message(F.text == kb.BTN_EXIT)
async def exit_admin_panel(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        return

    active_admin_sessions.discard(message.from_user.id)
    await state.clear()
    await message.answer(
        "🚪 Admin paneldan chiqdingiz.",
        reply_markup=kb.remove_keyboard(),
    )


# ---------------------------------------------------------------------------
# KINO YUKLASH
# ---------------------------------------------------------------------------

@router.message(F.text == kb.BTN_UPLOAD)
async def start_upload(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        return

    await state.set_state(UploadMovie.waiting_video)
    await message.answer("🎬 Kino videosini yuboring.")


@router.message(UploadMovie.waiting_video, F.video)
async def process_video(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        await state.clear()
        return

    await state.update_data(file_id=message.video.file_id)
    await state.set_state(UploadMovie.waiting_title)
    await message.answer("📝 Kino nomini kiriting:")


@router.message(UploadMovie.waiting_video)
async def process_video_invalid(message: Message) -> None:
    """Agar admin video o'rniga boshqa narsa yuborsa."""
    if not is_active_admin(message.from_user.id):
        return
    await message.answer("❌ Iltimos, video fayl yuboring.")


@router.message(UploadMovie.waiting_title, F.text)
async def process_title(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        await state.clear()
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(UploadMovie.waiting_movie_id)
    await message.answer("🆔 Kino uchun ID kiriting:")


@router.message(UploadMovie.waiting_movie_id, F.text)
async def process_movie_id(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        await state.clear()
        return

    movie_id = message.text.strip()

    if not movie_id.isdigit():
        await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    if await db.movie_exists(movie_id):
        await message.answer(
            "❌ Bu ID allaqachon mavjud. Boshqa ID kiriting:"
        )
        return

    data = await state.get_data()
    title = data["title"]
    file_id = data["file_id"]

    await db.add_movie(movie_id=movie_id, title=title, file_id=file_id)
    await state.clear()

    await message.answer(
        "✅ Kino muvaffaqiyatli saqlandi!\n\n"
        f"🎬 Nomi: {title}\n"
        f"🆔 ID: {movie_id}",
        reply_markup=kb.admin_menu_keyboard(),
    )


# ---------------------------------------------------------------------------
# KINOLAR RO'YXATI (pagination)
# ---------------------------------------------------------------------------

def _format_movies_page(movies: list) -> str:
    if not movies:
        return "📋 Hozircha kinolar mavjud emas."

    lines = [f"🆔 {m['movie_id']} — {m['title']}" for m in movies]
    return "\n".join(lines)


@router.message(F.text == kb.BTN_LIST)
async def show_movies_list(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        return

    await state.clear()
    total = await db.get_movies_count()
    movies = await db.get_movies_page(offset=0, limit=MOVIES_PER_PAGE)

    text = "📋 Kinolar ro'yxati:\n\n" + _format_movies_page(movies)
    markup = kb.pagination_keyboard(current_offset=0, limit=MOVIES_PER_PAGE, total=total)

    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("movies_page:"))
async def paginate_movies(callback: CallbackQuery) -> None:
    if not is_active_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    offset = int(callback.data.split(":", 1)[1])
    total = await db.get_movies_count()
    movies = await db.get_movies_page(offset=offset, limit=MOVIES_PER_PAGE)

    text = "📋 Kinolar ro'yxati:\n\n" + _format_movies_page(movies)
    markup = kb.pagination_keyboard(current_offset=offset, limit=MOVIES_PER_PAGE, total=total)

    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


# ---------------------------------------------------------------------------
# KINO QIDIRISH
# ---------------------------------------------------------------------------

@router.message(F.text == kb.BTN_SEARCH)
async def start_search(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        return

    await state.set_state(SearchMovie.waiting_query)
    await message.answer("🔎 Qidiruv uchun kino ID yoki nomini kiriting:")


@router.message(SearchMovie.waiting_query, F.text)
async def process_search(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        await state.clear()
        return

    query = message.text.strip()
    results = await db.search_movies(query)
    await state.clear()

    if not results:
        await message.answer(
            "❌ Hech narsa topilmadi.",
            reply_markup=kb.admin_menu_keyboard(),
        )
        return

    text = "🔎 Qidiruv natijalari:\n\n" + _format_movies_page(results)
    await message.answer(text, reply_markup=kb.admin_menu_keyboard())


# ---------------------------------------------------------------------------
# KINO O'CHIRISH
# ---------------------------------------------------------------------------

@router.message(F.text == kb.BTN_DELETE)
async def start_delete(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        return

    await state.set_state(DeleteMovie.waiting_movie_id)
    await message.answer("🆔 O'chiriladigan kino ID raqamini kiriting:")


@router.message(DeleteMovie.waiting_movie_id, F.text)
async def process_delete_id(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        await state.clear()
        return

    movie_id = message.text.strip()
    movie = await db.get_movie_by_id(movie_id)
    await state.clear()

    if movie is None:
        await message.answer(
            "❌ Bunday ID bilan kino topilmadi.",
            reply_markup=kb.admin_menu_keyboard(),
        )
        return

    await message.answer(
        f"⚠️ {movie_id} IDli kinoni o'chirishni tasdiqlaysizmi?",
        reply_markup=kb.confirm_delete_keyboard(movie_id),
    )


@router.callback_query(F.data.startswith("delete_confirm:"))
async def confirm_delete(callback: CallbackQuery) -> None:
    if not is_active_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    movie_id = callback.data.split(":", 1)[1]
    deleted = await db.delete_movie(movie_id)

    if deleted:
        await callback.message.edit_text(f"🗑 {movie_id} IDli kino o'chirildi.")
    else:
        await callback.message.edit_text("❌ Kino topilmadi yoki allaqachon o'chirilgan.")

    await callback.answer()


@router.callback_query(F.data == "delete_cancel")
async def cancel_delete(callback: CallbackQuery) -> None:
    if not is_active_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q.", show_alert=True)
        return

    await callback.message.edit_text("❌ O'chirish bekor qilindi.")
    await callback.answer()


# ---------------------------------------------------------------------------
# STATISTIKA
# ---------------------------------------------------------------------------

@router.message(F.text == kb.BTN_STATS)
async def show_stats(message: Message, state: FSMContext) -> None:
    if not is_active_admin(message.from_user.id):
        return

    await state.clear()
    users_count = await db.get_users_count()
    movies_count = await db.get_movies_count()

    await message.answer(
        "📊 BOT STATISTIKASI\n\n"
        f"👤 Foydalanuvchilar: {users_count}\n"
        f"🎬 Kinolar: {movies_count}\n"
        f"📥 Yuklangan kinolar: {movies_count}"
    )
