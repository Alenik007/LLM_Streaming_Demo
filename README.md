# LLM_Streaming_Demo
# LLM Streaming Demo

Минимальное веб-приложение, которое:

- отправляет запросы к LLM (через OpenAI API),
- показывает ответ **в режиме стриминга** (по кусочкам, как в ChatGPT),
- логирует пары «запрос–ответ» в SQLite,
- считает простую статистику по запросам.

Проект сделан для учебных целей: понять, как:
- подключаться к внешнему LLM API,
- реализовать стриминг ответа,
- логировать запросы/ответы и считать базовые метрики.

---

## 🧱 Стек технологий

**Backend:**

- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [OpenAI Python SDK](https://github.com/openai/openai-python) (старый клиент через `openai.ChatCompletion`)
- [python-dotenv](https://github.com/theskumar/python-dotenv) — загрузка ключа из `.env`
- SQLite — простая база для логов

**Frontend:**

- Чистый **HTML + CSS + JavaScript**
- `fetch()` + `ReadableStream` для получения стримингового ответа
- Запуск через стандартный `python -m http.server`

---

## 📁 Структура проекта

```text
LLM_Streaming_Demo/
├── backend/
│   ├── main.py             # FastAPI-приложение, стриминг + логирование + статистика
│   ├── requirements.txt    # зависимости backend'а
│   └── .env                # локальный файл с OPENAI_API_KEY (НЕ в репозитории)
│
├── frontend/
│   ├── index.html          # UI: поле ввода, кнопка, блоки ответа и статистики
│   ├── script.js           # логика запросов + стриминг + обновление статистики/логов
│   └── styles.css          # базовая стилизация
│
├── data/
│   └── logs.db             # SQLite-база с логами (игнорируется в .gitignore)
│
├── .gitignore
└── README.md
