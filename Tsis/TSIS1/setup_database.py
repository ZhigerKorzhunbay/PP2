from pathlib import Path

import psycopg2
from config import DB_CONFIG


BASE_DIR = Path(__file__).resolve().parent


def execute_sql_file(conn, filename):
    path = BASE_DIR / filename
    with open(path, 'r', encoding='utf-8') as file:
        sql = file.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f'OK: {filename}')


def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        execute_sql_file(conn, 'schema.sql')
        execute_sql_file(conn, 'procedures.sql')
        conn.close()
        print('База данных готова.')
    except Exception as e:
        print(f'Ошибка установки БД: {e}')


if __name__ == '__main__':
    main()
