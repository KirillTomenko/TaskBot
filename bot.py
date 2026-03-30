"""bot.py — Telegram-бот на pyTelegramBotAPI v2.1 (исправлен)."""

import logging
from datetime import datetime

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile

from config import ADMIN_USERS, ALLOWED_USERS, BOT_TOKEN, CATEGORIES, STATUSES
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Создаём бота БЕЗ parse_mode в конструкторе — передаём явно в каждый вызов
import telebot.util
telebot.util.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(BOT_TOKEN)
db  = Database()

HTML = "HTML"   # константа для parse_mode

# ── FSM ───────────────────────────────────────────────────────────
user_states: dict[int, dict] = {}

S_TEXT      = "text"
S_CATEGORY  = "category"
S_ASSIGNEE  = "assignee"
S_DEADLINE  = "deadline"
S_SETASSIGN = "set_assignee_btn"


# ══════════════════════════════════════════════════════════════════
# Хелперы
# ══════════════════════════════════════════════════════════════════

def allowed(user) -> bool:
    if not ALLOWED_USERS:
        return True
    return (user.username or "").lower() in ALLOWED_USERS or str(user.id) in ALLOWED_USERS

def admin(user) -> bool:
    return (user.username or "").lower() in ADMIN_USERS

def send(chat_id, text, **kw):
    """Обёртка над send_message с parse_mode=HTML по умолчанию."""
    kw.setdefault("parse_mode", HTML)
    return bot.send_message(chat_id, text, **kw)

def edit_text(chat_id, msg_id, text, **kw):
    """Обёртка над edit_message_text с parse_mode=HTML."""
    kw.setdefault("parse_mode", HTML)
    try:
        return bot.edit_message_text(text, chat_id, msg_id, **kw)
    except Exception as e:
        logger.warning("edit_message_text failed: %s", e)

def edit_kb(chat_id, msg_id, markup):
    try:
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=markup)
    except Exception as e:
        logger.warning("edit_message_reply_markup failed: %s", e)

def ack(call, text="", alert=False):
    """Всегда отвечаем на callback — иначе кнопка зависает."""
    try:
        bot.answer_callback_query(call.id, text, show_alert=alert)
    except Exception as e:
        logger.warning("answer_callback_query failed: %s", e)


# ══════════════════════════════════════════════════════════════════
# Клавиатуры
# ══════════════════════════════════════════════════════════════════

def kb_categories():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(label, callback_data=f"cat:{key}")
             for key, label in CATEGORIES.items()])
    return kb

def kb_filter_status():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📋 Все задачи", callback_data="filter:all"))
    kb.add(*[InlineKeyboardButton(label, callback_data=f"filter:{key}")
             for key, label in STATUSES.items()])
    return kb

def kb_filter_csv():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📋 Все категории", callback_data="csv:all"))
    kb.add(*[InlineKeyboardButton(label, callback_data=f"csv:{key}")
             for key, label in CATEGORIES.items()])
    return kb

def kb_task_actions(task_id: int, is_admin: bool = False):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🔄 Изменить статус",     callback_data=f"setstatus:{task_id}"),
        InlineKeyboardButton("👤 Назначить ответств.", callback_data=f"setassignee:{task_id}"),
    )
    if is_admin:
        kb.add(InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{task_id}"))
    return kb

def kb_statuses(task_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(label, callback_data=f"status:{task_id}:{key}")
             for key, label in STATUSES.items()])
    kb.add(InlineKeyboardButton("↩️ Отмена", callback_data=f"cancelaction:{task_id}"))
    return kb

def kb_confirm_delete(task_id: int):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirmdelete:{task_id}"),
        InlineKeyboardButton("❌ Отмена",      callback_data=f"cancelaction:{task_id}"),
    )
    return kb


# ══════════════════════════════════════════════════════════════════
# Форматирование
# ══════════════════════════════════════════════════════════════════

