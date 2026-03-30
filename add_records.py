import sqlite3
import random

first_names = [
    'Anna', 'Dmitry', 'Elena', 'Sergey', 'Olga', 'Alexey', 'Maria', 'Ivan',
    'Natalia', 'Pavel', 'Tatiana', 'Andrey', 'Svetlana', 'Mikhail', 'Yulia',
    'Nikolay', 'Ekaterina', 'Vladimir', 'Irina', 'Alexander', 'Marina', 'Roman',
    'Victoria', 'Artem', 'Anastasia', 'Denis', 'Polina', 'Maxim', 'Alina', 'Kirill'
]

last_names = [
    'Smirnova', 'Kuznetsov', 'Popova', 'Vasiliev', 'Petrov', 'Sokolov', 'Mikhailov',
    'Novikov', 'Fedorov', 'Morozov', 'Volkov', 'Alekseev', 'Lebedev', 'Semenov',
    'Egorov', 'Pavlov', 'Kozlov', 'Stepanov', 'Nikolaev', 'Orlov', 'Makarova',
    'Belov', 'Tarasov', 'Belova', 'Kovalenko', 'Bondarenko', 'Titov', 'Grigoriev',
    'Zakharov', 'Yakovlev'
]

# 🔥 ТОЧНЫЙ ПУТЬ К БАЗЕ ДАННЫХ
db_path = r'C:\Users\SNHIM\Desktop\test_sqlite'

print(f"📂 Подключение к: {db_path}")

# Проверяем существует ли файл
import os
if os.path.exists(db_path):
    print(f"✅ Файл найден (размер: {os.path.getsize(db_path)} байт)")
else:
    print("❌ Файл не найден!")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверяем какие таблицы есть
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"📋 Таблицы в базе: {[t[0] for t in tables]}")

# Проверяем есть ли таблица students
if ('stydents',) in tables:
    print("✅ Таблица 'students' найдена!")
    
    # Считаем текущие записи
    cursor.execute('SELECT COUNT(*) FROM stydents')
    old_count = cursor.fetchone()[0]
    print(f"📊 Текущее количество записей: {old_count}")
    
    # Добавляем 96 записей
    print("➕ Добавление 96 записей...")
    for i in range(96):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        age = random.randint(18, 65)
        is_active = random.choice([0, 1])
        
        cursor.execute('''
            INSERT INTO stydents (first_name, last_name, age, is_active)
            VALUES (?, ?, ?, ?)
        ''', (first_name, last_name, age, is_active))
    
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM students')
    new_count = cursor.fetchone()[0]
    print(f'✅ Успешно! Добавлено 96 записей.')
    print(f'📊 Всего записей: {new_count}')
else:
    print("❌ Таблица 'stydents' не найдена!")
    print("💡 Создаём таблицу...")
    cursor.execute('''
        CREATE TABLE stydents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            age INTEGER,
            is_active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    print("✅ Таблица создана!")

conn.close()
print('🔌 Готово!')