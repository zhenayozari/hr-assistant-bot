import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_FILE = 'hr_assistant.db'

class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.init_database()
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Возвращать результаты как словари
        return conn
    
    def init_database(self):
        """Создать таблицы если их нет"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица: Профили пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                company_name TEXT,              -- Добавили
                company_description TEXT,       -- Добавили
                hh_client_id TEXT,
                hh_employer_id TEXT,
                hh_access_token TEXT,
                hh_refresh_token TEXT,
                telegram_chat_ids TEXT,
                is_paid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица: Вакансии
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vacancies (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                pro_talk_criteria TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES profiles (id)
            )
        ''')
        
        # Таблица: Кандидаты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                vacancy_id INTEGER,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                salary TEXT,
                resume_url TEXT,
                analysis_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES profiles (id),
                FOREIGN KEY (vacancy_id) REFERENCES vacancies (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ База данных '{self.db_file}' инициализирована")
    
    # === ПРОФИЛИ ===
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получить профиль пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def create_profile(self, user_id: str) -> Dict[str, Any]:
        """Создать новый профиль"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO profiles (id, telegram_chat_ids) VALUES (?, ?)",
            (user_id, "[]")
        )
        conn.commit()
        conn.close()
        return self.get_profile(user_id)
    
    def update_profile(self, user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Обновить профиль"""
        if not kwargs:
            return self.get_profile(user_id)
        
        # Формируем SET часть запроса
        set_parts = []
        values = []
        for key, value in kwargs.items():
            set_parts.append(f"{key} = ?")
            values.append(value)
        values.append(user_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        query = f"UPDATE profiles SET {', '.join(set_parts)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return self.get_profile(user_id)
    
    # === ВАКАНСИИ ===
    
    def save_vacancy(self, vacancy_id: int, user_id: str, title: str, criteria: str = None):
        """Сохранить вакансию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO vacancies (id, user_id, title, pro_talk_criteria) 
               VALUES (?, ?, ?, ?)""",
            (vacancy_id, user_id, title, criteria)
        )
        conn.commit()
        conn.close()
    
    def get_all_vacancies(self, user_id: str) -> List[Dict[str, Any]]:
        """Получить все вакансии пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM vacancies WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_vacancy(self, vacancy_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """Получить вакансию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM vacancies WHERE id = ? AND user_id = ?",
            (vacancy_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_vacancies(self, user_id: str) -> List[Dict[str, Any]]:
        """Получить все вакансии пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM vacancies WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # === КАНДИДАТЫ ===
    
    def save_candidate(self, candidate_id: int, user_id: str, vacancy_id: int, 
                      full_name: str, analysis_result: str = None, **kwargs):
        """Сохранить кандидата"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO candidates 
               (id, user_id, vacancy_id, full_name, analysis_result, email, phone, salary, resume_url) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (candidate_id, user_id, vacancy_id, full_name, analysis_result,
             kwargs.get('email'), kwargs.get('phone'), kwargs.get('salary'), kwargs.get('resume_url'))
        )
        conn.commit()
        conn.close()
    
    def get_candidate(self, candidate_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """Получить кандидата"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM candidates WHERE id = ? AND user_id = ?",
            (candidate_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

# Создаём глобальный экземпляр
db = Database()
