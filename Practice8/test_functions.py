import psycopg2
from config import DB_CONFIG

def test_all_functions():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("="*60)
    print("ТЕСТИРОВАНИЕ ФУНКЦИЙ POSTGRESQL")
    print("="*60)
    
    print("\n1. Тест поиска по шаблону 'иван':")
    cur.callproc('search_contacts_pattern', ('иван',))
    results = cur.fetchall()
    for r in results:
        print(f"   {r[1]} - {r[2]}")
    
    print("\n2. Тест UPSERT (добавление нового):")
    cur.callproc('upsert_contact', ('Тестовый Пользователь', '7000000000'))
    result = cur.fetchone()
    print(f"   {result[0]}")
    
    print("\n   Тест UPSERT (обновление существующего):")
    cur.callproc('upsert_contact', ('Обновленное Имя', '7000000000'))
    result = cur.fetchone()
    print(f"   {result[0]}")
    conn.commit()
    
    print("\n3. Тест массовой вставки:")
    names = ['Иван1', 'Иван2', 'Неверный', 'Иван3']
    phones = ['777111111', '777222222', 'abc123', '777333333']
    
    cur.callproc('bulk_insert_contacts', (names, phones))
    invalid = cur.fetchall()
    
    if invalid:
        print("   Некорректные данные:")
        for inv in invalid:
            print(f"   - {inv[0]}, {inv[1]}: {inv[2]}")
    else:
        print("   Все данные корректны")
    conn.commit()
    
    print("\n4. Тест пагинации (страница 1, 3 записи):")
    cur.callproc('get_contacts_paginated', (1, 3))
    results = cur.fetchall()
    for r in results:
        print(f"   {r[1]} - {r[2]}")
    
    print("\n5. Тест удаления по телефону:")
    cur.callproc('delete_contacts', ('phone', '7000000000'))
    deleted = cur.fetchall()
    if deleted:
        print(f"   Удален: {deleted[0][1]} - {deleted[0][2]}")
    conn.commit()
    
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("="*60)

if __name__ == "__main__":
    test_all_functions()