import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG


def get_connection(dict_cursor=False):
    try:
        cursor_factory = RealDictCursor if dict_cursor else None
        return psycopg2.connect(**DB_CONFIG, cursor_factory=cursor_factory)
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None


def close_connection(conn):
    if conn:
        conn.close()
