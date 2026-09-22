# -*- coding: utf-8 -*-
"""Дожим через 24 часа тем, кто прошел тест, но не нажал оплату."""

import asyncio
import logging

from aiogram import Bot

import config
from src import keyboards as kb, storage as db, texts

log = logging.getLogger(__name__)


async def send_followups(bot: Bot) -> int:
    if not config.OFFER_ENABLED:
        # Дожим зовет купить — пока продукта нет, он не нужен
        return 0
    sent = 0
    for user in await db.users_for_followup():
        user_id = user["user_id"]
        try:
            await bot.send_message(user_id, texts.FOLLOWUP, reply_markup=kb.followup_kb())
            sent += 1
        except Exception as e:
            # Заблокировал бота или удалил аккаунт — помечаем, чтобы не долбиться
            log.info("Дожим не доставлен (id %s): %s", user_id, e)
        await db.mark_followup_sent(user_id)
        await asyncio.sleep(0.05)  # держимся в лимитах Telegram
    if sent:
        log.info("Отправлено дожимов: %s", sent)
    return sent


async def followup_loop(bot: Bot) -> None:
    while True:
        try:
            await send_followups(bot)
        except Exception as e:
            log.exception("Ошибка в цикле дожима: %s", e)
        await asyncio.sleep(config.FOLLOWUP_CHECK_INTERVAL)
