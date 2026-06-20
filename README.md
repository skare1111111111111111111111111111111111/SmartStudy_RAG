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
| Frontend | ✅ Готово | Streamlit чат-интерфейс |
| Docker | ✅ Готово | docker-compose: ollama + backend + frontend |

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
├── .env.example
├── docker-compose.yml
├── run.ps1                           # запуск (Windows)
├── run.sh                            # запуск (Linux/macOS)
├── install.ps1                       # скачать + запустить (Windows)
├── install.sh                        # скачать + запустить (Linux/macOS)
├── README.md
├── documents/                        # вшивается в Docker-образ backend
│   └── sample.txt
│
├── backend/
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── requirements-prod.txt         # зависимости для Docker
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
└── frontend/                         # Streamlit UI
    ├── app.py                        # главная страница
    ├── requirements.txt
    └── components/
        ├── chat.py                   # чат с историей
        └── sidebar.py                # stats, reindex, health
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

## Запуск одной строкой (Docker)

### Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### Скачать и запустить — 1 строка (Windows)

**Вариант A — EXE установщик (release, рекомендуется):**

1. Скачайте [`SmartStudy-Setup.exe`](https://github.com/Ffgags13/SmartStudy_RAG/releases/latest) из Releases
2. Запустите двойным кликом (нужен Docker Desktop)

Или из PowerShell:

```powershell
$exe="$env:TEMP\SmartStudy-Setup.exe"
Invoke-WebRequest "https://github.com/Ffgags13/SmartStudy_RAG/releases/latest/download/SmartStudy-Setup.exe" -OutFile $exe
& $exe
```

**Без GitHub** (локальная копия репозитория):

```powershell
SmartStudy-Setup.exe --local "C:\programming\Dev\projects\Smart_Study\smartstudy-rag"
```

**Вариант B — только Docker-образы (скрипт, мало RAM):**

```powershell
irm https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/install-images.ps1 | iex
```

**Вариант C — ZIP + сборка образов локально:**

```powershell
irm https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/install.ps1 | iex
```

**Уже скачано — только запуск (pull образов):**

```powershell
cd C:\SmartStudy_RAG; $env:COMPOSE_BAKE="false"; docker compose pull; docker compose up -d
```

Образы: `ghcr.io/ffgags13/smartstudy-rag-backend` и `ghcr.io/ffgags13/smartstudy-rag-frontend`

> **Первый запуск pull:** образы собираются в GitHub Actions. Если `pull` пишет *not found* — один раз добавьте workflow: скопируйте [`scripts/ghcr-docker-publish.yml`](scripts/ghcr-docker-publish.yml) в `.github/workflows/docker-publish.yml` на GitHub (или `gh auth refresh -s workflow` и push). Затем сделайте пакеты **Public** в [Packages](https://github.com/Ffgags13?tab=packages).

UI: http://localhost:8501 | Логи: `docker compose logs -f backend`

### Linux / macOS
```bash
git clone --depth 1 https://github.com/Ffgags13/SmartStudy_RAG.git SmartStudy_RAG && cd SmartStudy_RAG && sh run.sh
```

### Только запуск (если проект уже скачан)

```powershell
docker compose up --build -d
```

### Что происходит автоматически

При первом запуске контейнер **backend** сам:
1. Ждёт Ollama
2. Скачивает модель `llama3`
3. Скачивает модель эмбеддингов
4. Индексирует документы из образа (`sample.txt` уже внутри)

Документы, код backend и frontend **упакованы в Docker-образы** — монтировать папки не нужно.

### Адреса

| Сервис | URL |
|--------|-----|
| Streamlit UI | http://localhost:8501 |
| API Swagger | http://localhost:8000/docs |

Первый запуск занимает **5–15 минут** (скачивание моделей). Прогресс:

```powershell
docker compose logs -f backend
```

### Если Docker не запускается (Windows)

Инструкция для **Windows / PowerShell** (без WSL):  
[docs/DOCKER_RECOVERY.md](docs/DOCKER_RECOVERY.md)

Кратко:

```powershell
# PowerShell от администратора — сброс данных Docker
taskkill /F /IM "Docker Desktop.exe" 2>$null
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Docker Desktop" -ErrorAction SilentlyContinue
```

Переустановите Docker Desktop, скачайте проект ZIP-архивом:  
https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip

### Если сборка падает с `failed to execute bake`

```bash
export COMPOSE_BAKE=false
docker compose build --no-cache
docker compose up -d
```

Или клонируйте проект **внутри WSL**, не на `/mnt/c/`:

```bash
cd ~
git clone --depth 1 https://github.com/Ffgags13/SmartStudy_RAG.git
cd SmartStudy_RAG
sh run.sh
```

### Если `docker compose` не найден в WSL

1. Установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Settings → Resources → **WSL Integration** → включите ваш дистрибутив
3. Не ставьте `docker.io` через apt — используйте Docker Desktop

---

```powershell
docker compose ps
docker compose logs -f backend
docker compose down
docker compose down -v    # удалить индекс и модели
```

### Свои документы (опционально)

По умолчанию в образ встроен `sample.txt`. Чтобы добавить свои файлы без пересборки, можно временно смонтировать папку — добавьте в `docker-compose.yml` в сервис `backend`:

```yaml
volumes:
  - ./my-docs:/data/documents
```

Затем: `docker compose up --build -d` и `POST /reindex`.

---

## Установка и запуск (локально, без Docker)

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

### Запуск Frontend (Streamlit)

```powershell
# Терминал 3: Frontend (API должен быть запущен)
cd frontend
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Откройте http://localhost:8501

### Проверка всей системы

1. Запустите Ollama: `ollama run llama3`
2. Запустите API (терминал 2, см. выше)
3. Запустите Streamlit (терминал 3)
4. В боковой панели нажмите **Переиндексировать**
5. Задайте вопрос, например: «Что такое машинное обучение?»
6. Проверьте ответ и блок **Источники**


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
| 4 | Streamlit frontend | ✅ Готово |
| 5 | Docker Compose | ✅ Готово |
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
