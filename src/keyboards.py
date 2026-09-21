# -*- coding: utf-8 -*-
"""Инлайн-клавиатуры воронки."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config
from src import texts


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.START_BUTTON, callback_data="q:0:")]
        ]
    )


def question_kb(index: int, answers: str) -> InlineKeyboardMarkup:
    """Кнопки А / Б / В для вопроса index (0-based).

    Прогресс теста лежит прямо в кнопке: `q:<следующий вопрос>:<ответы>`,
    где ответы — строка вида "021" (номера выбранных вариантов).
    Благодаря этому бот не хранит состояние в памяти и одинаково работает
    и на сервере, и в облачной функции, которая живет доли секунды.
    """
    rows = []
    for opt_index, (letter, label, _points) in enumerate(texts.QUESTIONS[index]["options"]):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{letter}. {label}",
                    callback_data=f"q:{index + 1}:{answers}{opt_index}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def result_kb(zone: dict) -> InlineKeyboardMarkup:
    """Кнопка под результатом теста — своя формулировка для каждой зоны."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=zone["button"], callback_data="offer:show")]
        ]
    )


def offer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.OFFER_BUTTON, callback_data="offer:pay")]
        ]
    )


def followup_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.FOLLOWUP_BUTTON, callback_data="offer:pay")]
        ]
    )


def payment_kb(user_id: int) -> InlineKeyboardMarkup | None:
    """Кнопка-ссылка на страницу оплаты. None, если ссылка еще не подключена."""
    url = config.payment_link(user_id)
    if not url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=texts.PAY_LINK_BUTTON, url=url)]]
    )


def lessons_kb(current: int | None = None) -> InlineKeyboardMarkup:
    """Меню уроков. current — номер открытого урока (1-4), чтобы отметить его."""
    rows = []
    for lesson in texts.LESSONS:
        mark = "▶️ " if lesson["n"] == current else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark}Урок {lesson['n']}. {lesson['title']}",
                    callback_data=f"course:lesson:{lesson['n']}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def next_lesson_kb(current: int) -> InlineKeyboardMarkup:
    rows = []
    if current < len(texts.LESSONS):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"Следующий урок ({current + 1}/{len(texts.LESSONS)})",
                    callback_data=f"course:lesson:{current + 1}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="Все уроки", callback_data="course:menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def no_access_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.OFFER_BUTTON, callback_data="offer:pay")]
        ]
    )
