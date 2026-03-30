"""scheduler/reminders.py — Напоминания о дедлайнах через APScheduler."""
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from config import CATEGORIES, REMINDER_BEFORE_MINUTES
from database import Database

logger = logging.getLogger(__name__)
db = Database()


def check_deadlines(bot) -> None:
    """Проверяет задачи с приближающимся дедлайном и отправляет напоминание."""
    now    = datetime.now()
    target = now + timedelta(minutes=REMINDER_BEFORE_MINUTES)
    w_start = (target - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
    w_end   = (target + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")

    tasks = db.get_due_soon(w_start, w_end)
    for task in tasks:
        try:
            assignee_str = f"@{task['assignee']}" if task["assignee"] else "ответственный не назначен"
            text = (
                f"⏰ <b>Напоминание о дедлайне!</b>\n\n"
                f"<b>#{task['id']}</b>  {CATEGORIES.get(task['category'], task['category'])}\n"
                f"📝 {task['text']}\n\n"
                f"🎯 {assignee_str}\n"
                f"📅 Дедлайн: <b>{task['deadline']}</b>\n"
                f"⏳ Осталось ~<b>{REMINDER_BEFORE_MINUTES} мин</b>"
            )
            bot.send_message(task["chat_id"], text, parse_mode="HTML")
            db.mark_reminder_sent(task["id"])
            logger.info("Напоминание отправлено: задача #%d", task["id"])
        except Exception as e:
            logger.error("Ошибка напоминания #%d: %s", task["id"], e)


def start_scheduler(bot) -> BackgroundScheduler:
    """Запускает планировщик в фоновом потоке."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_deadlines,
        trigger="interval",
        seconds=60,
        kwargs={"bot": bot},
        id="deadline_reminder",
    )
    scheduler.start()
    logger.info("⏰ Планировщик запущен (напоминания за %d мин)", REMINDER_BEFORE_MINUTES)
    return scheduler
