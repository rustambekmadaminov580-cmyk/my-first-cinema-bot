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
from aiohttp import ClientSession, ClientTimeout, web

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


async def keep_server_awake() -> None:
    service_url = os.getenv("RENDER_EXTERNAL_URL")
    if not service_url:
        logger.info("RENDER_EXTERNAL_URL topilmadi, keep-alive o'chirildi.")
        return

    health_url = f"{service_url.rstrip('/')}/health"
    timeout = ClientTimeout(total=15)
    async with ClientSession(timeout=timeout) as session:
        while True:
            try:
                async with session.get(health_url) as response:
                    logger.info("Keep-alive so'rovi: HTTP %s", response.status)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.warning("Keep-alive so'rovi muvaffaqiyatsiz: %s", error)
            await asyncio.sleep(120)


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
    keep_alive_task = asyncio.create_task(keep_server_awake())
    try:
        await dp.start_polling(bot)
    finally:
        keep_alive_task.cancel()
        await asyncio.gather(keep_alive_task, return_exceptions=True)
        await health_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")
