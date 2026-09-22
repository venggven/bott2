# -*- coding: utf-8 -*-
"""Мелочи, из которых складывается ощущение живого бота.

Ничего важного тут не происходит: полоски прогресса и эффект набора текста.
Если захочется откатить внешний вид — достаточно перестать вызывать эти функции.
"""

import asyncio
import logging

FILLED = "▓"
EMPTY = "░"

log = logging.getLogger(__name__)


def progress_bar(current: int, total: int, width: int = 5) -> str:
    """Полоска прохождения теста: ▓▓▓░░  3 из 5"""
    filled = max(0, min(width, round(width * current / total)))
    return f"{FILLED * filled}{EMPTY * (width - filled)}  {current} из {total}"


def battery_bar(percent: int, width: int = 10) -> str:
    """Заряд батарейки картинкой: 🔋 ▓▓▓▓▓▓▓▓░░ 80%"""
    filled = max(0, min(width, round(width * percent / 100)))
    return f"🔋 {FILLED * filled}{EMPTY * (width - filled)} {percent}%"


async def typing(target, seconds: float = 0.9) -> None:
    """Показать «печатает…» перед ответом.

    `target` — сообщение или чат, из которого берутся бот и чат.
    Эффект чисто визуальный: человек видит, что ему отвечают, а не выдают
    заготовку. Ошибки намеренно проглатываются — из-за украшения
    ничего ломаться не должно.
    """
    try:
        await target.bot.send_chat_action(target.chat.id, "typing")
    except Exception as e:
        log.debug("Не удалось показать «печатает»: %s", e)
    await asyncio.sleep(seconds)
