import psycopg2
from psycopg2 import sql, extras
import csv
from config import DB_CONFIG

class PhoneBook:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = False
        self.cursor = self.conn.cursor()
    
    def close(self):
        self.cursor.close()
        self.conn.close()
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()
    
    def import_from_csv(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)
                
                for row in reader:
                    if len(row) >= 2:
                        name, phone = row[0], row[1]
                        try:
                            self.cursor.execute(
                                "INSERT INTO contacts (name, phone) VALUES (%s, %s)",
                                (name, phone)
                            )
                        except psycopg2.IntegrityError:
                            print(f"Контакт {name} с телефоном {phone} уже существует")
                            self.rollback()
                            continue
                
                self.commit()
                print(f"Контакты из файла {filename} успешно импортированы")
                
        except FileNotFoundError:
            print(f"Файл {filename} не найден")
        except Exception as e:
            print(f"Ошибка при импорте: {e}")
            self.rollback()
    
    def insert_from_console(self):
        print("\n--- Добавление нового контакта ---")
        name = input("Введите имя: ").strip()
        phone = input("Введите телефон: ").strip()
        
        if not name or not phone:
            print("Имя и телефон не могут быть пустыми")
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO contacts (name, phone) VALUES (%s, %s)",
                (name, phone)
            )
            self.commit()
            print(f"Контакт {name} успешно добавлен!")
        except psycopg2.IntegrityError:
            print(f"Контакт с телефоном {phone} уже существует")
            self.rollback()
        except Exception as e:
            print(f"Ошибка при добавлении: {e}")
            self.rollback()
    
    def update_contact(self):
        print("\n--- Обновление контакта ---")
        phone = input("Введите номер телефона контакта для обновления: ").strip()
        
        self.cursor.execute("SELECT id, name, phone FROM contacts WHERE phone = %s", (phone,))
        contact = self.cursor.fetchone()
        
        if not contact:
            print("Контакт не найден")
            return
        
        print(f"\nНайден контакт: ID: {contact[0]}, Имя: {contact[1]}, Телефон: {contact[2]}")
        
        print("\nЧто хотите обновить?")
        print("1. Имя")
        print("2. Телефон")
        choice = input("Выберите (1-2): ").strip()
        
        try:
            if choice == '1':
                new_name = input("Введите новое имя: ").strip()
                self.cursor.execute(
                    "UPDATE contacts SET name = %s WHERE phone = %s",
                    (new_name, phone)
                )
                print("Имя успешно обновлено!")
            elif choice == '2':
                new_phone = input("Введите новый телефон: ").strip()
                self.cursor.execute(
                    "UPDATE contacts SET phone = %s WHERE phone = %s",
                    (new_phone, phone)
                )
                print("Телефон успешно обновлен!")
            else:
                print("Неверный выбор")
                return
            
            self.commit()
        except psycopg2.IntegrityError:
            print("Такой телефон уже существует")
            self.rollback()
        except Exception as e:
            print(f"Ошибка при обновлении: {e}")
            self.rollback()
    
    def search_contacts(self):
        print("\n--- Поиск контактов ---")
        print("1. Поиск по имени")
        print("2. Поиск по префиксу телефона")
        print("3. Показать все контакты")
        choice = input("Выберите (1-3): ").strip()
        
        try:
            if choice == '1':
                name = input("Введите имя для поиска: ").strip()
                self.cursor.execute(
                    "SELECT * FROM contacts WHERE name ILIKE %s ORDER BY name",
                    (f"%{name}%",)
                )
            elif choice == '2':
                prefix = input("Введите префикс телефона: ").strip()
                self.cursor.execute(
                    "SELECT * FROM contacts WHERE phone LIKE %s ORDER BY name",
                    (f"{prefix}%",)
                )
            elif choice == '3':
                self.cursor.execute("SELECT * FROM contacts ORDER BY name")
            else:
                print("Неверный выбор")
                return
            
            contacts = self.cursor.fetchall()
            
            if not contacts:
                print("Контакты не найдены")
                return
            
            print("\n" + "="*50)
            print(f"{'ID':<5} {'Имя':<20} {'Телефон':<15}")
            print("="*50)
            for contact in contacts:
                print(f"{contact[0]:<5} {contact[1]:<20} {contact[2]:<15}")
            print("="*50)
            
        except Exception as e:
            print(f"Ошибка при поиске: {e}")
    
    def delete_contact(self):
        print("\n--- Удаление контакта ---")
        print("1. Удалить по имени")
        print("2. Удалить по номеру телефона")
        choice = input("Выберите (1-2): ").strip()
        
        try:
            if choice == '1':
                name = input("Введите имя для удаления: ").strip()
                self.cursor.execute(
                    "DELETE FROM contacts WHERE name ILIKE %s RETURNING *",
                    (name,)
                )
            elif choice == '2':
                phone = input("Введите номер телефона для удаления: ").strip()
                self.cursor.execute(
                    "DELETE FROM contacts WHERE phone = %s RETURNING *",
                    (phone,)
                )
            else:
                print("Неверный выбор")
                return
            
            deleted = self.cursor.fetchall()
            
            if deleted:
                self.commit()
                print(f"Удалено контактов: {len(deleted)}")
                for contact in deleted:
                    print(f"- {contact[1]} ({contact[2]})")
            else:
                print("Контакты не найдены")
                
        except Exception as e:
            print(f"Ошибка при удалении: {e}")
            self.rollback()

def main():
    phonebook = PhoneBook()
    
    while True:
        print("\n" + "="*50)
        print("ТЕЛЕФОННЫЙ СПРАВОЧНИК")
        print("="*50)
        print("1. Импорт из CSV файла")
        print("2. Добавить контакт (консоль)")
        print("3. Обновить контакт")
        print("4. Поиск контактов")
        print("5. Удалить контакт")
        print("6. Выход")
        print("="*50)
        
        choice = input("Выберите действие (1-6): ").strip()
        
        if choice == '1':
            filename = input("Введите имя CSV файла (например, contacts.csv): ").strip()
            phonebook.import_from_csv(filename)
        elif choice == '2':
            phonebook.insert_from_console()
        elif choice == '3':
            phonebook.update_contact()
        elif choice == '4':
            phonebook.search_contacts()
        elif choice == '5':
            phonebook.delete_contact()
        elif choice == '6':
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")
    
    phonebook.close()

if __name__ == "__main__":
    main()