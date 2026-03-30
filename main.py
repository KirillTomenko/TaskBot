"""
main.py — Точка входа.

Запускает одновременно:
  1. Telegram-бот (telebot polling — в главном потоке)
  2. Планировщик напоминаний (APScheduler BackgroundScheduler — фоновый поток)
  3. Flask дашборд (фоновый поток) — при запуске с флагом --with-web

Запуск:
    python main.py            # только бот + планировщик
    python main.py --with-web # бот + планировщик + веб
"""

import logging
import sys
import threading

from config import WEB_HOST, WEB_PORT
from bot import bot
from scheduler.reminders import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_web() -> None:
    """Запускает Flask-дашборд в отдельном потоке."""
    from web.main import app
    logger.info("🌐 Дашборд запускается на http://%s:%d", WEB_HOST, WEB_PORT)
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    # Запускаем планировщик (фоновый поток)
    scheduler = start_scheduler(bot)

    # Опционально — запускаем веб-дашборд
    if "--with-web" in sys.argv:
        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()

    logger.info("✅ Бот запущен! Нажмите Ctrl+C для остановки.")

    try:
        # Используем обычный polling
        print("Запуск polling...")
        bot.remove_webhook()
        bot.infinity_polling(
            timeout=10,
            long_polling_timeout=20,
            allowed_updates=["message", "callback_query"],
        )
    except KeyboardInterrupt:
        logger.info("👋 Остановлено (Ctrl+C)")
    finally:
        scheduler.shutdown(wait=False)
