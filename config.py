# -*- coding: utf-8 -*-
"""Настройки бота. Все значения берутся из .env — в коде ничего править не нужно."""

import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Telegram user ID админов через запятую — им приходят уведомления о заявках
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()
]

# Ссылка на оплату (ЮKassa / Продамус / Тинькофф и т.п.).
# Можно вставить плейсхолдер {user_id} — бот подставит ID пользователя,
# чтобы платеж было легко сопоставить с человеком.
PAYMENT_URL = os.getenv("PAYMENT_URL", "").strip()

# Юзернейм для личной связи (без @), используется в уведомлениях админу
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "").lstrip("@").strip()

# Показывать ли оффер мини-курса после теста.
# Пока продукта нет — воронка заканчивается результатом теста и мягким
# сообщением «напишу, когда будет готово». Чтобы включить продажу,
# поставь OFFER_ENABLED=true в настройках (в Railway — вкладка Variables).
OFFER_ENABLED = os.getenv("OFFER_ENABLED", "false").strip().lower() in (
    "1", "true", "yes", "on", "да",
)

# ---------- Связь с Telegram ----------
# Прокси для выхода к api.telegram.org. Нужен там, где прямого доступа нет
# (например, из России). Формат: http://127.0.0.1:10809 или
# socks5://логин:пароль@адрес:порт
# Если не задан — бот подхватит системный прокси Windows/Linux, а если
# и его нет, пойдет напрямую.
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY", "").strip() or (
    os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or ""
).strip()

DB_PATH = os.getenv("DB_PATH", "data/bot.db")

# ---------- Работа в Yandex Cloud (облачная функция) ----------
# STORAGE=ydb переключает хранилище лидов с файла на облачную базу.
# Обе строки ниже берутся со страницы базы в консоли Yandex Cloud.
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT", "").strip()
YDB_DATABASE = os.getenv("YDB_DATABASE", "").strip()

# Пароль, которым Telegram подписывает каждый запрос к функции.
# Нужен, чтобы по открытому адресу функции боту не могли писать посторонние.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()

# Через сколько часов после прохождения теста уходит дожим
FOLLOWUP_DELAY_HOURS = float(os.getenv("FOLLOWUP_DELAY_HOURS", "24"))

# Как часто фоновая задача проверяет, кому пора отправить дожим (секунды)
FOLLOWUP_CHECK_INTERVAL = int(os.getenv("FOLLOWUP_CHECK_INTERVAL", "300"))

# Видео уроков: file_id (появляется после первой отправки видео боту) или прямая ссылка.
# Если пусто — урок уходит текстом, без видео.
LESSON_VIDEOS = {
    1: os.getenv("LESSON_1_VIDEO", "").strip(),
    2: os.getenv("LESSON_2_VIDEO", "").strip(),
    3: os.getenv("LESSON_3_VIDEO", "").strip(),
    4: os.getenv("LESSON_4_VIDEO", "").strip(),
}


def payment_link(user_id: int) -> str:
    """Ссылка на оплату с подставленным ID пользователя."""
    if not PAYMENT_URL:
        return ""
    return PAYMENT_URL.replace("{user_id}", str(user_id))
