# SmartStudy RAG

RAG-система для ответов на вопросы по учебным материалам (лекции, PDF, DOCX).

**Репозитории:**
- Форк: [Ffgags13/SmartStudy_RAG](https://github.com/Ffgags13/SmartStudy_RAG)
- Оригинал: [skare1111111111111111111111111111111111/SmartStudy_RAG](https://github.com/skare1111111111111111111111111111111111/SmartStudy_RAG)

**Последний коммит:** `1ef950f` — Add FastAPI layer with RAG endpoints in api/

---

## Текущий результат

| Компонент | Статус | Описание |
|-----------|--------|----------|
| Parser | ✅ Готово | PDF, DOCX, TXT → страницы с текстом |
| Chunker | ✅ Готово | Страницы → чанки с overlap |
| Indexer | ✅ Готово | Чанки → эмбеддинги → Chroma |
| Embedder | ✅ Готово | SentenceTransformer (384-dim векторы) |
| Retriever | ✅ Готово | Векторный поиск в Chroma |
| RAG + LLM | ✅ Готово | Промпт → Ollama → ответ с источниками |
| FastAPI | ✅ Готово | `/ask`, `/stats`, `/reindex`, `/health` |
| Тесты | ✅ 27/27 | parser, chunker, indexer, api |
| Frontend | ❌ Нет | Streamlit не реализован |
| Docker | ❌ Нет | docker-compose не настроен |

### Пайплайн данных

```
Документ (PDF/DOCX/TXT)
    ↓  parser.py
Страницы [{page, text, source}]
    ↓  chunker.py
Чанки [{text, source, page, chunk_id, start_char, end_char}]
    ↓  indexer.py + embedding.py
Chroma DB (коллекция "lectures")
    ↓  retriever.py
Похожие чанки по вопросу
    ↓  rag.py + llm.py (Ollama)
Ответ + источники
    ↓  api/main.py
HTTP JSON → клиент
```

---

## Структура проекта

```
SmartStudy_RAG/
├── .gitignore
├── README.md                         # этот файл
│
├── backend/
│   ├── pytest.ini                    # pythonpath = src
│   ├── requirements.txt
│   │
│   ├── src/
│   │   ├── config.py                 # настройки из переменных окружения
│   │   │
│   │   ├── ingestion/                # загрузка и индексация документов
│   │   │   ├── __init__.py
│   │   │   ├── parser.py             # PDF, DOCX, TXT → страницы
│   │   │   ├── chunker.py            # страницы → чанки (~500 символов)
│   │   │   ├── indexer.py            # чанки → Chroma
│   │   │   └── documents/
│   │   │       └── sample.txt        # тестовый документ
│   │   │
│   │   ├── retrieval/                # поиск по индексу
│   │   │   ├── __init__.py
│   │   │   ├── embedding.py          # текст → вектор (all-MiniLM-L6-v2)
│   │   │   └── retriever.py          # поиск в Chroma
│   │   │
│   │   └── api/                      # REST API
│   │       ├── __init__.py
│   │       ├── main.py               # FastAPI app + CORS
│   │       ├── schemas.py            # Pydantic-модели запросов/ответов
│   │       ├── services/
│   │       │   ├── llm.py            # HTTP-клиент Ollama
│   │       │   └── rag.py            # RAG-оркестратор
│   │       └── routes/
│   │           ├── ask.py            # POST /ask
│   │           ├── stats.py          # GET  /stats
│   │           ├── reindex.py        # POST /reindex
│   │           └── health.py         # GET  /health
│   │
│   └── tests/                        # 27 автотестов
│       ├── conftest.py
│       ├── test_parser.py            # 7 тестов
│       ├── test_chunker.py           # 7 тестов
│       ├── test_indexer.py           # 6 тестов
│       ├── test_api.py               # 7 тестов
│       └── fixtures/
│           └── sample.pdf
│
└── frontend/                         # пока пусто
```

---

## API-эндпоинты

| Метод | URL | Тело запроса | Ответ |
|-------|-----|--------------|-------|
| `GET` | `/health` | — | `{status, ollama}` |
| `GET` | `/stats` | — | `{chunks_count, documents[]}` |
| `POST` | `/reindex` | `{path?}` | `{indexed_files, chunks_added, path}` |
| `POST` | `/ask` | `{question, top_k?}` | `{answer, sources[]}` |

Swagger UI: http://localhost:8000/docs

---

## Настройки (config.py / .env)

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Модель эмбеддингов |
| `CHROMA_PATH` | `./chroma_storage` | Путь к векторной БД |
| `DOCUMENTS_PATH` | `./src/ingestion/documents` | Папка с документами |
| `CHUNK_SIZE` | `500` | Размер чанка (символы) |
| `CHUNK_OVERLAP` | `50` | Перекрытие чанков |
| `TOP_K` | `5` | Число чанков при поиске |
| `OLLAMA_URL` | `http://localhost:11434` | URL Ollama |
| `OLLAMA_MODEL` | `llama3` | Модель LLM |
| `LLM_TEMPERATURE` | `0.3` | Температура генерации |
| `LLM_NUM_PREDICT` | `512` | Макс. токенов ответа |
| `CORS_ORIGINS` | `http://localhost:8501,...` | CORS для Streamlit |

---

## Установка и запуск

### Требования

- Python 3.10+
- [Ollama](https://ollama.com/) с моделью `llama3` (для `/ask`)

### Установка

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

### Тесты

```powershell
py -m pytest tests -v
```

Ожидаемый результат: **27 passed**

### Запуск API

```powershell
# Терминал 1: Ollama
ollama run llama3

# Терминал 2: API
cd backend
$env:PYTHONPATH = "src"
py -m uvicorn api.main:app --reload --port 8000
```

### Пример использования

```powershell
# Индексация документов
curl -X POST http://localhost:8000/reindex -H "Content-Type: application/json" -d "{}"

# Статистика
curl http://localhost:8000/stats

# Вопрос
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"Что такое машинное обучение?\"}"
```

### Использование из Python

```python
from ingestion import index_file, index_directory
from retrieval import get_retriever
from api.services.rag import ask
from api.services.llm import get_llm

index_directory()  # индексировать все файлы в documents/

retriever = get_retriever()
llm = get_llm()
result = ask("Что такое нейросеть?", retriever, llm)
print(result["answer"])
print(result["sources"])
```

---

## Git: совместная работа

```powershell
# remotes
origin   → Ffgags13/SmartStudy_RAG      (ваш форк)
upstream → skare.../SmartStudy_RAG       (оригинал)

# workflow
git checkout dev
git pull upstream main
# ... изменения ...
git push origin dev
# merge dev → main → upstream
```

---

## План развития

| Этап | Задача | Статус |
|------|--------|--------|
| 1 | Ingestion (parser, chunker, indexer) | ✅ Готово |
| 2 | Retrieval (embedding, retriever) | ✅ Готово |
| 3 | API (FastAPI + RAG + Ollama) | ✅ Готово |
| 4 | Streamlit frontend | ⏳ Следующий |
| 5 | Docker Compose | ⏳ Планируется |
| 6 | Инкрементальная индексация + CLI | ⏳ Планируется |
| 7 | README, CI, .env.example | ⏳ Частично (этот файл) |

### Этап 4 — Frontend (Streamlit)

```
frontend/
├── app.py
├── requirements.txt
└── components/
    ├── chat.py
    └── sidebar.py
```

### Этап 5 — Docker

```
docker-compose.yml    # ollama + backend + frontend
backend/Dockerfile
frontend/Dockerfile
.env.example
```

---

## История коммитов

| Коммит | Описание |
|--------|----------|
| `6af93ec` | Add ingestion pipeline: parser and chunker modules |
| `5477ebd` | Add pytest suite for parser and chunker modules |
| `fb3ea6f` | retriever (embedding + retriever) |
| `fa67a7e` | Complete ingestion pipeline: indexer and Chroma integration |
| `1ef950f` | Add FastAPI layer with RAG endpoints in api/ |
