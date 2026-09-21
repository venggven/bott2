# -*- coding: utf-8 -*-
"""Выбор хранилища лидов.

Один и тот же набор функций работает на двух движках:

* `STORAGE=sqlite` (по умолчанию) — файл `data/bot.db`, когда бот крутится
  на своем сервере или на компьютере;
* `STORAGE=ydb` — облачная база Yandex Database, когда бот живет
  в Yandex Cloud Functions, где файлы между запусками не сохраняются.

Остальной код бота про это не знает и всегда пишет `from src import storage as db`.
"""

import os

BACKEND = os.getenv("STORAGE", "sqlite").strip().lower()

if BACKEND == "ydb":
    from src import db_ydb as _impl
else:
    from src import db as _impl

init_db = _impl.init_db
upsert_user = _impl.upsert_user
save_result = _impl.save_result
mark_offer_shown = _impl.mark_offer_shown
mark_pay_click = _impl.mark_pay_click
mark_paid = _impl.mark_paid
mark_followup_sent = _impl.mark_followup_sent
get_user = _impl.get_user
has_access = _impl.has_access
users_for_followup = _impl.users_for_followup
stats = _impl.stats
