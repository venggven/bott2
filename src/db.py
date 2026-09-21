# -*- coding: utf-8 -*-
"""Хранилище лидов на SQLite."""

import os
import time
from typing import Any, Optional

import aiosqlite

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY,
    username       TEXT,
    first_name     TEXT,
    started_at     REAL,
    score          INTEGER,
    zone           TEXT,
    answers        TEXT,
    finished_at    REAL,
    offer_shown_at REAL,
    pay_click_at   REAL,
    followup_at    REAL,
    paid_at        REAL
);
"""


async def init_db() -> None:
    path = config.DB_PATH
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def _execute(sql: str, params: tuple = ()) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(sql, params)
        await db.commit()


async def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name, started_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username = ?, first_name = ?
            """,
            (user_id, username, first_name, time.time(), username, first_name),
        )
        await db.commit()


async def save_result(user_id: int, score: int, zone: str, answers: str) -> None:
    await _execute(
        "UPDATE users SET score = ?, zone = ?, answers = ?, finished_at = ? WHERE user_id = ?",
        (score, zone, answers, time.time(), user_id),
    )


async def mark_offer_shown(user_id: int) -> None:
    await _execute(
        "UPDATE users SET offer_shown_at = COALESCE(offer_shown_at, ?) WHERE user_id = ?",
        (time.time(), user_id),
    )


async def mark_pay_click(user_id: int) -> None:
    await _execute(
        "UPDATE users SET pay_click_at = COALESCE(pay_click_at, ?) WHERE user_id = ?",
        (time.time(), user_id),
    )


async def mark_paid(user_id: int, paid: bool = True) -> None:
    await _execute(
        "UPDATE users SET paid_at = ? WHERE user_id = ?",
        (time.time() if paid else None, user_id),
    )


async def mark_followup_sent(user_id: int) -> None:
    await _execute(
        "UPDATE users SET followup_at = ? WHERE user_id = ?", (time.time(), user_id)
    )


async def get_user(user_id: int) -> Optional[dict[str, Any]]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
    return dict(row) if row else None


async def has_access(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user and user.get("paid_at"))


async def users_for_followup() -> list[dict[str, Any]]:
    """Прошли тест больше N часов назад, не нажимали оплату, дожим еще не получали."""
    deadline = time.time() - config.FOLLOWUP_DELAY_HOURS * 3600
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM users
            WHERE finished_at IS NOT NULL
              AND finished_at <= ?
              AND pay_click_at IS NULL
              AND paid_at IS NULL
              AND followup_at IS NULL
            """,
            (deadline,),
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def stats() -> dict[str, int]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute(
            """
            SELECT
                COUNT(*),
                COUNT(finished_at),
                SUM(zone = 'green'),
                SUM(zone = 'yellow'),
                SUM(zone = 'red'),
                COUNT(pay_click_at),
                COUNT(followup_at),
                COUNT(paid_at)
            FROM users
            """
        ) as cur:
            row = await cur.fetchone()
    keys = ["total", "finished", "green", "yellow", "red", "pay_clicks", "followups", "paid"]
    return {k: int(v or 0) for k, v in zip(keys, row)}
