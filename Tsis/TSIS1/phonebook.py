import csv
import json
from datetime import date, datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from config import DB_CONFIG


VALID_SORTS = {
    'name': 'c.name ASC',
    'birthday': 'c.birthday ASC NULLS LAST, c.name ASC',
    'date': 'c.created_at ASC, c.name ASC',
    'created_at': 'c.created_at ASC, c.name ASC',
}
PHONE_TYPES = {'home', 'work', 'mobile'}


class PhoneBook:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()
        print('Подключение к базе данных установлено.')

    def close(self):
        self.cur.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    @staticmethod
    def normalize_type(value):
        phone_type = (value or 'mobile').strip().lower()
        return phone_type if phone_type in PHONE_TYPES else 'mobile'

    @staticmethod
    def normalize_date(value):
        value = (value or '').strip()
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError('Дата должна быть в формате YYYY-MM-DD')

    @staticmethod
    def parse_phones(raw):
        """Accepts: 7771234567 or mobile:7771234567, work:7772223333."""
        phones = []
        for part in (raw or '').split(','):
            part = part.strip()
            if not part:
                continue
            if ':' in part:
                phone_type, phone = part.split(':', 1)
            else:
                phone_type, phone = 'mobile', part
            phone = phone.strip()
            if phone:
                phones.append({'phone': phone, 'type': PhoneBook.normalize_type(phone_type)})
        return phones

    @staticmethod
    def to_json_value(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    def group_id(self, group_name):
        group_name = (group_name or 'Other').strip() or 'Other'
        self.cur.execute(
            'INSERT INTO groups(name) VALUES (%s) ON CONFLICT (name) DO NOTHING',
            (group_name,)
        )
        self.cur.execute('SELECT id FROM groups WHERE name = %s LIMIT 1', (group_name,))
        return self.cur.fetchone()['id']

    def contact_id(self, name):
        self.cur.execute(
            'SELECT id FROM contacts WHERE LOWER(name) = LOWER(%s) ORDER BY id LIMIT 1',
            ((name or '').strip(),)
        )
        row = self.cur.fetchone()
        return row['id'] if row else None

    def set_phones(self, contact_id, phones, replace=False):
        if replace:
            self.cur.execute('DELETE FROM phones WHERE contact_id = %s', (contact_id,))

        first_phone = None
        for item in phones or []:
            phone = str(item.get('phone') or '').strip()
            if not phone:
                continue
            phone_type = self.normalize_type(item.get('type'))
            first_phone = first_phone or phone
            self.cur.execute(
                '''INSERT INTO phones(contact_id, phone, type)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (contact_id, phone) DO UPDATE SET type = EXCLUDED.type''',
                (contact_id, phone, phone_type)
            )

        if first_phone:
            self.cur.execute('UPDATE contacts SET phone = %s WHERE id = %s', (first_phone, contact_id))

    def save_contact(self, data, overwrite=False, replace_phones=True):
        name = (data.get('name') or '').strip()
        if not name:
            raise ValueError('Имя не может быть пустым')

        phones = data.get('phones') or []
        if not phones and data.get('phone'):
            phones = [{'phone': data.get('phone'), 'type': data.get('type') or 'mobile'}]

        contact_id = self.contact_id(name)
        if contact_id and not overwrite:
            return 'skipped'

        birthday = self.normalize_date(data.get('birthday'))
        group_id = self.group_id(data.get('group') or data.get('group_name') or 'Other')
        first_phone = None
        if phones:
            raw_phone = phones[0].get('phone')
            first_phone = str(raw_phone).strip() if raw_phone else None

        if contact_id:
            self.cur.execute(
                '''UPDATE contacts
                   SET email = %s, birthday = %s, group_id = %s, phone = COALESCE(%s, phone)
                   WHERE id = %s''',
                (data.get('email') or None, birthday, group_id, first_phone, contact_id)
            )
            self.set_phones(contact_id, phones, replace=replace_phones)
            return 'updated'

        self.cur.execute(
            '''INSERT INTO contacts(name, phone, email, birthday, group_id)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id''',
            (name, first_phone, data.get('email') or None, birthday, group_id)
        )
        contact_id = self.cur.fetchone()['id']
        self.set_phones(contact_id, phones, replace=False)
        return 'inserted'

    def print_rows(self, rows):
        rows = list(rows or [])
        if not rows:
            print('Контакты не найдены.')
            return

        print('\n' + '=' * 126)
        print(f"{'ID':<5} {'Имя':<24} {'Email':<28} {'ДР':<12} {'Группа':<12} {'Телефоны':<35} {'Создан':<19}")
        print('=' * 126)
        for row in rows:
            created_at = self.to_json_value(row.get('created_at')) or '-'
            print(
                f"{str(row.get('id', '-')):<5} "
                f"{str(row.get('name') or '-'):<24} "
                f"{str(row.get('email') or '-'):<28} "
                f"{str(row.get('birthday') or '-'):<12} "
                f"{str(row.get('group_name') or '-'):<12} "
                f"{str(row.get('phones') or '-'):<35} "
                f"{str(created_at)[:19]:<19}"
            )
        print('=' * 126)

    def add_or_update_contact(self):
        print('\n--- Добавить / обновить контакт ---')
        item = {
            'name': input('Имя: ').strip(),
            'email': input('Email: ').strip() or None,
            'birthday': input('Birthday YYYY-MM-DD: ').strip() or None,
            'group': input('Группа Family/Work/Friend/Other: ').strip() or 'Other',
            'phones': self.parse_phones(input('Телефоны (mobile:777, work:888): '))
        }
        try:
            exists = self.contact_id(item['name'])
            overwrite = True
            if exists:
                answer = input('Контакт уже существует. overwrite/skip? ').strip().lower()
                overwrite = answer.startswith('o')
            status = self.save_contact(item, overwrite=overwrite, replace_phones=True)
            self.commit()
            print(f'Готово: {status}')
        except Exception as e:
            self.rollback()
            print(f'Ошибка сохранения: {e}')

    def search_contacts(self):
        query = input('Поиск по имени/email/телефону/группе: ').strip()
        try:
            self.cur.execute('SELECT * FROM search_contacts(%s::text)', (query,))
            self.print_rows(self.cur.fetchall())
        except Exception as e:
            self.rollback()
            print(f'Ошибка поиска: {e}')

    def filter_sort(self):
        group_name = input('Группа (Enter = все): ').strip()
        email_part = input('Email содержит (Enter = все): ').strip()
        sort_key = input('Сортировка name/birthday/date (по умолчанию name): ').strip().lower() or 'name'
        order_by = VALID_SORTS.get(sort_key, VALID_SORTS['name'])

        where, params = [], []
        if group_name:
            where.append('g.name ILIKE %s')
            params.append(f'%{group_name}%')
        if email_part:
            where.append('COALESCE(c.email, \'\') ILIKE %s')
            params.append(f'%{email_part}%')
        where_sql = 'WHERE ' + ' AND '.join(where) if where else ''

        try:
            self.cur.execute(f'''
                SELECT c.id, c.name, c.email, c.birthday, g.name AS group_name,
                       COALESCE(STRING_AGG(p.type || ': ' || p.phone, ', ' ORDER BY p.type, p.phone), '') AS phones,
                       c.created_at
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                {where_sql}
                GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
                ORDER BY {order_by}
            ''', params)
            self.print_rows(self.cur.fetchall())
        except Exception as e:
            self.rollback()
            print(f'Ошибка фильтрации: {e}')

    def page_loop(self):
        try:
            page_size = int(input('Размер страницы (по умолчанию 5): ').strip() or '5')
            page_size = max(page_size, 1)
        except ValueError:
            page_size = 5

        page = 1
        while True:
            try:
                self.cur.execute('SELECT * FROM get_contacts_paginated(%s, %s)', (page, page_size))
                page_data = self.cur.fetchall()
                total = page_data[0]['total_count'] if page_data else 0
                total_pages = max((total + page_size - 1) // page_size, 1)

                if page > total_pages:
                    page = total_pages
                    continue

                ids = [row['id'] for row in page_data]
                print(f'\nСтраница {page}/{total_pages}. Всего: {total}')

                if ids:
                    self.cur.execute('''
                        SELECT c.id, c.name, c.email, c.birthday, g.name AS group_name,
                               COALESCE(STRING_AGG(p.type || ': ' || p.phone, ', ' ORDER BY p.type, p.phone), '') AS phones,
                               c.created_at
                        FROM contacts c
                        LEFT JOIN groups g ON g.id = c.group_id
                        LEFT JOIN phones p ON p.contact_id = c.id
                        WHERE c.id = ANY(%s)
                        GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
                        ORDER BY c.name
                    ''', (ids,))
                    self.print_rows(self.cur.fetchall())
                else:
                    print('Нет контактов.')

                command = input('next / prev / quit: ').strip().lower()
                if command in {'next', 'n'} and page < total_pages:
                    page += 1
                elif command in {'prev', 'p'} and page > 1:
                    page -= 1
                elif command in {'quit', 'q'}:
                    break
            except Exception as e:
                self.rollback()
                print(f'Ошибка пагинации: {e}')
                break

    def add_phone(self):
        name = input('Имя контакта: ').strip()
        phone = input('Новый телефон: ').strip()
        phone_type = input('Тип home/work/mobile: ').strip().lower() or 'mobile'
        try:
            self.cur.execute('CALL add_phone(%s, %s, %s)', (name, phone, phone_type))
            self.commit()
            print('Телефон добавлен.')
        except Exception as e:
            self.rollback()
            print(f'Ошибка: {e}')

    def move_to_group(self):
        name = input('Имя контакта: ').strip()
        group_name = input('Новая группа: ').strip() or 'Other'
        try:
            self.cur.execute('CALL move_to_group(%s, %s)', (name, group_name))
            self.commit()
            print('Группа обновлена.')
        except Exception as e:
            self.rollback()
            print(f'Ошибка: {e}')

    def export_json(self):
        filename = input('JSON файл для экспорта (contacts.json): ').strip() or 'contacts.json'
        try:
            self.cur.execute('''
                SELECT c.id, c.name, c.email, c.birthday, g.name AS group_name, c.created_at
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                ORDER BY c.name
            ''')
            contacts = []
            for contact in self.cur.fetchall():
                self.cur.execute(
                    'SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY type, phone',
                    (contact['id'],)
                )
                contacts.append({
                    'name': contact['name'],
                    'email': contact['email'],
                    'birthday': self.to_json_value(contact['birthday']),
                    'group': contact['group_name'] or 'Other',
                    'phones': [dict(row) for row in self.cur.fetchall()],
                    'created_at': self.to_json_value(contact['created_at'])
                })

            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(contacts, file, ensure_ascii=False, indent=2)
            print(f'Экспортировано контактов: {len(contacts)} -> {filename}')
        except Exception as e:
            self.rollback()
            print(f'Ошибка экспорта JSON: {e}')

    def import_json(self):
        filename = input('JSON файл для импорта: ').strip()
        if not filename:
            print('Файл не указан.')
            return

        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
            contacts = data.get('contacts', data) if isinstance(data, dict) else data
            if not isinstance(contacts, list):
                raise ValueError('JSON должен быть списком контактов или объектом {"contacts": [...]}')

            stats = {'inserted': 0, 'updated': 0, 'skipped': 0}
            for item in contacts:
                name = item.get('name', '')
                overwrite = False
                if self.contact_id(name):
                    answer = input(f"Контакт '{name}' уже есть. skip/overwrite? ").strip().lower()
                    overwrite = answer.startswith('o')
                status = self.save_contact(item, overwrite=overwrite, replace_phones=True)
                stats[status] += 1

            self.commit()
            print(f'Импорт JSON завершён: {stats}')
        except Exception as e:
            self.rollback()
            print(f'Ошибка импорта JSON: {e}')

    def import_csv(self):
        filename = input('CSV файл (contacts.csv): ').strip() or 'contacts.csv'
        try:
            stats = {'inserted': 0, 'updated': 0, 'skipped': 0}
            with open(filename, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    item = {
                        'name': row.get('name'),
                        'email': row.get('email') or None,
                        'birthday': row.get('birthday') or None,
                        'group': row.get('group') or row.get('group_name') or 'Other',
                        'phones': [{
                            'phone': row.get('phone'),
                            'type': row.get('type') or row.get('phone_type') or 'mobile'
                        }]
                    }
                    status = self.save_contact(item, overwrite=True, replace_phones=False)
                    stats[status] += 1
            self.commit()
            print(f'CSV импортирован: {stats}')
        except Exception as e:
            self.rollback()
            print(f'Ошибка импорта CSV: {e}')


def main():
    try:
        phonebook = PhoneBook()
    except Exception as e:
        print(f'Не удалось подключиться к базе данных. Проверьте config.py. Ошибка: {e}')
        return

    actions = {
        '1': phonebook.add_or_update_contact,
        '2': phonebook.search_contacts,
        '3': phonebook.filter_sort,
        '4': phonebook.page_loop,
        '5': phonebook.add_phone,
        '6': phonebook.move_to_group,
        '7': phonebook.export_json,
        '8': phonebook.import_json,
        '9': phonebook.import_csv,
    }

    while True:
        print('\n' + '=' * 52)
        print('TSIS 1 PHONEBOOK — EXTENDED')
        print('1. Добавить / обновить контакт')
        print('2. Поиск по имени/email/телефону/группе')
        print('3. Фильтр по группе/email + сортировка')
        print('4. Пагинация next/prev/quit')
        print('5. Добавить телефон контакту')
        print('6. Переместить контакт в группу')
        print('7. Export JSON')
        print('8. Import JSON')
        print('9. Import CSV extended')
        print('0. Выход')
        choice = input('Выберите действие: ').strip()

        if choice == '0':
            break
        action = actions.get(choice)
        action() if action else print('Неверный выбор.')

    phonebook.close()


if __name__ == '__main__':
    main()