def fmt_task(task) -> str:
    status_lbl   = STATUSES.get(task["status"],   task["status"])
    category_lbl = CATEGORIES.get(task["category"], task["category"])
    assignee = f"@{task['assignee']}" if task["assignee"] else "—"
    try:
        created = datetime.fromisoformat(task["created_at"]).strftime("%d.%m.%Y %H:%M")
    except Exception:
        created = task["created_at"]

    dl = ""
    if task["deadline"]:
        try:
            d     = datetime.fromisoformat(task["deadline"])
            hours = int((d - datetime.now()).total_seconds() // 3600)
            if hours < 0:
                dl = f"\n⚠️ Дедлайн: <b>{d.strftime('%d.%m.%Y %H:%M')}</b> (просрочено!)"
            elif hours < 24:
                dl = f"\n⏰ Дедлайн: <b>{d.strftime('%d.%m.%Y %H:%M')}</b> (через {hours}ч)"
            else:
                dl = f"\n📅 Дедлайн: <b>{d.strftime('%d.%m.%Y %H:%M')}</b>"
        except Exception:
            dl = f"\n📅 Дедлайн: {task['deadline']}"

    return (
        f"<b>#{task['id']}</b>  {status_lbl}  <i>{category_lbl}</i>\n"
        f"📝 {task['text']}\n"
        f"👤 @{task['user']}  |  🎯 {assignee}{dl}\n"
        f"🕒 {created}"
    )

def parse_deadline(text: str):
    text = text.strip()
    if text in ("-", "нет", "skip", ""):
        return None
    for fmt in ["%d.%m.%Y %H:%M", "%d.%m.%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return None


# ══════════════════════════════════════════════════════════════════
# КОМАНДЫ
# ══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start", "Start"])
def cmd_start(m):
    user_states.pop(m.from_user.id, None)
    if not allowed(m.from_user):
        send(m.chat.id, "🔒 <b>Доступ закрыт.</b>")
        return
    send(m.chat.id,
        f"👋 Привет, <b>{m.from_user.first_name or 'коллега'}</b>!\n\n"
        "Я <b>TaskBot</b> — командный менеджер задач.\n\n"
        "📋 <b>Команды:</b>\n"
        "  /add — ➕ Добавить задачу\n"
        "  /list — 📄 Просмотреть задачи\n"
        "  /list_csv — 📥 Выгрузить в CSV\n"
        "  /stats — 📊 Статистика\n"
        "  /cancel — ❌ Отменить диалог\n"
        "  /help — ❓ Справка"
    )

@bot.message_handler(commands=["cancel"])
def cmd_cancel(m):
    if user_states.pop(m.from_user.id, None):
        send(m.chat.id, "❌ Действие отменено.")
    else:
        send(m.chat.id, "Нет активного диалога.")

@bot.message_handler(commands=["add"])
def cmd_add(m):
    if not allowed(m.from_user):
        send(m.chat.id, "🔒 Доступ закрыт.")
        return
    user_states[m.from_user.id] = {"state": S_TEXT, "data": {}}
    send(m.chat.id,
        "✏️ <b>Новая задача — шаг 1/4</b>\n\n"
        "Введите текст задачи:\n"
        "<i>Для отмены: /cancel</i>"
    )

@bot.message_handler(commands=["list"])
def cmd_list(m):
    if not allowed(m.from_user):
        return
    send(m.chat.id, "🔍 <b>Фильтр задач</b>\n\nВыберите статус:",
         reply_markup=kb_filter_status())

@bot.message_handler(commands=["list_csv"])
def cmd_list_csv(m):
    if not allowed(m.from_user):
        return
    send(m.chat.id, "📥 <b>Экспорт в CSV</b>\n\nВыберите категорию:",
         reply_markup=kb_filter_csv())

@bot.message_handler(commands=["stats"])
def cmd_stats(m):
    if not allowed(m.from_user):
        return
    stats = db.get_stats()
    total = sum(stats.values())
    if total == 0:
        send(m.chat.id, "📭 Задач нет. Добавьте через /add")
        return
    lines = [f"📊 <b>Статистика</b>  (всего: {total})\n{'─'*26}"]
    for key, label in STATUSES.items():
        n = stats.get(key, 0)
        lines.append(f"{label}: <b>{n}</b>  <code>{'█'*min(n,10)}{'░'*max(0,10-n)}</code>")
    for item in db.get_stats_by_category():
        lines.append(f"  {item['label']}: <b>{item['count']}</b>")
    send(m.chat.id, "\n".join(lines))

@bot.message_handler(commands=["help"])
def cmd_help(m):
    send(m.chat.id,
        "📖 <b>Справка TaskBot</b>\n\n"
        "<b>Диалог /add (4 шага):</b>\n"
        "  1. Текст задачи\n"
        "  2. Категория — нажмите кнопку\n"
        "  3. Ответственный (username или -)\n"
        "  4. Дедлайн (25.12.2025 15:00 или -)\n\n"
        "/cancel — отменить в любой момент"
    )


# ══════════════════════════════════════════════════════════════════
# FSM — текстовые шаги
# ══════════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: (
    m.from_user.id in user_states
    and not m.text.startswith("/")
    and user_states[m.from_user.id]["state"] != S_CATEGORY
))
def fsm_text(m):
    uid   = m.from_user.id
    state = user_states[uid]["state"]
    data  = user_states[uid]["data"]

    # Шаг 1 — текст задачи
    if state == S_TEXT:
        text = m.text.strip()
        if len(text) < 3:
            send(m.chat.id, "⚠️ Слишком коротко. Введите текст задачи:")
            return
        data["text"] = text
        user_states[uid]["state"] = S_CATEGORY
        send(m.chat.id, "📂 <b>Шаг 2/4</b> — Выберите категорию:",
             reply_markup=kb_categories())

    # Шаг 3 — ответственный
    elif state == S_ASSIGNEE:
        raw = m.text.strip().lstrip("@")
        data["assignee"] = None if raw in ("-", "") else raw
        user_states[uid]["state"] = S_DEADLINE
        send(m.chat.id,
            "📅 <b>Шаг 4/4</b> — Укажите дедлайн:\n\n"
            "Формат: <code>25.12.2025 15:00</code>\n"
            "Или <code>-</code> чтобы пропустить."
        )

    # Шаг 4 — дедлайн → сохраняем
    elif state == S_DEADLINE:
        raw      = m.text.strip()
        deadline = parse_deadline(raw)
        if raw not in ("-", "нет", "skip", "") and deadline is None:
            send(m.chat.id, "⚠️ Формат: <code>DD.MM.YYYY HH:MM</code> или <code>-</code>:")
            return

        username = m.from_user.username or m.from_user.first_name
        try:
            task_id = db.add_task(
                text=data["text"],
                user=username,
                user_id=m.from_user.id,
                chat_id=m.chat.id,
                category=data.get("category", "other"),
                assignee=data.get("assignee"),
                deadline=deadline,
            )
            user_states.pop(uid)
            dl_str = f"\n📅 Дедлайн: <b>{deadline}</b>" if deadline else ""
            asgn   = f"@{data.get('assignee')}" if data.get("assignee") else "не назначен"
            send(m.chat.id,
                f"✅ <b>Задача #{task_id} сохранена!</b>\n\n"
                f"📝 {data['text']}\n"
                f"📂 {CATEGORIES.get(data.get('category','other'), '')}\n"
                f"🎯 {asgn}{dl_str}\n\n"
                "Просмотр: /list"
            )
            logger.info("Задача #%d сохранена (@%s)", task_id, username)
        except Exception as e:
            user_states.pop(uid, None)
            logger.error("Ошибка add_task: %s", e)
            send(m.chat.id, f"❌ Ошибка сохранения: <code>{e}</code>\nПопробуйте /add снова.")

    # Смена ответственного через кнопку
    elif state == S_SETASSIGN:
        task_id  = data.get("task_id")
        raw      = m.text.strip().lstrip("@")
        assignee = None if raw in ("-", "") else raw
        db.update_assignee(task_id, assignee)
        user_states.pop(uid)
        result = f"@{assignee}" if assignee else "снят"
        send(m.chat.id, f"✅ Ответственный задачи <b>#{task_id}</b>: <b>{result}</b>")


