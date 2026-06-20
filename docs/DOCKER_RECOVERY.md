# Docker на Windows — восстановление и запуск SmartStudy RAG

Инструкция **только для Windows** (PowerShell). WSL и Linux-терминал не нужны.

Если Docker не запускается **после удаления проекта** — повреждён Docker Desktop, а не SmartStudy RAG.

---

## Требования

| Ресурс | Минимум |
|--------|---------|
| Windows 10/11 64-bit | Pro, Enterprise или Home с WSL2 |
| RAM | 8 GB (лучше 16 GB) |
| Свободно на диске C: | **15 GB** |
| Docker Desktop | последняя версия |

---

## Часть 1. Восстановить Docker Desktop

### 1.1 Остановить Docker

1. Правый клик по иконке Docker в трее → **Quit Docker Desktop**
2. **PowerShell от администратора:**

```powershell
taskkill /F /IM "Docker Desktop.exe" 2>$null
taskkill /F /IM "com.docker.backend.exe" 2>$null
taskkill /F /IM "com.docker.service.exe" 2>$null
```

Подождите 30 секунд.

### 1.2 Сброс через интерфейс (если Docker открывается)

1. Запустите **Docker Desktop**
2. **Settings** (шестерёнка) → **Troubleshoot**
3. **Reset to factory defaults** → подтвердите
4. Перезагрузите компьютер

### 1.3 Сброс вручную (если Docker не открывается)

**PowerShell от администратора:**

```powershell
# остановить службы Docker
Stop-Service -Name com.docker.service -ErrorAction SilentlyContinue
Stop-Service -Name docker -ErrorAction SilentlyContinue

# удалить данные Docker Desktop
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Docker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Docker Desktop" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:ProgramData\Docker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:ProgramData\DockerDesktop" -ErrorAction SilentlyContinue
```

Перезагрузите компьютер.

### 1.4 Переустановка Docker Desktop

1. **Параметры Windows → Приложения** → удалите **Docker Desktop**
2. Скачайте заново: https://www.docker.com/products/docker-desktop/
3. Установите, перезагрузите ПК
4. Запустите Docker Desktop, дождитесь статуса **Engine running**

### 1.5 Ограничить память Docker (чтобы не упасть снова)

Docker Desktop → **Settings → Resources**:

- **Memory:** 4 GB (если RAM 8 GB) или 6 GB (если RAM 16 GB)
- **Disk image size:** минимум 40 GB
- **Apply & Restart**

### 1.6 Проверка

**PowerShell** (обычный, не обязательно админ):

```powershell
docker version
docker compose version
docker run --rm hello-world
```

Все три команды должны завершиться без ошибок.

---

## Часть 2. Одна строка — скачать и запустить

### A) Только Docker-образы (без git, без ZIP, без сборки)

**PowerShell:**

```powershell
irm https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/install-images.ps1 | iex
```

Inline:

```powershell
$d="C:\SmartStudy_RAG"; mkdir -Force $d | Out-Null; irm "https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/docker-compose.pull.yml" -OutFile "$d\docker-compose.yml"; cd $d; docker compose pull; docker compose up -d
```

Скачиваются готовые образы:
- `ghcr.io/ffgags13/smartstudy-rag-backend:latest`
- `ghcr.io/ffgags13/smartstudy-rag-frontend:latest`
- `ollama/ollama:latest`

### B) ZIP + локальная сборка

```powershell
irm https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/install.ps1 | iex
```

### Если `pull` пишет "denied", "not found" или **500 Internal Server Error**

**500 на Windows** часто означает одно из двух:
1. **Образа ещё нет в GHCR** (GitHub Actions не собирал его) — Docker Desktop иногда отвечает 500 вместо понятной ошибки
2. **Docker Engine сломан** — см. Часть 1 (перезапуск / reset)

**Быстрое решение — ZIP + сборка (работает всегда):**

```powershell
irm https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/install.ps1 | iex
```

Или обновлённый `install-images.ps1` — он сам переключится на ZIP, если pull не удался:

