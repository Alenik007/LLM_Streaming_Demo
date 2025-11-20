from dotenv import load_dotenv
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime, date
import sqlite3
import os
import openai

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "logs.db"

# Настройка OpenAI (переменная окружения OPENAI_API_KEY)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="LLM streaming demo")

# Разрешаем запросы с фронтенда (8080)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # можно сузить до ["http://127.0.0.1:8080"]
    allow_credentials=True,
    allow_methods=["*"],          # разрешаем все методы, в т.ч. OPTIONS, POST
    allow_headers=["*"],          # разрешаем все заголовки
)

# ---------- Модели запросов/ответов ----------

class ChatRequest(BaseModel):
    prompt: str


# ---------- Работа с базой данных ----------

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            output_chars INTEGER NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def log_interaction(prompt: str, response: str, started_at: datetime):
    finished_at = datetime.utcnow()
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    output_chars = len(response)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO interactions (prompt, response, created_at, duration_ms, output_chars)
        VALUES (?, ?, ?, ?, ?)
        """,
        (prompt, response, started_at.isoformat(), duration_ms, output_chars),
    )
    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Общая статистика
    cur.execute("SELECT COUNT(*), COALESCE(SUM(output_chars), 0) FROM interactions")
    total_requests, total_output_chars = cur.fetchone()

    # За сегодня
    today = date.today().isoformat()
    cur.execute(
        "SELECT COUNT(*) FROM interactions WHERE date(created_at) = ?",
        (today,),
    )
    today_requests = cur.fetchone()[0]

    conn.close()
    return {
        "total_requests": total_requests,
        "total_output_chars": total_output_chars,
        "today_requests": today_requests,
    }


def get_last_logs(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, prompt, response, created_at, duration_ms, output_chars
        FROM interactions
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append(
            {
                "id": row[0],
                "prompt": row[1],
                "response": row[2],
                "created_at": row[3],
                "duration_ms": row[4],
                "output_chars": row[5],
            }
        )
    return result


# ---------- Инициализация при старте ----------

@app.on_event("startup")
def on_startup():
    init_db()


# ---------- LLM streaming ----------

def stream_from_llm(prompt: str):
    """
    Стриминговый вызов OpenAI ChatCompletion.
    Возвращаем генератор, который отдает кусочки текста.
    """
    # Здесь можно заменить модель на любую (gpt-4o-mini, gpt-4.1-mini и т.п.)
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    for chunk in response:
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content", "")
            if content:
                yield content


# ---------- HTTP-эндпоинты ----------

@app.post("/api/chat")
def chat(req: ChatRequest):
    """
    Принимает prompt, делает стриминговый запрос к LLM
    и возвращает StreamingResponse.
    """
    started_at = datetime.utcnow()
    prompt = req.prompt
    full_answer_parts = []

    def token_stream():
        # Отдаем токены фронту по мере получения
        nonlocal full_answer_parts
        for chunk in stream_from_llm(prompt):
            full_answer_parts.append(chunk)
            # Важно: yield именно строку (FastAPI сам упакует в байты)
            yield chunk
        # Когда стрим закончен — сохраняем лог
        full_answer = "".join(full_answer_parts)
        log_interaction(prompt, full_answer, started_at)

    return StreamingResponse(token_stream(), media_type="text/plain")


@app.get("/api/stats")
def stats():
    """
    Простая статистика затрат.
    """
    return JSONResponse(get_stats())


@app.get("/api/logs")
def logs(limit: int = 20):
    """
    Список последних запросов.
    """
    return JSONResponse(get_last_logs(limit))
