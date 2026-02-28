import sqlite3
from datetime import datetime
import os
import json


class Database:
    def __init__(self, db_name="reactionrps.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица сессий - создаем заново с правильными колонками
            cursor.execute('DROP TABLE IF EXISTS sessions')
            cursor.execute('''
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    avg_reaction REAL,
                    min_reaction REAL,
                    max_reaction REAL,
                    std_deviation REAL,
                    accuracy REAL,
                    total_wrong INTEGER,
                    trials_data TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица для хранения текущей сессии пользователя
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_session (
                    user_id INTEGER PRIMARY KEY,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            conn.commit()

    def create_user(self, username):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username) VALUES (?)",
                    (username,)
                )
                conn.commit()
                user_id = cursor.lastrowid
                # Автоматически делаем этого пользователя активным
                self.set_active_user(user_id)
                return user_id
        except sqlite3.IntegrityError:
            return None

    def get_user(self, username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, age, gender, created_at FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "age": row[2],
                    "gender": row[3],
                    "created_at": row[4]
                }
            return None

    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, age, gender, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "age": row[2],
                    "gender": row[3],
                    "created_at": row[4]
                }
            return None

    def username_exists(self, username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE username = ?",
                (username,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def set_active_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO active_session (user_id, last_login) VALUES (?, CURRENT_TIMESTAMP)",
                (user_id,)
            )
            conn.commit()

    def get_active_user(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM active_session ORDER BY last_login DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return self.get_user_by_id(row[0])
            return None

    def clear_active_user(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_session")
            conn.commit()

    def save_session(self, user_id, stats, trials_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions 
                (user_id, avg_reaction, min_reaction, max_reaction, std_deviation, accuracy, total_wrong, trials_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                stats['avg_reaction_time'],
                stats['min_reaction'],
                stats['max_reaction'],
                stats['std_deviation'],
                stats['accuracy'],
                stats['total_wrong'],
                json.dumps(trials_data, ensure_ascii=False)
            ))
            conn.commit()

    def get_user_sessions(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, avg_reaction, min_reaction, max_reaction, std_deviation, accuracy, total_wrong, trials_data
                FROM sessions
                WHERE user_id = ?
                ORDER BY date DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            return [{
                "date": row[0],
                "avg_reaction": row[1],
                "min_reaction": row[2],
                "max_reaction": row[3],
                "std_deviation": row[4],
                "accuracy": row[5],
                "total_wrong": row[6],
                "trials_data": json.loads(row[7]) if row[7] else []
            } for row in rows]

    def get_leaderboard(self, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.username, 
                       MIN(s.avg_reaction) as best_avg,
                       COUNT(s.id) as sessions_count,
                       AVG(s.accuracy) as avg_accuracy
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                GROUP BY u.id
                ORDER BY best_avg ASC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [{
                "username": row[0],
                "best_avg": row[1],
                "sessions_count": row[2],
                "avg_accuracy": row[3]
            } for row in rows]

    def update_user_profile(self, user_id, age, gender):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET age = ?, gender = ? WHERE id = ?",
                (age, gender, user_id)
            )
            conn.commit()

    def update_username(self, user_id, new_username):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET username = ? WHERE id = ?",
                    (new_username, user_id)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False