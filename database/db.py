"""database/db.py — Все операции с SQLite3."""
import csv, io, logging, os, sqlite3
from datetime import datetime
from typing import Any
from config import DB_PATH, CATEGORIES, STATUSES

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._create_tables()
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _create_tables(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    text          TEXT    NOT NULL,
                    user          TEXT    NOT NULL,
                    user_id       INTEGER NOT NULL,
                    chat_id       INTEGER NOT NULL DEFAULT 0,
                    assignee      TEXT    DEFAULT NULL,
                    status        TEXT    NOT NULL DEFAULT 'new',
                    category      TEXT    NOT NULL DEFAULT 'other',
                    deadline      TEXT    DEFAULT NULL,
                    reminder_sent INTEGER NOT NULL DEFAULT 0,
                    created_at    TEXT    NOT NULL,
                    updated_at    TEXT    NOT NULL
                )
            """)
            conn.commit()

    def _migrate(self) -> None:
        new_cols = {
            "chat_id":       "INTEGER NOT NULL DEFAULT 0",
            "deadline":      "TEXT DEFAULT NULL",
            "reminder_sent": "INTEGER NOT NULL DEFAULT 0",
        }
        with self._connect() as conn:
            existing = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
            for col, definition in new_cols.items():
                if col not in existing:
                    conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {definition}")
            conn.commit()

    def add_task(self, text, user, user_id, chat_id,
                 category="other", assignee=None, deadline=None) -> int:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO tasks (text,user,user_id,chat_id,assignee,status,category,"
                "deadline,reminder_sent,created_at,updated_at) VALUES (?,?,?,?,?,'new',?,?,0,?,?)",
                (text, user, user_id, chat_id, assignee, category, deadline, now, now),
            )
            conn.commit()
            return cur.lastrowid

    def get_tasks(self, status=None, category=None, assignee=None):
        q = "SELECT * FROM tasks WHERE 1=1"
        p: list[Any] = []
        if status:   q += " AND status=?";   p.append(status)
        if category: q += " AND category=?"; p.append(category)
        if assignee: q += " AND assignee=?"; p.append(assignee)
        q += " ORDER BY created_at DESC"
        with self._connect() as conn:
            return conn.execute(q, p).fetchall()

    def get_task_by_id(self, task_id: int):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()

    def update_status(self, task_id: int, status: str) -> bool:
        if status not in STATUSES:
            return False
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._connect() as conn:
            rows = conn.execute(
                "UPDATE tasks SET status=?, updated_at=? WHERE id=?", (status, now, task_id)
            ).rowcount
            conn.commit()
            return rows > 0

    def update_assignee(self, task_id: int, assignee) -> bool:
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        with self._connect() as conn:
            rows = conn.execute(
                "UPDATE tasks SET assignee=?, updated_at=? WHERE id=?", (assignee, now, task_id)
            ).rowcount
            conn.commit()
            return rows > 0

    def delete_task(self, task_id: int) -> bool:
        with self._connect() as conn:
            rows = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,)).rowcount
            conn.commit()
            return rows > 0

    def get_due_soon(self, window_start: str, window_end: str):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM tasks WHERE deadline>=? AND deadline<=? "
                "AND reminder_sent=0 AND status NOT IN ('done','cancelled')",
                (window_start, window_end),
            ).fetchall()

    def mark_reminder_sent(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE tasks SET reminder_sent=1 WHERE id=?", (task_id,))
            conn.commit()

    def get_stats(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
            ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def get_stats_by_category(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM tasks GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
        return [{"category": r["category"],
                 "label": CATEGORIES.get(r["category"], r["category"]),
                 "count": r["cnt"]} for r in rows]

    def export_csv(self, status=None, category=None) -> io.BytesIO:
        tasks = self.get_tasks(status=status, category=category)
        out = io.StringIO()
        w = csv.writer(out, quoting=csv.QUOTE_ALL)
        w.writerow(["ID","Задача","Автор","Ответственный","Статус","Категория","Дедлайн","Создано"])
        for t in tasks:
            w.writerow([
                t["id"], t["text"], f"@{t['user']}",
                f"@{t['assignee']}" if t["assignee"] else "—",
                STATUSES.get(t["status"], t["status"]),
                CATEGORIES.get(t["category"], t["category"]),
                t["deadline"] or "—", t["created_at"],
            ])
        out.seek(0)
        return io.BytesIO(out.read().encode("utf-8-sig"))
