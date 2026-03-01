import sqlite3
from datetime import datetime
import json
import urllib.request
import urllib.parse
import urllib.error


class Database:
    def __init__(self, db_name="neurospint.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    avg_reaction REAL,
                    min_reaction REAL,
                    max_reaction REAL,
                    std_deviation REAL,
                    total_wrong INTEGER,
                    difficulty TEXT DEFAULT 'medium',
                    trials_data TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Миграция: difficulty
            cursor.execute("PRAGMA table_info(sessions)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'difficulty' not in cols:
                cursor.execute("ALTER TABLE sessions ADD COLUMN difficulty TEXT DEFAULT 'medium'")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_session (
                    user_id INTEGER PRIMARY KEY,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            conn.commit()

    def _row_to_user(self, row):
        return {
            "id": row[0], "username": row[1],
            "age": row[2], "gender": row[3], "created_at": row[4]
        }

    def create_user(self, username):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
                conn.commit()
                user_id = cursor.lastrowid
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
            return self._row_to_user(row) if row else None

    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, age, gender, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def username_exists(self, username):
        """Проверяет никнейм глобально по всей БД."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            return cursor.fetchone()[0] > 0

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
            return self.get_user_by_id(row[0]) if row else None

    def clear_active_user(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_session")
            conn.commit()

    def delete_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM active_session WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

    def save_session(self, user_id, stats, trials_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions
                (user_id, avg_reaction, min_reaction, max_reaction,
                 std_deviation, total_wrong, difficulty, trials_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                stats['avg_reaction_time'],
                stats['min_reaction'],
                stats['max_reaction'],
                stats['std_deviation'],
                stats['total_wrong'],
                stats.get('difficulty', 'medium'),
                json.dumps(trials_data, ensure_ascii=False)
            ))
            conn.commit()

    def get_user_sessions(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, avg_reaction, min_reaction, max_reaction,
                       std_deviation, total_wrong, difficulty, trials_data
                FROM sessions WHERE user_id = ? ORDER BY date DESC
            ''', (user_id,))
            return [{
                "date": r[0],
                "avg_reaction": r[1],
                "min_reaction": r[2],
                "max_reaction": r[3],
                "std_deviation": r[4],
                "total_wrong": r[5],
                "difficulty": r[6] or "medium",
                "trials_data": json.loads(r[7]) if r[7] else []
            } for r in cursor.fetchall()]

    def get_leaderboard(self, limit=20):
        """Упрощённый метод для обратной совместимости."""
        return self.get_leaderboard_full(limit=limit)

    def get_leaderboard_full(self, gender=None, age_from=None, age_max=None, difficulty=None, limit=100):
        """
        Расширенный метод с фильтрами:
          gender    — 'Мужчина' / 'Женщина' / None (все)
          age_from  — минимальный возраст (int, включительно) / None (все)
          age_max   — максимальный возраст (int, включительно) / None (все)
          difficulty — 'easy'/'medium'/'hard' / None (все)
          limit     — макс. количество строк
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            where_user  = []
            where_sess  = []
            params_user = []
            params_sess = []

            if gender:
                where_user.append("u.gender = ?")
                params_user.append(gender)

            if age_from is not None:
                where_user.append("u.age IS NOT NULL AND u.age >= ?")
                params_user.append(age_from)

            if age_max is not None:
                where_user.append("u.age IS NOT NULL AND u.age <= ?")
                params_user.append(age_max)

            if difficulty:
                where_sess.append("s.difficulty = ?")
                params_sess.append(difficulty)

            user_cond = ("AND " + " AND ".join(where_user)) if where_user else ""
            sess_cond = ("AND " + " AND ".join(where_sess)) if where_sess else ""

            sql = f"""
                SELECT
                    u.username,
                    u.age,
                    u.gender,
                    AVG(s.avg_reaction)  AS avg_account,
                    COUNT(s.id)          AS sessions_count,
                    MIN(s.min_reaction)  AS best_ever,
                    SUM(CASE WHEN s.total_wrong = 0 THEN 1 ELSE 0 END) AS perfect_sessions
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE 1=1 {user_cond} {sess_cond}
                GROUP BY u.id
                LIMIT ?
            """
            params = params_user + params_sess + [limit]
            cursor.execute(sql, params)

            return [{
                "username":         r[0],
                "age":              r[1],
                "gender":           r[2],
                "avg_account":      round(r[3], 2) if r[3] else None,
                "sessions_count":   r[4],
                "best_ever":        r[5],
                "perfect_sessions": r[6],
            } for r in cursor.fetchall()]


# ─────────────────────────────────────────────────────────────────────────────
# Онлайн-клиент для работы с сервером (server.py)
# Используется для загрузки таблицы лидеров в реальном времени.
# При недоступности сервера автоматически откатывается к локальным данным.
# ─────────────────────────────────────────────────────────────────────────────

class OnlineDatabase:
    """
    Обёртка над Database с поддержкой онлайн-сервера.
    - Сервер запускается автоматически через main.py
    - Таблица лидеров читается с сервера
    - Сессии пишутся локально + синхронизируются на сервер
    - При недоступности сервера — тихий fallback на локальные данные
    """

    SERVER_URL = "http://localhost:8000"

    def __init__(self, db_name="neurospint.db", server_url: str = None):
        # Инициализируем атрибуты НАПРЯМУЮ через object.__setattr__
        # чтобы избежать рекурсии через __getattr__
        object.__setattr__(self, '_local', Database(db_name))
        object.__setattr__(self, '_online', False)
        if server_url:
            object.__setattr__(self, 'SERVER_URL', server_url.rstrip("/"))
        # Проверяем сервер
        object.__setattr__(self, '_online', self._check_server())

    def __getattr__(self, name):
        """Проксируем все неизвестные атрибуты в локальную БД."""
        # _local уже точно инициализирован через object.__setattr__
        return getattr(object.__getattribute__(self, '_local'), name)

    def _check_server(self) -> bool:
        try:
            url = object.__getattribute__(self, 'SERVER_URL')
            with urllib.request.urlopen(f"{url}/health", timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _recheck_if_needed(self):
        """Повторно проверяет сервер, если сейчас оффлайн."""
        if not object.__getattribute__(self, '_online'):
            result = self._check_server()
            object.__setattr__(self, '_online', result)

    def _post_json(self, path: str, payload: dict):
        url = object.__getattribute__(self, 'SERVER_URL')
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    def _get_json(self, path: str) -> list:
        url = object.__getattribute__(self, 'SERVER_URL')
        with urllib.request.urlopen(f"{url}{path}", timeout=5) as resp:
            return json.loads(resp.read())

    def save_session(self, user_id, stats, trials_data):
        local = object.__getattribute__(self, '_local')
        # Всегда сохраняем локально
        local.save_session(user_id, stats, trials_data)

        user = local.get_user_by_id(user_id)
        if not user:
            return

        # Пробуем синхронизировать на сервер
        try:
            self._post_json("/sessions", {
                "username":      user["username"],
                "avg_reaction":  stats["avg_reaction_time"],
                "min_reaction":  stats["min_reaction"],
                "max_reaction":  stats["max_reaction"],
                "std_deviation": stats["std_deviation"],
                "total_wrong":   stats["total_wrong"],
                "difficulty":    stats.get("difficulty", "medium"),
                "trials_data":   trials_data,
            })
            object.__setattr__(self, '_online', True)
        except Exception:
            object.__setattr__(self, '_online', False)

    def get_leaderboard_full(self, gender=None, age_from=None, age_max=None,
                              difficulty=None, limit=100):
        # Если оффлайн — пробуем переподключиться
        self._recheck_if_needed()

        if object.__getattribute__(self, '_online'):
            try:
                url_params = {"limit": limit}
                if gender:     url_params["gender"]     = gender
                if age_from:   url_params["age_from"]   = age_from
                if age_max:    url_params["age_to"]      = age_max
                if difficulty: url_params["difficulty"] = difficulty
                qs = urllib.parse.urlencode(url_params)
                data = self._get_json(f"/leaderboard?{qs}")
                return data
            except Exception:
                object.__setattr__(self, '_online', False)

        # Fallback на локальные данные
        local = object.__getattribute__(self, '_local')
        return local.get_leaderboard_full(
            gender=gender, age_from=age_from, age_max=age_max,
            difficulty=difficulty, limit=limit
        )

    def get_leaderboard(self, limit=20):
        return self.get_leaderboard_full(limit=limit)

    @property
    def is_online(self) -> bool:
        return object.__getattribute__(self, '_online')
