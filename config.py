"""config.py — Конфигурация бота."""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")

def _parse_userlist(env_key: str) -> set[str]:
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return set()
    return {u.strip().lstrip("@").lower() for u in raw.split(",") if u.strip()}

ALLOWED_USERS: set[str] = _parse_userlist("ALLOWED_USERS")
ADMIN_USERS: set[str]   = _parse_userlist("ADMIN_USERS")

DB_PATH: str = os.getenv("DB_PATH", "data/tasks.db")

WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))

DASHBOARD_USER: str = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASS: str = os.getenv("DASHBOARD_PASS", "changeme")

REMINDER_BEFORE_MINUTES: int = int(os.getenv("REMINDER_BEFORE_MINUTES", "60"))

CATEGORIES: dict[str, str] = {
    "frontend": "🎨 Фронт-энд",
    "backend":  "⚙️ Бэк-энд",
    "database": "🗄️ База данных",
    "design":   "✏️ Дизайн",
    "devops":   "🚀 DevOps",
    "other":    "📌 Прочее",
}

STATUSES: dict[str, str] = {
    "new":         "🆕 Новое",
    "in_progress": "🔄 В работе",
    "done":        "✅ Выполнено",
    "cancelled":   "❌ Отменено",
}
