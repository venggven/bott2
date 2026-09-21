# -*- coding: utf-8 -*-
"""Мини-курс «Аптечка самопомощи»: выдача уроков и админские команды."""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

import config
from src import keyboards as kb, storage as db, texts

log = logging.getLogger(__name__)
router = Router()

CAPTION_LIMIT = 1000


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def lesson_by_number(number: int) -> dict | None:
    for lesson in texts.LESSONS:
        if lesson["n"] == number:
            return lesson
    return None


async def send_course_menu(bot: Bot, chat_id: int) -> None:
    await bot.send_message(chat_id, texts.COURSE_INTRO, reply_markup=kb.lessons_kb())


async def send_lesson(bot: Bot, chat_id: int, number: int) -> None:
    lesson = lesson_by_number(number)
    if not lesson:
        return

    video = config.LESSON_VIDEOS.get(number)
    text = lesson["text"]
    markup = kb.next_lesson_kb(number)

    if video:
        try:
            if len(text) <= CAPTION_LIMIT:
                await bot.send_video(chat_id, video, caption=text, reply_markup=markup)
            else:
                await bot.send_video(chat_id, video)
                await bot.send_message(chat_id, text, reply_markup=markup)
        except Exception as e:
            log.warning("Видео урока %s не отправилось (%s), шлю текстом", number, e)
            await bot.send_message(chat_id, text, reply_markup=markup)
    else:
        await bot.send_message(chat_id, text, reply_markup=markup)

    if number == len(texts.LESSONS):
        await bot.send_message(chat_id, texts.COURSE_OUTRO)


@router.message(Command("course"))
async def cmd_course(message: Message, bot: Bot) -> None:
    if not await db.has_access(message.from_user.id):
        await message.answer(texts.NO_ACCESS, reply_markup=kb.no_access_kb())
        return
    await send_course_menu(bot, message.chat.id)


@router.callback_query(F.data == "course:menu")
async def course_menu(call: CallbackQuery, bot: Bot) -> None:
    if not await db.has_access(call.from_user.id):
        await call.message.answer(texts.NO_ACCESS, reply_markup=kb.no_access_kb())
        await call.answer()
        return
    await call.message.answer(
        "<b>Аптечка самопомощи</b> — выбери урок:", reply_markup=kb.lessons_kb()
    )
    await call.answer()


@router.callback_query(F.data.startswith("course:lesson:"))
async def course_lesson(call: CallbackQuery, bot: Bot) -> None:
    if not await db.has_access(call.from_user.id):
        await call.message.answer(texts.NO_ACCESS, reply_markup=kb.no_access_kb())
        await call.answer()
        return
    number = int(call.data.rsplit(":", 1)[1])
    await send_lesson(bot, call.message.chat.id, number)
    await call.answer()


# ---------- Админские команды ----------


@router.message(Command("grant"))
async def cmd_grant(message: Message, command: CommandObject, bot: Bot) -> None:
    """Открыть доступ к урокам после подтверждения оплаты: /grant 123456789"""
    if not is_admin(message.from_user.id):
        return
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Формат: <code>/grant 123456789</code>")
        return

    user_id = int(arg)
    user = await db.get_user(user_id)
    if not user:
        await message.answer("Такого пользователя нет в базе бота.")
        return

    await db.mark_paid(user_id, True)
    try:
        await send_course_menu(bot, user_id)
        await message.answer(f"✅ Доступ открыт, уроки отправлены (id {user_id}).")
    except Exception as e:
        await message.answer(
            f"Доступ в базе открыт, но сообщение не доставлено: {e}\n"
            "Возможно, человек заблокировал бота."
        )


@router.message(Command("revoke"))
async def cmd_revoke(message: Message, command: CommandObject) -> None:
    """Закрыть доступ: /revoke 123456789"""
    if not is_admin(message.from_user.id):
        return
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Формат: <code>/revoke 123456789</code>")
        return
    await db.mark_paid(int(arg), False)
    await message.answer(f"Доступ закрыт (id {arg}).")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    s = await db.stats()
    await message.answer(
        "<b>Статистика воронки</b>\n\n"
        f"Запустили бота: {s['total']}\n"
        f"Прошли тест: {s['finished']}\n"
        f"🟢 Зеленая: {s['green']} · 🟡 Желтая: {s['yellow']} · 🔴 Красная: {s['red']}\n\n"
        f"Нажали оплату: {s['pay_clicks']}\n"
        f"Получили дожим: {s['followups']}\n"
        f"Оплатили (доступ открыт): {s['paid']}"
    )


@router.message(Command("whoami"))
async def cmd_whoami(message: Message) -> None:
    await message.answer(f"Твой Telegram ID: <code>{message.from_user.id}</code>")


# ---------- Любое другое сообщение ----------


@router.message(F.text)
async def fallback(message: Message, bot: Bot) -> None:
    await message.answer(texts.UNKNOWN_MESSAGE)
    if is_admin(message.from_user.id):
        return
    user = message.from_user
    username = f"@{user.username}" if user.username else "без юзернейма"
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✉️ Сообщение от <b>{user.full_name}</b> ({username}, "
                f"id <code>{user.id}</code>):\n\n{message.text}",
            )
        except Exception as e:
            log.warning("Не удалось переслать сообщение админу %s: %s", admin_id, e)
