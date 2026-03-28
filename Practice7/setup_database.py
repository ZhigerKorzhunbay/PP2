import psycopg2

# Параметры подключения
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': '1234',  # Замени на свой пароль
    'database': 'postgres'  # Временно используем стандартную БД
}

def create_database():
    """Создание базы данных phonebook_db"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Проверяем существует ли база данных
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'phonebook_db'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE phonebook_db")
        print("База данных phonebook_db создана")
    else:
        print("База данных phonebook_db уже существует")
    
    cur.close()
    conn.close()

def create_table():
    """Создание таблицы contacts"""
    config = DB_CONFIG.copy()
    config['database'] = 'phonebook_db'
    
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    
    # Создаем таблицу
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    print("Таблица contacts создана")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_database()
    create_table()
    print("База данных готова к использованию!")