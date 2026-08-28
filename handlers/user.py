"""
handlers/user.py — Oddiy foydalanuvchilar uchun handlerlar.

/start buyrug'i va kino ID orqali kino olish shu yerda amalga oshiriladi.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db

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

    if movie is None:
        await message.answer("❌ Bunday ID bilan kino topilmadi.")
        return

    caption = f"🎬 {movie['title']}\n🆔 ID: {movie['movie_id']}"
    await message.answer_video(video=movie["file_id"], caption=caption)


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
