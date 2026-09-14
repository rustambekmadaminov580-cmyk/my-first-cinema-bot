"""
handlers/user.py — Oddiy foydalanuvchilar uchun handlerlar.

/start buyrug'i va kino ID orqali kino olish shu yerda amalga oshiriladi.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb

router = Router(name="user")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """/start buyrug'iga javob va foydalanuvchini bazaga saqlash."""
    # Har ehtimolga qarshi, boshqa FSM holatlarini tozalaymiz
    await state.clear()

    await db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    await message.answer(
        "🎬 Kino botga xush kelibsiz!\n\n"
        "Kino ID raqamini yuboring va kerakli kinoni oling."
    )


@router.message(Command("admin"))
async def redirect_note(message: Message) -> None:
    """
    Bu handler bu yerda ishlamaydi — /admin buyrug'i admin.py da
    to'g'ridan-to'g'ri ushlanadi. Bu funksiya faqat router tartibini
    aniq qilish uchun izoh sifatida qoldirilgan va hech qachon
    chaqirilmaydi (admin.py routeri birinchi ro'yxatdan o'tkaziladi).
    """
    pass


@router.message(F.text.regexp(r"^\d+$"))
async def handle_movie_id(message: Message, state: FSMContext) -> None:
    """Foydalanuvchi raqamli xabar (kino ID) yuborganda ishlaydi."""
    # Agar foydalanuvchi biror FSM holatida bo'lsa (masalan, admin
    # ID kiritayotgan bo'lsa), bu handler ishlamasligi kerak.
    current_state = await state.get_state()
    if current_state is not None:
        return

    movie_id = message.text.strip()
    movie = await db.get_movie_by_id(movie_id)

    if movie is not None:
        average, votes = await db.get_rating_stats("movie", movie_id)
        caption = (
            f"🎬 {movie['title']}\n🆔 ID: {movie['movie_id']}\n"
            f"⭐ Reyting: {average}/5 ({votes} ta ovoz)"
        )
        await message.answer_video(
            video=movie["file_id"],
            caption=caption,
            reply_markup=kb.rating_keyboard("movie", movie_id),
        )
        return

    serial = await db.get_serial_by_id(movie_id)
    if serial is not None:
        episodes = await db.get_serial_episodes(movie_id)
        if not episodes:
            await message.answer("❌ Bu serialda hali qismlar mavjud emas.")
            return

        average, votes = await db.get_rating_stats("serial", movie_id)
        await message.answer(
            f"📺 {serial['title']}\n🆔 ID: {serial['serial_id']}\n"
            f"⭐ Reyting: {average}/5 ({votes} ta ovoz)\n\nQismni tanlang:",
            reply_markup=kb.serial_episodes_keyboard(movie_id, episodes),
        )
        return

    await message.answer("❌ Bunday ID bilan kino yoki serial topilmadi.")


@router.callback_query(F.data.startswith("serial_episode:"))
async def send_serial_episode(callback: CallbackQuery) -> None:
    _, serial_id, episode_raw = callback.data.split(":", 2)
    try:
        episode_number = int(episode_raw)
    except ValueError:
        await callback.answer("❌ Qism ID noto'g'ri.", show_alert=True)
        return

    serial = await db.get_serial_by_id(serial_id)
    episode = await db.get_episode(serial_id, episode_number)
    if serial is None or episode is None:
        await callback.answer("❌ Bu qism topilmadi.", show_alert=True)
        return

    await callback.message.answer_video(
        video=episode["file_id"],
        caption=f"📺 {serial['title']}\n🎞 {episode_number}-qism",
        reply_markup=kb.rating_keyboard("serial", serial_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def rate_content(callback: CallbackQuery) -> None:
    _, content_type, content_id, rating_raw = callback.data.split(":", 3)
    if content_type not in {"movie", "serial"}:
        await callback.answer("❌ Noto'g'ri reyting turi.", show_alert=True)
        return

    try:
        rating = int(rating_raw)
    except ValueError:
        await callback.answer("❌ Reyting noto'g'ri.", show_alert=True)
        return

    if not 1 <= rating <= 5:
        await callback.answer("❌ Reyting 1 dan 5 gacha bo'lishi kerak.", show_alert=True)
        return

    if content_type == "movie":
        content = await db.get_movie_by_id(content_id)
    else:
        content = await db.get_serial_by_id(content_id)
    if content is None:
        await callback.answer("❌ Kontent topilmadi.", show_alert=True)
        return

    await db.save_rating(callback.from_user.id, content_type, content_id, rating)
    average, votes = await db.get_rating_stats(content_type, content_id)
    await callback.answer(f"✅ {rating}/5 baho saqlandi")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(f"⭐ Hozirgi reyting: {average}/5 ({votes} ta ovoz)")


@router.message(F.text)
async def handle_unknown_text(message: Message, state: FSMContext) -> None:
    """Boshqa har qanday matnli xabarlarga (agar FSM holatida bo'lmasa) javob."""
    current_state = await state.get_state()
    if current_state is not None:
        return

    await message.answer(
        "ℹ️ Kino olish uchun faqat kino ID raqamini yuboring.\n"
        "Masalan: 125"
    )
