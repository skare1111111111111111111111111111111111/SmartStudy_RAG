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

## Часть 2. Скачать проект (Windows, без git)

Если при `git clone` не хватило памяти — используйте ZIP:

1. Скачайте: https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip  
2. Правый клик → **Извлечь всё** → `C:\SmartStudy_RAG`
3. Папка проекта: `C:\SmartStudy_RAG\SmartStudy_RAG-main`

---

## Часть 3. Запуск SmartStudy RAG (PowerShell)

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
