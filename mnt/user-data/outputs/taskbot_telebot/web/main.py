"""web/main.py — Flask веб-дашборд."""
import functools
from flask import Flask, render_template, request, Response
from config import CATEGORIES, DASHBOARD_PASS, DASHBOARD_USER, STATUSES
from database import Database

app = Flask(__name__, template_folder="templates")
db  = Database()


def require_auth(f):
    """Декоратор HTTP Basic Auth."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != DASHBOARD_USER or auth.password != DASHBOARD_PASS:
            return Response(
                "Требуется авторизация", 401,
                {"WWW-Authenticate": 'Basic realm="TaskBot"'}
            )
        return f(*args, **kwargs)
    return decorated


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats")
@require_auth
def api_stats():
    stats = db.get_stats()
    return {"total": sum(stats.values()),
            "by_status": {k: stats.get(k, 0) for k in STATUSES}}


@app.get("/")
@require_auth
def dashboard():
    status_filter   = request.args.get("status")
    category_filter = request.args.get("category")
    search          = request.args.get("search", "")

    tasks = db.get_tasks(
        status=status_filter if status_filter not in (None, "all") else None,
        category=category_filter if category_filter not in (None, "all") else None,
    )
    if search:
        q = search.lower()
        tasks = [t for t in tasks if q in t["text"].lower()
                 or q in (t["user"] or "").lower()]

    stats = db.get_stats()
    return render_template("index.html",
        tasks=tasks, stats=stats, total=sum(stats.values()),
        statuses=STATUSES, categories=CATEGORIES,
        status_filter=status_filter or "all",
        category_filter=category_filter or "all",
        search=search,
    )