# ══════════════════════════════════════════════════════════════════
# CALLBACK-ОБРАБОТЧИКИ — по одному на каждый тип
# ══════════════════════════════════════════════════════════════════

# ── Выбор категории (шаг 2) ───────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def cb_category(call):
    logger.info(f"cb_category вызван с данными: {call.data}")
    ack(call)   # ПЕРВЫМ делом отвечаем — кнопка разблокируется мгновенно
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id

    if uid not in user_states or user_states[uid]["state"] != S_CATEGORY:
        send(cid, "⚠️ Начните заново: /add")
        return

    category = call.data.split(":", 1)[1]
    user_states[uid]["data"]["category"] = category
    user_states[uid]["state"] = S_ASSIGNEE

    logger.info("Категория выбрана: %s для uid=%d", category, uid)

    edit_text(cid, mid,
        f"✅ Категория: <b>{CATEGORIES.get(category, category)}</b>\n\n"
        "👤 <b>Шаг 3/4</b> — Введите username ответственного (без @)\n"
        "или <code>-</code> чтобы пропустить:"
    )


# ── Фильтр /list ─────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("filter:"))
def cb_filter(call):
    ack(call)
    status_key = call.data.split(":", 1)[1]
    status     = None if status_key == "all" else status_key
    cid, mid   = call.message.chat.id, call.message.message_id

    edit_kb(cid, mid, None)
    tasks = db.get_tasks(status=status)
    if not tasks:
        send(cid, "📭 Задач не найдено. Добавьте через /add")
        return

    label = STATUSES.get(status_key, "Все задачи") if status else "Все задачи"
    send(cid, f"📋 <b>{label}</b> — найдено: {len(tasks)}\n{'─'*30}")
    is_adm = admin(call.from_user)
    for task in tasks:
        send(cid, fmt_task(task), reply_markup=kb_task_actions(task["id"], is_adm))


