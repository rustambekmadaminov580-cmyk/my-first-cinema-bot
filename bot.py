"""
bot.py — Botning asosiy ishga tushirish fayli.

Ishga tushirish:
    python bot.py
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from config import config
from database import init_db
from handlers import admin, user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def start_health_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health server %s-portda ishga tushdi.", port)
    return runner


async def main() -> None:
    # Bazani ishga tushirishdan oldin tayyorlaymiz
    await init_db()
    logger.info("Baza tayyor.")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # MUHIM: admin routeri user routeridan OLDIN ro'yxatdan o'tkaziladi.
    # Shunda "🎬 Kino yuklash" kabi menyu tugmalari va /admin buyrug'i
    # avval admin handlerlariga tushadi, keyin umumiy matn handlerlariga
    # tushib ketmaydi.
    dp.include_router(admin.router)
    dp.include_router(user.router)

    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    health_runner = await start_health_server()
    try:
        await dp.start_polling(bot)
    finally:
        await health_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")
