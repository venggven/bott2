# -*- coding: utf-8 -*-
"""Точка входа. Запуск: python main.py"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.client.session.aiohttp import AiohttpSession  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from aiogram.types import BotCommand  # noqa: E402

import config  # noqa: E402
from src.course import router as course_router  # noqa: E402
from src.storage import init_db  # noqa: E402
from src.followup import followup_loop  # noqa: E402
from src.quiz import router as quiz_router  # noqa: E402

log = logging.getLogger(__name__)


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Пройти тест на батарейку"),
            BotCommand(command="course", description="Мои уроки"),
            BotCommand(command="help", description="Помощь"),
        ]
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if not config.BOT_TOKEN:
        sys.exit("BOT_TOKEN не задан. Скопируй .env.example в .env и впиши токен от @BotFather.")
    if not config.ADMIN_IDS:
        log.warning("ADMIN_IDS не заданы — уведомления о заявках приходить не будут.")
    if not config.PAYMENT_URL:
        log.warning("PAYMENT_URL не задан — бот попросит написать в чат вместо ссылки на оплату.")

    await init_db()

    if config.TELEGRAM_PROXY:
        log.info("Связь с Telegram через прокси %s", config.TELEGRAM_PROXY)
        session = AiohttpSession(proxy=config.TELEGRAM_PROXY)
    else:
        session = None

    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(quiz_router)
    dp.include_router(course_router)  # последним: в нем ловится любое сообщение

    await set_commands(bot)
    asyncio.create_task(followup_loop(bot))

    log.info("Бот запущен")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
