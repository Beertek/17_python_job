import sqlite3
from datetime import datetime, timedelta
import random

# 2. Создаем базу данных (или подключаемся к существующей)
conn = sqlite3.connect('beauty_salon.db')
cursor = conn.cursor()

# 3. Создаем таблицы
def create_tables():
    # Таблица клиентов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        email TEXT,
        registration_date DATE DEFAULT CURRENT_DATE
    )
    ''')
    
    # Таблица мастеров
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS masters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        specialization TEXT,
        phone TEXT UNIQUE NOT NULL,
        hire_date DATE DEFAULT CURRENT_DATE
    )
    ''')
    
    # Таблица услуг
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        duration_minutes INTEGER NOT NULL,
        price DECIMAL(10, 2) NOT NULL
    )
    ''')
    
    # Таблица записей (связующая)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        master_id INTEGER NOT NULL,
        service_id INTEGER NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time TIME NOT NULL,
        status TEXT DEFAULT 'scheduled',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
        FOREIGN KEY (master_id) REFERENCES masters(id) ON DELETE CASCADE,
        FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    print("Таблицы успешно созданы!")

# 4. Функции для заполнения базы данных
def insert_sample_data():
    # Очищаем таблицы перед заполнением (для чистоты эксперимента)
    cursor.execute("DELETE FROM appointments")
    cursor.execute("DELETE FROM clients")
    cursor.execute("DELETE FROM masters")
    cursor.execute("DELETE FROM services")
    
    # Добавляем клиентов
    clients_data = [
        ('Анна', 'Иванова', '+79001234567', 'anna.ivanova@email.com'),
        ('Мария', 'Петрова', '+79002345678', 'maria.petrova@email.com'),
        ('Елена', 'Сидорова', '+79003456789', 'elena.sidorova@email.com'),
        ('Ольга', 'Смирнова', '+79004567890', 'olga.smirnova@email.com'),
        ('Наталья', 'Козлова', '+79005678901', 'natalia.kozlova@email.com'),
        ('Татьяна', 'Морозова', '+79006789012', 'tatiana.morozova@email.com'),
        ('Ирина', 'Волкова', '+79007890123', 'irina.volkova@email.com'),
        ('Светлана', 'Соколова', '+79008901234', 'svetlana.sokolova@email.com')
    ]
    
    cursor.executemany('''
    INSERT INTO clients (first_name, last_name, phone, email)
    VALUES (?, ?, ?, ?)
    ''', clients_data)
    
    # Добавляем мастеров
    masters_data = [
        ('Александр', 'Кузнецов', 'Парикмахер-стилист', '+79851234567'),
        ('Екатерина', 'Васильева', 'Визажист', '+79852345678'),
        ('Дмитрий', 'Новиков', 'Маникюр', '+79853456789'),
        ('Юлия', 'Морозова', 'Косметолог', '+79854567890'),
        ('Сергей', 'Павлов', 'Парикмахер', '+79855678901'),
        ('Анастасия', 'Федорова', 'Массажист', '+79856789012')
    ]
    
    cursor.executemany('''
    INSERT INTO masters (first_name, last_name, specialization, phone)
    VALUES (?, ?, ?, ?)
    ''', masters_data)
    
    # Добавляем услуги
    services_data = [
        ('Стрижка женская', 'Стрижка любой сложности', 60, 2500.00),
        ('Стрижка мужская', 'Классическая или модельная стрижка', 45, 1800.00),
        ('Маникюр классический', 'Обрезной маникюр', 60, 2000.00),
        ('Педикюр', 'Комплексный уход за ногами', 90, 3000.00),
        ('Макияж вечерний', 'Яркий образ для особого случая', 75, 3500.00),
        ('Чистка лица', 'Глубокая чистка лица', 60, 2800.00),
        ('Окрашивание волос', 'Окрашивание любой сложности', 120, 5000.00),
        ('Массаж спины', 'Расслабляющий массаж', 60, 2500.00),
        ('Укладка', 'Укладка феном или плойкой', 45, 1500.00),
        ('Биозавивка ресниц', 'Долговременная завивка ресниц', 60, 2200.00)
    ]
    
    cursor.executemany('''
    INSERT INTO services (name, description, duration_minutes, price)
    VALUES (?, ?, ?, ?)
    ''', services_data)
    
    # Создаем записи (случайные)
    start_date = datetime.now() - timedelta(days=30)
    statuses = ['scheduled', 'completed', 'cancelled']
    
    appointments_data = []
    for i in range(25):  # 25 записей
        client_id = random.randint(1, 8)
        master_id = random.randint(1, 6)
        service_id = random.randint(1, 10)
        
        # Случайная дата в последние 30 дней или следующие 14 дней
        days_offset = random.randint(-30, 14)
        app_date = (datetime.now() + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        
        # Случайное время с 9:00 до 19:00
        hour = random.randint(9, 18)
        minute = random.choice([0, 15, 30, 45])
        app_time = f"{hour:02d}:{minute:02d}"
        
        # Статус зависит от даты
        if app_date < datetime.now().strftime('%Y-%m-%d'):
            status = random.choice(['completed', 'cancelled'])
        else:
            status = 'scheduled'
        
        notes = random.choice(['', 'Прийти пораньше', 'Аллергия на цитрусовые', ''])
        
        appointments_data.append((
            client_id, master_id, service_id, app_date, app_time, status, notes
        ))
    
    cursor.executemany('''
    INSERT INTO appointments (client_id, master_id, service_id, appointment_date, appointment_time, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', appointments_data)
    
    conn.commit()
    print("Тестовые данные успешно добавлены!")

# Функции для выборки данных
def get_all_clients():
    cursor.execute('''
    SELECT id, first_name, last_name, phone, email, registration_date 
    FROM clients 
    ORDER BY last_name, first_name
    ''')
    return cursor.fetchall()

def get_upcoming_appointments():
    cursor.execute('''
    SELECT 
        c.first_name || ' ' || c.last_name as client,
        m.first_name || ' ' || m.last_name as master,
        s.name as service,
        a.appointment_date,
        a.appointment_time,
        a.status
    FROM appointments a
    JOIN clients c ON a.client_id = c.id
    JOIN masters m ON a.master_id = m.id
    JOIN services s ON a.service_id = s.id
    WHERE a.appointment_date >= DATE('now') 
    AND a.status = 'scheduled'
    ORDER BY a.appointment_date, a.appointment_time
    LIMIT 10
    ''')
    return cursor.fetchall()

def get_popular_services():
    cursor.execute('''
    SELECT 
        s.name,
        COUNT(*) as booking_count,
        SUM(s.price) as total_revenue
    FROM appointments a
    JOIN services s ON a.service_id = s.id
    WHERE a.status = 'completed'
    GROUP BY s.id
    ORDER BY booking_count DESC
    LIMIT 5
    ''')
    return cursor.fetchall()

def get_master_schedule(master_id):
    cursor.execute('''
    SELECT 
        a.appointment_date,
        a.appointment_time,
        c.first_name || ' ' || c.last_name as client,
        s.name as service,
        a.status
    FROM appointments a
    JOIN clients c ON a.client_id = c.id
    JOIN services s ON a.service_id = s.id
    WHERE a.master_id = ? 
    AND a.appointment_date >= DATE('now')
    ORDER BY a.appointment_date, a.appointment_time
    ''', (master_id,))
    return cursor.fetchall()

def print_section(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

# Основная программа
if __name__ == "__main__":
    # Создаем таблицы
    create_tables()
    
    # Заполняем тестовыми данными
    insert_sample_data()
    
    # Выводим различные выборки данных
    
    # 1. Все клиенты
    print_section("СПИСОК ВСЕХ КЛИЕНТОВ")
    clients = get_all_clients()
    for client in clients:
        print(f"ID: {client[0]}, {client[1]} {client[2]}, Тел: {client[3]}, Регистрация: {client[5]}")
    
    # 2. Ближайшие записи
    print_section("БЛИЖАЙШИЕ ЗАПИСИ (на 10 записей)")
    upcoming = get_upcoming_appointments()
    if upcoming:
        for app in upcoming:
            print(f"📅 {app[3]} {app[4]} | Клиент: {app[0]} | Мастер: {app[1]} | Услуга: {app[2]} | Статус: {app[5]}")
    else:
        print("Нет ближайших записей")
    
    # 3. Популярные услуги
    print_section("ТОП-5 ПОПУЛЯРНЫХ УСЛУГ")
    popular = get_popular_services()
    for i, service in enumerate(popular, 1):
        print(f"{i}. {service[0]} - {service[1]} записей, выручка: {service[2]:.2f} руб.")
    
    # 4. Расписание конкретного мастера
    print_section("РАСПИСАНИЕ МАСТЕРА (Александр Кузнецов)")
    schedule = get_master_schedule(1)  # ID мастера Александра
    if schedule:
        for app in schedule:
            status_icon = "✅" if app[4] == "completed" else "📅" if app[4] == "scheduled" else "❌"
            print(f"{status_icon} {app[0]} {app[1]} | {app[2]} | {app[3]} | {app[4]}")
    else:
        print("Нет записей к этому мастеру")
    
    # 5. Произвольный запрос: статистика по дням недели
    print_section("СТАТИСТИКА ЗАПИСЕЙ ПО ДНЯМ НЕДЕЛИ")
    cursor.execute('''
    SELECT 
        CASE cast(strftime('%w', appointment_date) as integer)
            WHEN 0 THEN 'Воскресенье'
            WHEN 1 THEN 'Понедельник'
            WHEN 2 THEN 'Вторник'
            WHEN 3 THEN 'Среда'
            WHEN 4 THEN 'Четверг'
            WHEN 5 THEN 'Пятница'
            WHEN 6 THEN 'Суббота'
        END as day_of_week,
        COUNT(*) as appointments_count
    FROM appointments
    WHERE status = 'completed'
    GROUP BY day_of_week
    ORDER BY appointments_count DESC
    ''')
    
    day_stats = cursor.fetchall()
    for day in day_stats:
        print(f"{day[0]}: {day[1]} записей")
    
    # Закрываем соединение
    conn.close()
    print("\n✅ Программа завершена. Соединение с БД закрыто.")