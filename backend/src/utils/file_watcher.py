"""Watchdog: авто-переиндексация при изменении файлов в documents/."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.config import DOCUMENTS_PATH
from src.ingestion.indexer import Indexer, get_indexer
from src.ingestion.parser import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

IGNORED_SUFFIXES = {".tmp", ".part", ".crdownload", ".swp"}


def is_supported_document(path: Path) -> bool:
    """Проверяет, что файл подходит для индексации."""
    suffix = path.suffix.lower()
    if suffix in IGNORED_SUFFIXES:
        return False
    return suffix in SUPPORTED_EXTENSIONS


class DocumentEventHandler(FileSystemEventHandler):
    """Реагирует на изменения в папке documents/."""

    def __init__(
        self,
        indexer: Indexer,
        debounce_seconds: float = 1.0,
    ) -> None:
        super().__init__()
        self.indexer = indexer
        self.debounce_seconds = debounce_seconds
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._schedule_index(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._schedule_index(Path(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._schedule_delete(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        src = Path(event.src_path)
        dest = Path(event.dest_path)

        self._schedule_delete(src)
        self._schedule_index(dest)

    def _schedule_index(self, path: Path) -> None:
        if not is_supported_document(path):
            return

        key = f"index:{path.name}"
        self._debounce(key, self._index_file, path)

    def _schedule_delete(self, path: Path) -> None:
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        key = f"delete:{path.name}"
        self._debounce(key, self._remove_file, path)

    def _debounce(self, key: str, callback, path: Path) -> None:
        with self._lock:
            timer = self._timers.pop(key, None)
            if timer is not None:
                timer.cancel()

            timer = threading.Timer(
                self.debounce_seconds,
                callback,
                args=(path,),
            )
            timer.daemon = True
            self._timers[key] = timer
            timer.start()

    def _index_file(self, path: Path) -> None:
        try:
            if not path.exists() or not is_supported_document(path):
                return

            count = self.indexer.index_file(path)
            logger.info("Indexed %s (%d chunks)", path.name, count)
        except Exception:
            logger.exception("Failed to index %s", path)

    def _remove_file(self, path: Path) -> None:
        try:
            self.indexer.delete_by_source(path.name)
            logger.info("Removed from index: %s", path.name)
        except Exception:
            logger.exception("Failed to remove %s from index", path)

    def cancel_pending(self) -> None:
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()


class DocumentWatcher:
    """Следит за папкой documents/ и переиндексирует файлы автоматически."""

    def __init__(
        self,
        directory: str | Path = DOCUMENTS_PATH,
        indexer: Indexer | None = None,
        debounce_seconds: float = 1.0,
    ) -> None:
        self.directory = Path(directory)
        self.indexer = indexer or get_indexer()
        self.debounce_seconds = debounce_seconds
        self._handler = DocumentEventHandler(self.indexer, debounce_seconds)
        self._observer = Observer()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, *, index_existing: bool = False) -> None:
        """Запускает наблюдение за папкой."""
        if self._running:
            return

        self.directory.mkdir(parents=True, exist_ok=True)

        if index_existing:
            count = self.indexer.index_directory(self.directory)
            logger.info("Initial indexing: %d chunks", count)

        self._observer.schedule(
            self._handler,
            str(self.directory),
            recursive=False,
        )
        self._observer.start()
        self._running = True
        logger.info("Watching documents in %s", self.directory)

    def stop(self) -> None:
        """Останавливает наблюдение."""
        if not self._running:
            return

        self._handler.cancel_pending()
        self._observer.stop()
        self._observer.join(timeout=5)
        self._running = False
        logger.info("Stopped watching %s", self.directory)


_watcher: DocumentWatcher | None = None


def get_watcher(
    directory: str | Path = DOCUMENTS_PATH,
) -> DocumentWatcher:
    """Возвращает один экземпляр watcher на всё приложение."""
    global _watcher
    if _watcher is None:
        _watcher = DocumentWatcher(directory=directory)
    return _watcher
