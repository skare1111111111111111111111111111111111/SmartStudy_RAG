# Восстановление Docker после нехватки памяти / диска

Если Docker не запускается **даже после удаления проекта** — проблема в Docker Desktop или WSL, не в SmartStudy RAG.

---

## Шаг 1. Полностью остановить Docker и WSL

**PowerShell от администратора:**

```powershell
# закрыть Docker Desktop через трей (Quit Docker Desktop)
wsl --shutdown
taskkill /F /IM "Docker Desktop.exe" 2>$null
taskkill /F /IM com.docker.backend.exe 2>$null
```

Подождите 30 секунд.

---

## Шаг 2. Сброс Docker Desktop (Windows)

1. Откройте **Docker Desktop** (если запускается)  
   → **Settings** → **Troubleshoot** → **Reset to factory defaults**

2. Если Docker **не открывается** — удалите данные вручную:

```powershell
# PowerShell от администратора
wsl --shutdown

# удалить WSL-дистрибутивы Docker (освобождает много места)
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

# удалить кэш Docker Desktop (если папки есть)
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Docker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Docker Desktop" -ErrorAction SilentlyContinue
```

3. **Переустановите** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

4. После установки: **Settings → Resources → WSL Integration** → включите ваш дистрибутив

---

## Шаг 3. Ограничить память WSL (чтобы снова не упасть)

Создайте файл `C:\Users\<ВАШ_ПОЛЬЗОВАТЕЛЬ>\.wslconfig`:

```ini
[wsl2]
memory=4GB
swap=2GB
processors=2
```

Затем:

```powershell
wsl --shutdown
```

Перезапустите WSL / Docker.

**Минимум для SmartStudy RAG:** 8 GB RAM на компьютере, Docker — 4 GB.

---

## Шаг 4. Проверить, что Docker работает

```powershell
docker version
docker compose version
docker run hello-world
```

Все три команды должны выполниться без ошибок.

---

## Шаг 5. Скачать проект БЕЗ git (меньше памяти)

Не используйте `git clone`, если RAM мало. Скачайте ZIP:

1. https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip  
2. Распакуйте в `C:\SmartStudy_RAG`  
3. Запуск:

```powershell
cd C:\SmartStudy_RAG\SmartStudy_RAG-main
$env:COMPOSE_BAKE = "false"
docker compose build backend
docker compose build frontend
docker compose up -d
```

Сборка **по одному сервису** занимает меньше памяти, чем параллельная.

---

## Шаг 6. Запуск SmartStudy RAG (после восстановления Docker)

```powershell
cd C:\SmartStudy_RAG\SmartStudy_RAG-main
$env:COMPOSE_BAKE = "false"
.\run.ps1
```

Или в WSL (лучше не на `/mnt/c/`):

```bash
cd ~/SmartStudy_RAG
export COMPOSE_BAKE=false
sh run.sh
```

---

## Шаг 7. Если сборка снова падает по памяти

```powershell
# только Ollama (лёгкий образ)
docker compose up -d ollama

# подождать 1 мин, затем backend отдельно
docker compose build backend
docker compose up -d backend

# затем frontend
docker compose build frontend
docker compose up -d frontend
```

---

## Сколько места нужно на диске

| Компонент | Размер |
|-----------|--------|
| Docker Desktop | ~1 GB |
| Образы Python (backend + frontend) | ~2–3 GB |
| Ollama + модель llama3 | ~4–5 GB |
| Embedding model (кэш) | ~100 MB |
| **Итого** | **~8–10 GB свободно** |

Проверка места:

```powershell
wsl df -h
```

---

## Если ничего не помогло

1. Перезагрузите компьютер  
2. Освободите **минимум 15 GB** на диске C:  
3. Переустановите Docker Desktop  
4. Не запускайте сборку и браузер с десятками вкладок одновременно  
5. Используйте ZIP + поэтапную сборку (шаг 5–7)

---

## Альтернатива без Docker

Запуск локально (меньше нагрузка, без контейнеров):

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
py -m uvicorn src.api.main:app --port 8000
```

Ollama установите отдельно: https://ollama.com/

Frontend:

```powershell
cd frontend
py -m pip install -r requirements.txt
py -m streamlit run app.py
```
