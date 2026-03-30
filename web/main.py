"""web/main.py — Flask-дашборд для TaskBot."""
import functools
from flask import Flask, render_template, request, Response, jsonify
from config import DASHBOARD_USER, DASHBOARD_PASS, CATEGORIES, STATUSES
from database.db import Database

app = Flask(__name__, template_folder="templates")
db = Database()


# ── Basic Auth ────────────────────────────────────────────────────

def check_auth(username, password):
    return username == DASHBOARD_USER and password == DASHBOARD_PASS

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Требуется авторизация", 401,
                {"WWW-Authenticate": 'Basic realm="TaskBot Dashboard"'}
            )
        return f(*args, **kwargs)
    return decorated


# ── Маршруты ──────────────────────────────────────────────────────

@app.route("/")
@require_auth
def index():
    status   = request.args.get("status")   or None
    category = request.args.get("category") or None
    search   = request.args.get("search",  "").strip()

    tasks = db.get_tasks(status=status, category=category)

    # Поиск по тексту
    if search:
        sl = search.lower()
        tasks = [t for t in tasks if sl in t["text"].lower()
                 or sl in (t["assignee"] or "").lower()
                 or sl in t["user"].lower()]

    stats = db.get_stats()
    total = sum(stats.values())

    return render_template(
        "index.html",
        tasks=tasks,
        stats=stats,
        total=total,
        categories=CATEGORIES,
        statuses=STATUSES,
        sel_status=status or "",
        sel_category=category or "",
        search=search,
    )


@app.route("/api/status", methods=["POST"])
@require_auth
def api_set_status():
    data    = request.get_json(silent=True) or {}
    task_id = data.get("task_id")
    status  = data.get("status")
    if not task_id or not status:
        return jsonify({"ok": False, "error": "missing params"}), 400
    ok = db.update_status(int(task_id), status)
    return jsonify({"ok": ok})


@app.route("/api/delete", methods=["POST"])
@require_auth
def api_delete():
    data    = request.get_json(silent=True) or {}
    task_id = data.get("task_id")
    if not task_id:
        return jsonify({"ok": False, "error": "missing task_id"}), 400
    ok = db.delete_task(int(task_id))
    return jsonify({"ok": ok})