# ── CSV-экспорт ───────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("csv:"))
def cb_csv(call):
    ack(call, "⏳ Генерирую…")
    cat_key  = call.data.split(":", 1)[1]
    category = None if cat_key == "all" else cat_key
    cid, mid = call.message.chat.id, call.message.message_id

    edit_kb(cid, mid, None)
    tasks = db.get_tasks(category=category)
    if not tasks:
        send(cid, "📭 Нет задач для выгрузки.")
        return
    buf      = db.export_csv(category=category)
    filename = f"tasks_{cat_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    bot.send_document(cid, InputFile(buf, file_name=filename),
        caption=(
            f"📊 <b>Выгрузка</b>\n"
            f"Категория: <b>{CATEGORIES.get(cat_key,'Все')}</b>\n"
            f"Записей: <b>{len(tasks)}</b>"
        ),
        parse_mode=HTML,
    )


# ── Меню смены статуса ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("setstatus:"))
def cb_setstatus(call):
    ack(call)
    task_id = int(call.data.split(":")[1])
    if not db.get_task_by_id(task_id):
        send(call.message.chat.id, "❌ Задача не найдена")
        return
    edit_kb(call.message.chat.id, call.message.message_id, kb_statuses(task_id))


# ── Применить статус ──────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("status:"))
def cb_status(call):
    parts   = call.data.split(":")
    task_id = int(parts[1])
    new_st  = parts[2]
    db.update_status(task_id, new_st)
    ack(call, STATUSES.get(new_st, new_st))
    task = db.get_task_by_id(task_id)
    edit_text(call.message.chat.id, call.message.message_id,
              fmt_task(task), reply_markup=kb_task_actions(task_id, admin(call.from_user)))


# ── Назначить ответственного ──────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("setassignee:"))
def cb_setassignee(call):
    ack(call)
    task_id = int(call.data.split(":")[1])
    user_states[call.from_user.id] = {"state": S_SETASSIGN, "data": {"task_id": task_id}}
    send(call.message.chat.id,
        f"👤 Username ответственного для задачи <b>#{task_id}</b>\n"
        "(без @, или <code>-</code> чтобы снять):"
    )


# ── Удалить — подтверждение ───────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("delete:"))
def cb_delete(call):
    if not admin(call.from_user):
        ack(call, "🔒 Только администратор", alert=True)
        return
    ack(call)
    task_id = int(call.data.split(":")[1])
    edit_kb(call.message.chat.id, call.message.message_id, kb_confirm_delete(task_id))


# ── Подтвердить удаление ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("confirmdelete:"))
def cb_confirmdelete(call):
    if not admin(call.from_user):
        ack(call, "🔒 Нет прав", alert=True)
        return
    task_id = int(call.data.split(":")[1])
    if db.delete_task(task_id):
        ack(call, "✅ Удалено")
        edit_text(call.message.chat.id, call.message.message_id,
                  f"🗑 <i>Задача #{task_id} удалена.</i>")
    else:
        ack(call, "❌ Задача не найдена", alert=True)


# ── Отмена действия ───────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("cancelaction:"))
def cb_cancelaction(call):
    ack(call, "↩️ Отменено")
    task_id = int(call.data.split(":")[1])
    task    = db.get_task_by_id(task_id)
    if task:
        edit_kb(call.message.chat.id, call.message.message_id,
                kb_task_actions(task_id, admin(call.from_user)))


# ── Неизвестный callback ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def cb_unknown(call):
    logger.warning("Неизвестный callback: %s", call.data)
    ack(call)
