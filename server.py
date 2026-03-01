"""
НейроСпринт — онлайн-сервер таблицы лидеров
============================================
Запуск вручную
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import json
import os
from datetime import datetime

app = FastAPI(title="НейроСпринт API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Используем ТУ ЖЕ БД что и клиент — файл лежит рядом со скриптом
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neurospint.db")


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                age INTEGER,
                gender TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
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
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()


init_db()


# ── Pydantic-модели ──────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    age: Optional[int] = None
    gender: Optional[str] = None


class SessionCreate(BaseModel):
    username: str
    avg_reaction: float
    min_reaction: float
    max_reaction: float
    std_deviation: float
    total_wrong: int
    difficulty: str = "medium"
    trials_data: list = []


# ── Эндпоинты ────────────────────────────────────────────────────────────────

@app.post("/users", summary="Создать пользователя")
def create_user(data: UserCreate):
    try:
        with get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (username, age, gender) VALUES (?, ?, ?)",
                (data.username, data.age, data.gender)
            )
            conn.commit()
            return {"id": c.lastrowid, "username": data.username}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Пользователь уже существует")


@app.get("/users/{username}", summary="Получить пользователя")
def get_user(username: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, age, gender, created_at FROM users WHERE username = ?", (username,))
        row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"id": row[0], "username": row[1], "age": row[2], "gender": row[3], "created_at": row[4]}


@app.post("/sessions", summary="Сохранить сессию тренировки")
def save_session(data: SessionCreate):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (data.username,))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        user_id = row[0]
        c.execute("""
            INSERT INTO sessions
            (user_id, avg_reaction, min_reaction, max_reaction,
             std_deviation, total_wrong, difficulty, trials_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, data.avg_reaction, data.min_reaction, data.max_reaction,
            data.std_deviation, data.total_wrong, data.difficulty,
            json.dumps(data.trials_data, ensure_ascii=False)
        ))
        conn.commit()
    return {"status": "ok", "session_id": c.lastrowid}


@app.get("/leaderboard", summary="Таблица лидеров с фильтрами")
def leaderboard(
    gender: Optional[str] = Query(None, description="Мужчина / Женщина"),
    age_from: Optional[int] = Query(None, ge=0, description="Возраст от (включительно)"),
    age_to: Optional[int] = Query(None, le=120, description="Возраст до (включительно)"),
    difficulty: Optional[str] = Query(None, description="easy / medium / hard"),
    limit: int = Query(100, le=500),
):
    where_user, where_sess = [], []
    params_user, params_sess = [], []

    if gender:
        where_user.append("u.gender = ?")
        params_user.append(gender)
    if age_from is not None:
        where_user.append("u.age IS NOT NULL AND u.age >= ?")
        params_user.append(age_from)
    if age_to is not None:
        where_user.append("u.age IS NOT NULL AND u.age <= ?")
        params_user.append(age_to)
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
        ORDER BY avg_account ASC
        LIMIT ?
    """
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(sql, params_user + params_sess + [limit])
        rows = c.fetchall()

    return [
        {
            "username": r[0], "age": r[1], "gender": r[2],
            "avg_account": round(r[3], 2) if r[3] else None,
            "sessions_count": r[4],
            "best_ever": r[5], "perfect_sessions": r[6],
        }
        for r in rows
    ]


@app.get("/health", summary="Проверка работоспособности сервера")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
