# -*- coding: utf-8 -*-
"""Воронка: приветствие → 5 вопросов → результат → оффер → оплата."""

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

import config
from src import keyboards as kb, storage as db, texts

log = logging.getLogger(__name__)
router = Router()


def question_text(index: int) -> str:
    q = texts.QUESTIONS[index]
    return (
        f"<b>{q['title']}</b>  ({index + 1}/{len(texts.QUESTIONS)})\n\n{q['text']}"
    )


async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode=ParseMode.HTML)
        except Exception as e:  # админ не начал диалог с ботом / заблокировал
            log.warning("Не удалось уведомить админа %s: %s", admin_id, e)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    await db.upsert_user(user.id, user.username, user.first_name)
    await message.answer(texts.WELCOME, reply_markup=kb.start_kb())


def parse_progress(data: str) -> tuple[int, str] | None:
    """`q:<номер вопроса>:<ответы>` → (номер, ответы). None, если кнопка битая."""
    parts = data.split(":")
    if len(parts) != 3:
        return None
    try:
        index = int(parts[1])
    except ValueError:
        return None
    answers = parts[2]
    if index != len(answers) or not 0 <= index <= len(texts.QUESTIONS):
        return None
    for i, ch in enumerate(answers):
        if not ch.isdigit() or int(ch) >= len(texts.QUESTIONS[i]["options"]):
            return None
    return index, answers


def score_and_letters(answers: str) -> tuple[int, str]:
    score = 0
    letters = []
    for i, ch in enumerate(answers):
        letter, _label, points = texts.QUESTIONS[i]["options"][int(ch)]
        score += points
        letters.append(letter)
    return score, "".join(letters)


@router.callback_query(F.data.startswith("q:"))
async def quiz_step(call: CallbackQuery, bot: Bot) -> None:
    progress = parse_progress(call.data)
    if progress is None:
        await call.message.answer(texts.WELCOME, reply_markup=kb.start_kb())
        await call.answer()
        return

    index, answers = progress

    # Еще есть вопросы — показываем следующий
    if index < len(texts.QUESTIONS):
        await call.message.edit_text(
            question_text(index), reply_markup=kb.question_kb(index, answers)
        )
        await call.answer()
        return

    # Тест пройден
    score, letters = score_and_letters(answers)
    zone = texts.zone_by_score(score)
    user = call.from_user
    await db.save_result(user.id, score, zone["code"], letters)
    await call.message.edit_text(zone["text"], reply_markup=kb.result_kb(zone))
    await call.answer()

    username = f"@{user.username}" if user.username else "без юзернейма"
    await notify_admins(
        bot,
        f"🧪 Тест пройден: <b>{user.full_name}</b> ({username}, id {user.id})\n"
        f"Баллы: {score} → {zone['name']} · ответы: {letters}",
    )


@router.callback_query(F.data == "offer:show")
async def offer_show(call: CallbackQuery) -> None:
    await db.mark_offer_shown(call.from_user.id)
    await call.message.answer(texts.OFFER, reply_markup=kb.offer_kb())
    await call.answer()


@router.callback_query(F.data == "offer:pay")
async def offer_pay(call: CallbackQuery, bot: Bot) -> None:
    user = call.from_user
    await db.mark_pay_click(user.id)

    payment_kb = kb.payment_kb(user.id)
    if payment_kb:
        await call.message.answer(texts.PAY_INSTRUCTIONS, reply_markup=payment_kb)
    else:
        await call.message.answer(texts.PAY_FALLBACK)
    await call.answer()

    username = f"@{user.username}" if user.username else "без юзернейма"
    record = await db.get_user(user.id) or {}
    await notify_admins(
        bot,
        f"💳 Нажата оплата: <b>{user.full_name}</b> ({username}, id <code>{user.id}</code>)\n"
        f"Зона: {record.get('zone') or '—'} · баллы: {record.get('score') or '—'}\n"
        f"После оплаты открой доступ: <code>/grant {user.id}</code>",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Что я умею:\n"
        "/start — пройти тест на батарейку\n"
        "/course — твои уроки «Аптечки самопомощи»\n\n"
        "Если нужна живая помощь — просто напиши сюда сообщение."
    )