```powershell
irm https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/install-images.ps1 | iex
```

**Чтобы pull заработал для всех**, один раз опубликуйте образы:
1. На GitHub: **Add file** → `.github/workflows/docker-publish.yml` → содержимое из [`scripts/ghcr-docker-publish.yml`](https://github.com/Ffgags13/SmartStudy_RAG/blob/main/scripts/ghcr-docker-publish.yml)
2. Commit в `main` → дождитесь Actions (~10 мин)
3. Пакеты **Public**: https://github.com/Ffgags13?tab=packages

Проверка Docker:

```powershell
docker info
docker pull hello-world
docker pull ghcr.io/ffgags13/smartstudy-rag-backend:latest
```

---

## Часть 3. Скачать вручную (если одна строка не сработала)

1. https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip  
2. Распаковать в `C:\SmartStudy_RAG`  
3. Запуск — см. Часть 3 ниже (поэтапная сборка)

Откройте **PowerShell**, не WSL:

```powershell
cd C:\SmartStudy_RAG\SmartStudy_RAG-main

# отключить bake (исправляет ошибку "failed to execute bake")
$env:COMPOSE_BAKE = "false"

# поэтапная сборка — меньше нагрузка на RAM
docker compose up -d ollama
Start-Sleep -Seconds 30
docker compose build backend
docker compose up -d backend
docker compose build frontend
docker compose up -d frontend
```

Или одной командой (если RAM достаточно):

```powershell
cd C:\SmartStudy_RAG\SmartStudy_RAG-main
$env:COMPOSE_BAKE = "false"
.\run.ps1
```

### Скачать модель LLM (первый раз, ~4 GB)

```powershell
docker compose exec ollama ollama pull llama3
```

Если в `run.ps1` / entrypoint модель уже тянется автоматически — этот шаг может не понадобиться. При ошибках `/ask` выполните команду выше вручную.

### Открыть в браузере

| Сервис | URL |
|--------|-----|
| Streamlit (чат) | http://localhost:8501 |
| API (Swagger) | http://localhost:8000/docs |

### Логи (если что-то не работает)

```powershell
docker compose ps
docker compose logs -f backend
```

Первый запуск: **5–15 минут** (модели + индексация).

---

## Часть 4. Частые ошибки на Windows

### `failed to execute bake`

```powershell
$env:COMPOSE_BAKE = "false"
docker compose build --no-cache backend
docker compose build --no-cache frontend
docker compose up -d
```

### Docker Desktop: "Engine stopped" / не запускается

1. Перезагрузка ПК  
2. Часть 1 (сброс)  
3. **Windows Update** — установите все обновления  
4. Включите виртуализацию в BIOS (Intel VT-x / AMD-V)

### Нехватка места на диске C:

```powershell
# сколько свободно
Get-PSDrive C | Select-Object Used, Free

# очистить неиспользуемые образы Docker
docker system prune -a --volumes
```

Подтвердите `y`. Освободит несколько GB.

### Порт занят (8000 или 8501)

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :8501
# завершить процесс по PID:
taskkill /F /PID <номер>
```

---

## Часть 5. Альтернатива — без Docker (только Windows)

Если Docker не удаётся починить:

**Терминал 1 — Ollama для Windows:**  
https://ollama.com/download → установить → `ollama run llama3`

**Терминал 2 — Backend:**

```powershell
cd C:\SmartStudy_RAG\SmartStudy_RAG-main\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
py -m uvicorn src.api.main:app --reload --port 8000
```

**Терминал 3 — Frontend:**

```powershell
cd C:\SmartStudy_RAG\SmartStudy_RAG-main\frontend
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

UI: http://localhost:8501

---

## Чеклист

- [ ] Docker Desktop: **Engine running**
- [ ] `docker run hello-world` — OK
- [ ] На C: свободно **15+ GB**
- [ ] Проект скачан (ZIP или git)
- [ ] `$env:COMPOSE_BAKE = "false"`
- [ ] `docker compose ps` — 3 контейнера running
- [ ] http://localhost:8501 открывается
