# 📋 TaskBot — Командный менеджер задач в Telegram

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![pyTelegramBotAPI](https://img.shields.io/badge/pyTelegramBotAPI-4.x-blue?logo=telegram)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?logo=sqlite)
![APScheduler](https://img.shields.io/badge/APScheduler-3.x-green)
![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)
![License](https://img.shields.io/badge/license-MIT-green)

Telegram-бот для управления командными задачами с веб-дашбордом, дедлайнами и напоминаниями. Написан на `pyTelegramBotAPI` + `Flask`, хранит данные в `SQLite3`, разворачивается через `Docker`.

---

## ✨ Возможности

| Функция | Описание |
|---|---|
| ➕ Добавление задач | 4-шаговый FSM-диалог: текст → категория → ответственный → дедлайн |
| 📋 Просмотр задач | Фильтрация по статусу, inline-кнопки управления |
| 🔄 Смена статуса | `новое` → `в работе` → `выполнено` / `отменено` |
| 👤 Назначение | Указать ответственного через @username |
| 📅 Дедлайны | Хранение дедлайна, визуальное предупреждение о просрочке |
| ⏰ Напоминания | APScheduler отправляет уведомление за 60 минут до дедлайна |
| 📥 Экспорт CSV | Выгрузка задач с фильтрацией по категории |
| 📊 Статистика | Распределение задач по статусам и категориям |
| 🌐 Веб-дашборд | Flask-интерфейс с фильтрами, поиском и Basic Auth |
| 🔒 Авторизация | Белый список пользователей, роль администратора |
| 🐳 Docker | `docker-compose` с двумя сервисами: бот + веб |

---

## 🖥️ Скриншоты

<table>
  <tr>
    <td><b>Главное меню</b></td>
    <td><b>Добавление задачи</b></td>
    <td><b>Список задач</b></td>
  </tr>
  <tr>
    <td><img src="docs/screens/start.png" width="250"/></td>
    <td><img src="docs/screens/add.png" width="250"/></td>
    <td><img src="docs/screens/list.png" width="250"/></td>
  </tr>
</table>

> Скриншоты размещаются в папке `docs/screens/`

---

## 🗂️ Структура проекта

```
taskbot/
├── bot.py                  # Бот: команды, FSM, callback-обработчики
├── main.py                 # Точка входа: polling + планировщик + (опц.) веб
├── config.py               # Настройки из .env
├── database/
│   └── db.py               # Все операции с SQLite3
├── scheduler/
│   └── reminders.py        # APScheduler: напоминания о дедлайнах
├── web/
│   ├── main.py             # Flask-приложение (дашборд)
│   └── templates/
│       └── index.html      # Bootstrap 5 интерфейс
├── data/
│   └── tasks.db            # SQLite база данных (создаётся автоматически)
├── .env.example            # Пример переменных окружения
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🚀 Быстрый старт

### Локально (без Docker)

**1. Клонировать репозиторий**
```bash
git clone https://github.com/KirillTomenko/taskbot.git
cd taskbot
```

**2. Создать и активировать виртуальное окружение**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

**3. Установить зависимости**
```bash
pip install -r requirements.txt
```

**4. Настроить переменные окружения**
```bash
cp .env.example .env
# Отредактируйте .env — укажите токен бота
```

**5. Запустить**
```bash
# Только бот + планировщик
python main.py

# Бот + планировщик + веб-дашборд
python main.py --with-web
```

### Через Docker

```bash
cp .env.example .env
# Укажите токен в .env

docker-compose up -d
```

Веб-дашборд будет доступен на `http://localhost:5000`

---

## ⚙️ Конфигурация

Скопируйте `.env.example` в `.env` и заполните:

```env
# Обязательно
BOT_TOKEN=ваш_токен_от_BotFather

# Белый список (через запятую). Пусто = доступ для всех
ALLOWED_USERS=username1,username2

# Администраторы (могут удалять задачи)
ADMIN_USERS=your_username

# Напоминания — за сколько минут до дедлайна
REMINDER_BEFORE_MINUTES=60

# Веб-дашборд
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_USER=admin
WEB_PASSWORD=changeme

# Путь к базе данных
DB_PATH=data/tasks.db
```

---

## 🤖 Команды бота

| Команда | Описание |
|---|---|
| `/start` | Приветствие и список команд |
| `/add` | Добавить новую задачу (4 шага) |
| `/list` | Просмотр задач с фильтрацией по статусу |
| `/list_csv` | Выгрузить задачи в CSV-файл |
| `/stats` | Статистика по статусам и категориям |
| `/cancel` | Отменить текущий диалог |
| `/help` | Справка |

---

## 🗄️ Схема базы данных

```sql
CREATE TABLE tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    text          TEXT    NOT NULL,
    user          TEXT    NOT NULL,        -- username автора
    user_id       INTEGER NOT NULL,        -- Telegram ID автора
    chat_id       INTEGER NOT NULL,        -- для отправки напоминаний
    assignee      TEXT    DEFAULT NULL,    -- username ответственного
    status        TEXT    NOT NULL DEFAULT 'new',
    category      TEXT    NOT NULL DEFAULT 'other',
    deadline      TEXT    DEFAULT NULL,    -- YYYY-MM-DD HH:MM
    reminder_sent INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL
);
```

---

## 🏗️ Архитектура

```
Пользователь (Telegram)
        │
        ▼
  pyTelegramBotAPI (polling)
        │
   ┌────┴─────┐
   │  bot.py  │  ← FSM (user_states dict), callback-обработчики
   └────┬─────┘
        │
   ┌────▼──────┐        ┌──────────────┐
   │   db.py   │        │ reminders.py │ ← APScheduler (60 сек)
   │  SQLite3  │◄───────┤              │
   └────┬──────┘        └──────────────┘
        │
   ┌────▼──────┐
   │  Flask    │  ← веб-дашборд (опционально)
   │ dashboard │
   └───────────┘
```

---

## 📦 Зависимости

```
pyTelegramBotAPI>=4.14
flask>=3.0
apscheduler>=3.10
python-dotenv>=1.0
```

---

## 🛠️ Стек технологий

- **Python 3.10+** — основной язык
- **pyTelegramBotAPI** — Telegram Bot API, без зависимости от pydantic/Rust
- **SQLite3** — встроенная БД, без внешнего сервера
- **APScheduler** — планировщик напоминаний в фоновом потоке
- **Flask + Bootstrap 5** — веб-дашборд
- **Docker + docker-compose** — контейнеризация

---

## 📝 Лицензия

MIT © 2026 [Ваше имя](https://github.com/KirillTomenko)