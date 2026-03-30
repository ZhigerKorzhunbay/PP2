import psycopg2
from config import DB_CONFIG

def execute_sql_file(conn, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            sql = file.read()
            
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            print(f"Файл {filename} успешно выполнен")
            
    except Exception as e:
        print(f"Ошибка при выполнении {filename}: {e}")
        conn.rollback()

def main():
    print("Установка функций и процедур PostgreSQL...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        
        execute_sql_file(conn, 'functions.sql')
        
        conn.close()
        print("\nВсе функции и процедуры успешно установлены!")
        
    except Exception as e:
        print(f"Ошибка подключения: {e}")

if __name__ == "__main__":
    main()