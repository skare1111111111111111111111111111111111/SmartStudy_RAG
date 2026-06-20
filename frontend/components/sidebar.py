"""Боковая панель: статус API, статистика, переиндексация."""

from __future__ import annotations

import os

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000")


def render_sidebar() -> str:
    st.sidebar.title("SmartStudy RAG")
    api_url = st.sidebar.text_input("URL API", value=DEFAULT_API_URL).rstrip("/")

    _render_health(api_url)
    st.sidebar.divider()
    _render_stats(api_url)
    st.sidebar.divider()
    _render_reindex(api_url)

    return api_url


def _render_health(api_url: str) -> None:
    if st.sidebar.button("Проверить API", use_container_width=True):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            response.raise_for_status()
            data = response.json()
            ollama = data.get("ollama", "unknown")
            if ollama == "available":
                st.sidebar.success("API: OK | Ollama: доступна")
            else:
                st.sidebar.warning("API: OK | Ollama: недоступна")
        except requests.RequestException as exc:
            st.sidebar.error(f"API недоступен: {exc}")


def _render_stats(api_url: str) -> None:
    try:
        response = requests.get(f"{api_url}/stats", timeout=10)
        response.raise_for_status()
        data = response.json()
        st.sidebar.metric("Чанков в базе", data.get("chunks_count", 0))
        documents = data.get("documents", [])
        if documents:
            st.sidebar.caption("Документы:")
            for doc in documents:
                st.sidebar.write(f"• {doc}")
        else:
            st.sidebar.caption("Документы не проиндексированы")
    except requests.RequestException:
        st.sidebar.metric("Чанков в базе", "—")


def _render_reindex(api_url: str) -> None:
    st.sidebar.subheader("Индексация")
    custom_path = st.sidebar.text_input(
        "Путь (необязательно)",
        placeholder="Оставьте пустым для documents/",
    )

    if st.sidebar.button("Переиндексировать", use_container_width=True):
        payload = {"path": custom_path.strip()} if custom_path.strip() else {}
        try:
            with st.sidebar.spinner("Индексация..."):
                response = requests.post(
                    f"{api_url}/reindex",
                    json=payload,
                    timeout=300,
                )
                response.raise_for_status()
            data = response.json()
            st.sidebar.success(
                f"Готово: {data['chunks_added']} чанков "
                f"из {data['indexed_files']} файлов"
            )
            st.rerun()
        except requests.RequestException as exc:
            st.sidebar.error(f"Ошибка индексации: {exc}")
