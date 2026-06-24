# SmartStudy RAG

**RAG-система для вопросов по учебным материалам (PDF, DOCX, TXT) с веб-интерфейсом и локальной LLM.**

Репозитории:
- Форк: [Ffgags13/SmartStudy_RAG](https://github.com/Ffgags13/SmartStudy_RAG)
- Оригинал: [skare1111111111111111111111111111111111/SmartStudy_RAG](https://github.com/skare1111111111111111111111111111111111/SmartStudy_RAG)

---

## Быстрый обзор

SmartStudy RAG индексирует лекции и методички, ищет релевантные фрагменты и генерирует ответ через **Ollama**.

**Возможности:**

- 📄 Парсинг **PDF / DOCX / TXT** и автоматическая индексация
- 🔍 Векторный поиск в **Chroma** (эмбеддинги MiniLM, 384-dim)
- 🤖 Ответы через **Ollama** (`llama3.2:1b` по умолчанию)
- 🖥️ **Streamlit UI** — чат, загрузка файлов, переиндексация
- 🐳 **Docker Compose** — Ollama + backend + frontend одной командой
- ⚡ Оптимизация под слабое железо (лимит контекста LLM, кэш, async API)

| Сервис | URL |
|--------|-----|
| UI | http://localhost:8501 |
| API / Swagger | http://localhost:8000/docs |

---

## Запуск

### Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (рекомендуется)
- или Python 3.10+ и [Ollama](https://ollama.com/)

### Одна команда (Windows)

```powershell
irm https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/install-images.ps1 | iex
```

**Уже скачано:**

```powershell
docker compose pull; docker compose up -d
```

### Linux / macOS

```bash
git clone --depth 1 https://github.com/Ffgags13/SmartStudy_RAG.git && cd SmartStudy_RAG && sh run.sh
```

### EXE-установщик

Скачайте из [Releases](https://github.com/Ffgags13/SmartStudy_RAG/releases/latest): `SmartStudy-Setup-PS.exe` (рекомендуется).

> Первый запуск: **5–15 мин** (скачивание моделей Ollama и эмбеддингов). Прогресс: `docker compose logs -f backend`

Подробнее: [docs/DOCKER_RECOVERY.md](docs/DOCKER_RECOVERY.md)

---

## Использование

1. Откройте http://localhost:8501
2. Загрузите PDF/DOCX/TXT в боковой панели **или** положите файлы в `data/documents/`
3. Нажмите **Переиндексировать** (если база пуста)
4. Задайте вопрос в чате

Слайдер «Чанков для поиска» задаёт число источников; в LLM уходит **топ-6** самых релевантных фрагментов.

---

## Архитектура

### Пайплайн данных

```
Документ (PDF/DOCX/TXT)
    ↓  parser.py
Страницы [{page, text, source}]
    ↓  chunker.py
Чанки [{text, source, page, chunk_id}]
    ↓  indexer.py + embedding.py
Chroma DB (коллекция "lectures")
    ↓  retriever.py
Похожие чанки по вопросу
    ↓  rag.py + llm/client.py (Ollama)
Ответ + источники
    ↓  api/main.py  →  Streamlit UI
```

### Компоненты

| Модуль | Файл | Назначение |
|--------|------|------------|
| **Parser** | `backend/src/ingestion/parser.py` | PDF/DOCX/TXT → страницы |
| **Chunker** | `backend/src/ingestion/chunker.py` | Страницы → чанки с overlap |
| **Indexer** | `backend/src/ingestion/indexer.py` | Чанки → эмбеддинги → Chroma |
| **Embedder** | `backend/src/retrieval/embedding.py` | Текст → вектор (MiniLM) |
| **Retriever** | `backend/src/retrieval/retriever.py` | Семантический поиск в Chroma |
| **RAG** | `backend/src/api/services/rag.py` | Ранжирование чанков + вызов LLM |
| **LLM** | `backend/src/llm/client.py` | HTTP-клиент Ollama |
| **API** | `backend/src/api/routes/` | REST: ask, stats, reindex, upload, health |
| **UI** | `frontend/` | Streamlit: чат, sidebar, upload |

### API

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/health` | Статус API и Ollama |
| `GET` | `/stats` | Число чанков и список документов |
| `POST` | `/reindex` | Переиндексация папки/файла |
| `POST` | `/documents/upload` | Загрузка и индексация файла |
| `POST` | `/ask` | `{question, top_k?, answer_language?}` → ответ + источники |

---

## Конфигурация (`.env`)

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `OLLAMA_MODEL` | `llama3.2:1b` | Модель LLM |
| `DOCUMENTS_PATH` | `data/documents` | Папка с документами |
| `CHROMA_PATH` | `data/chroma` | Векторная БД (локально, не в Git) |
| `CHUNK_SIZE` | `400` | Размер чанка (символы) |
| `TOP_K` | `5` | Чанков для поиска (UI) |
| `LLM_TOP_K` | `6` | Чанков для LLM |
| `LLM_MAX_CONTEXT_CHARS` | `2500` | Лимит контекста в промпте |

Полный список: [.env.example](.env.example)

---

## Локальная разработка

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:PYTHONPATH = "."
py -m pytest tests -q          # 27+ тестов
py -m uvicorn src.api.main:app --port 8000
```

```powershell
cd frontend
py -m streamlit run app.py
```

---

## Git workflow

```powershell
git fetch upstream
git checkout dev
git merge upstream/main
# ... изменения ...
git push origin dev
git checkout main && git merge dev && git push origin main
git push upstream main
```

---

## Contributors

- [IIIBBS](https://github.com/skare1111111111111111111111111111111111) — оригинальный автор
- [Ffgags13](https://github.com/Ffgags13) — форк, Docker, release, оптимизация

---

## Лицензия

MIT (см. репозиторий)
