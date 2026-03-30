import psycopg2
from config import DB_CONFIG

class PhoneBook:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            print("Подключение к базе данных установлено!")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            raise
    
    def close(self):
        self.cursor.close()
        self.conn.close()
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()
    
    def search_pattern(self):
        print("\n--- Поиск по шаблону ---")
        pattern = input("Введите текст для поиска: ").strip()
        
        try:
            self.cursor.callproc('search_contacts_pattern', (pattern,))
            contacts = self.cursor.fetchall()
            
            if not contacts:
                print("Контакты не найдены")
                return
            
            print("\n" + "="*70)
            print(f"{'ID':<5} {'Имя':<25} {'Телефон':<15} {'Дата создания':<20}")
            print("="*70)
            for contact in contacts:
                print(f"{contact[0]:<5} {contact[1]:<25} {contact[2]:<15} {contact[3]:<20}")
            print("="*70)
            
        except Exception as e:
            print(f"Ошибка при поиске: {e}")
    
    def upsert_contact(self):
        print("\n--- Добавление или обновление контакта ---")
        name = input("Введите имя: ").strip()
        phone = input("Введите телефон: ").strip()
        
        if not name or not phone:
            print("Имя и телефон не могут быть пустыми")
            return
        
        try:
            self.cursor.callproc('upsert_contact', (name, phone))
            result = self.cursor.fetchone()
            print(result[0])
            self.commit()
            
        except Exception as e:
            print(f"Ошибка: {e}")
            self.rollback()
    
    def bulk_insert(self):
        print("\n--- Массовая вставка контактов ---")
        print("Введите контакты в формате: имя,телефон")
        print("Для завершения введите пустую строку")
        
        names = []
        phones = []
        
        while True:
            line = input("Контакт: ").strip()
            if not line:
                break
            
            parts = line.split(',')
            if len(parts) >= 2:
                names.append(parts[0].strip())
                phones.append(parts[1].strip())
            else:
                print("Неверный формат. Используйте: имя,телефон")
        
        if not names:
            print("Нет данных для вставки")
            return
        
        try:
            self.cursor.callproc('bulk_insert_contacts', (names, phones))
            invalid = self.cursor.fetchall()
            
            if invalid:
                print("\nНекорректные данные:")
                print("-"*50)
                for inv in invalid:
                    print(f"Имя: {inv[0]}, Телефон: {inv[1]}, Ошибка: {inv[2]}")
            else:
                print("Все контакты успешно добавлены/обновлены!")
            
            self.commit()
            
        except Exception as e:
            print(f"Ошибка при массовой вставке: {e}")
            self.rollback()
    
    def show_paginated(self):
        print("\n--- Постраничный вывод контактов ---")
        
        try:
            self.cursor.execute("SELECT COUNT(*) FROM contacts")
            total = self.cursor.fetchone()[0]
            
            if total == 0:
                print("Нет контактов в базе данных")
                return
            
            page_size = int(input("Сколько записей показывать на странице? (по умолчанию 5): ") or "5")
            total_pages = (total + page_size - 1) // page_size
            
            current_page = 1
            
            while True:
                self.cursor.callproc('get_contacts_paginated', (current_page, page_size))
                contacts = self.cursor.fetchall()
                
                print(f"\nСтраница {current_page} из {total_pages}")
                print("="*70)
                print(f"{'ID':<5} {'Имя':<25} {'Телефон':<15} {'Дата создания':<20}")
                print("="*70)
                
                for contact in contacts:
                    print(f"{contact[0]:<5} {contact[1]:<25} {contact[2]:<15} {contact[3]:<20}")
                
                print("="*70)
                print(f"Всего записей: {contacts[0][4] if contacts else 0}")
                
                print("\nНавигация:")
                print("n - следующая страница")
                print("p - предыдущая страница")
                print("q - выход")
                
                choice = input("Ваш выбор: ").strip().lower()
                
                if choice == 'n' and current_page < total_pages:
                    current_page += 1
                elif choice == 'p' and current_page > 1:
                    current_page -= 1
                elif choice == 'q':
                    break
                else:
                    if choice not in ['n', 'p']:
                        print("Неверная команда")
                        
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def delete_contacts(self):
        print("\n--- Удаление контактов ---")
        print("1. Удалить по имени")
        print("2. Удалить по телефону")
        choice = input("Выберите (1-2): ").strip()
        
        if choice == '1':
            name = input("Введите имя (или часть имени) для удаления: ").strip()
            delete_by = 'name'
            delete_value = name
        elif choice == '2':
            phone = input("Введите телефон для удаления: ").strip()
            delete_by = 'phone'
            delete_value = phone
        else:
            print("Неверный выбор")
            return
        
        try:
            self.cursor.callproc('delete_contacts', (delete_by, delete_value))
            deleted = self.cursor.fetchall()
            
            if deleted:
                print(f"\nУдалено контактов: {len(deleted)}")
                print("-"*50)
                for d in deleted:
                    print(f"ID: {d[0]}, Имя: {d[1]}, Телефон: {d[2]}")
                self.commit()
            else:
                print("Контакты не найдены")
                
        except Exception as e:
            print(f"Ошибка при удалении: {e}")
            self.rollback()
    
    def show_all(self):
        try:
            self.cursor.callproc('show_all_contacts')
            contacts = self.cursor.fetchall()
            
            if not contacts:
                print("Нет контактов в базе данных")
                return
            
            print("\n" + "="*70)
            print(f"{'ID':<5} {'Имя':<25} {'Телефон':<15} {'Дата создания':<20}")
            print("="*70)
            for contact in contacts:
                print(f"{contact[0]:<5} {contact[1]:<25} {contact[2]:<15} {contact[3]:<20}")
            print("="*70)
            
        except Exception as e:
            print(f"Ошибка: {e}")

def main():
    try:
        phonebook = PhoneBook()
    except:
        print("Не удалось подключиться к базе данных. Проверьте настройки.")
        return
    
    while True:
        print("\n" + "="*50)
        print("ТЕЛЕФОННЫЙ СПРАВОЧНИК (с функциями PostgreSQL)")
        print("="*50)
        print("1. Поиск по шаблону (имя/телефон)")
        print("2. Добавить или обновить контакт (UPSERT)")
        print("3. Массовая вставка контактов (с валидацией)")
        print("4. Постраничный вывод контактов")
        print("5. Удалить контакты")
        print("6. Показать все контакты")
        print("7. Выход")
        print("="*50)
        
        choice = input("Выберите действие (1-7): ").strip()
        
        if choice == '1':
            phonebook.search_pattern()
        elif choice == '2':
            phonebook.upsert_contact()
        elif choice == '3':
            phonebook.bulk_insert()
        elif choice == '4':
            phonebook.show_paginated()
        elif choice == '5':
            phonebook.delete_contacts()
        elif choice == '6':
            phonebook.show_all()
        elif choice == '7':
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")
    
    phonebook.close()

if __name__ == "__main__":
    main()