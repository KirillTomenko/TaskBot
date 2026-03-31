# 🤖 TaskBot

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![pyTelegramBotAPI](https://img.shields.io/badge/pyTelegramBotAPI-4.x-blue?logo=telegram)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite)
![License](https://img.shields.io/badge/license-MIT-green)

Телеграм-бот для управления задачами с веб-дашбордом на Flask.  
Принимает задачи через Telegram, хранит в SQLite, управляется через браузер.

---

## ✨ Фичи

| Возможность | Детали |
|---|---|
| 📥 Приём задач | Пользователь отправляет текст — бот сохраняет |
| 🔘 Смена статуса | Inline-кнопки: новая → в работе → готово |
| 🌐 Веб-дашборд | Flask + Basic Auth, фильтрация, поиск |
| ⚡ Без перезагрузки | Смена статуса и удаление через AJAX |
| 🔔 Toast-уведомления | Мгновенный фидбек в интерфейсе |
| 🐳 Docker | Запуск одной командой |
| 🔒 Безопасность | Токен и БД не попадают в репозиторий |

---

## 🗂 Структура проекта

```
TaskBot/
├── Dockerfile              # Образ для bot и web
├── docker-compose.yml      # Два сервиса + shared volume
├── main.py                 # Точка входа бота
├── bot.py                  # Обработчики команд и callback'ов
├── requirements.txt        # 4 зависимости
├── .env                    # Секреты (не в git)
├── .env.example            # Шаблон переменных окружения
├── .gitignore
└── web/
    ├── main.py             # Flask-приложение с Basic Auth и API
    └── templates/
        └── index.html      # Тёмный интерфейс дашборда
```

---

## 🏗 Архитектура

```
Telegram API
    │
    ▼
┌─────────────┐    SQLite (Docker volume)    ┌─────────────┐
│  bot        │ ◄──────────────────────────► │    web      │
│  (main.py)  │        tasks.db              │  (Flask)    │
└─────────────┘                              └─────────────┘
                                                    │
                                             Basic Auth
                                                    │
                                             ┌──────▼──────┐
                                             │   Browser   │
                                             │    :8000    │
                                             └─────────────┘
```

---

## 🐳 Запуск через Docker (рекомендуется)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/KirillTomenko/TaskBot.git
cd TaskBot
```

### 2. Создать `.env` из шаблона

```bash
cp .env.example .env
```

Заполнить `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_LOGIN=admin
ADMIN_PASSWORD=your_password
DB_PATH=/app/data/tasks.db
```

### 3. Запустить

```bash
docker-compose up --build -d
```

Бот запустится автоматически. Дашборд доступен на `http://localhost:8000`.

### Полезные команды

```bash
docker-compose logs -f           # все логи в реальном времени
docker-compose logs -f bot       # только бот
docker-compose logs -f web       # только дашборд
docker-compose down              # остановить (данные сохраняются)
docker-compose down -v           # остановить + удалить БД
docker volume ls                 # проверить volume
```

### Бэкап базы данных

```bash
docker run --rm \
  -v taskbot_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/db_backup.tar.gz /data
```

---

## 💻 Запуск без Docker

```bash
pip install -r requirements.txt
cp .env.example .env  # заполнить токен и пароль

# Терминал 1 — бот
python main.py

# Терминал 2 — дашборд
python web/main.py
```

---

## 🗃 База данных

Таблица `tasks`:

| Поле | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | Автоинкремент |
| `user_id` | INTEGER | Telegram user ID |
| `username` | TEXT | @username |
| `text` | TEXT | Текст задачи |
| `status` | TEXT | `new` / `in_progress` / `done` |
| `created_at` | DATETIME | Время создания |

---

## ⚙️ Переменные окружения

| Переменная | Описание | Обязательная |
|---|---|---|
| `BOT_TOKEN` | Токен от @BotFather | ✅ |
| `ADMIN_LOGIN` | Логин для дашборда | ✅ |
| `ADMIN_PASSWORD` | Пароль для дашборда | ✅ |
| `DB_PATH` | Путь к SQLite файлу | ✅ в Docker |

---

## 📦 Зависимости

```
pyTelegramBotAPI
flask
python-dotenv
flask-httpauth
```

---

## 📄 Лицензия

MIT
