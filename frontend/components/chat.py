"""Чат: история сообщений и отправка вопросов."""

from __future__ import annotations

import requests
import streamlit as st


def init_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_chat(api_url: str, top_k: int) -> None:
    init_chat_state()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                _render_sources(message["sources"])

    if question := st.chat_input("Задайте вопрос по учебным материалам..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Ищу ответ..."):
                try:
                    response = requests.post(
                        f"{api_url}/ask",
                        json={"question": question, "top_k": top_k},
                        timeout=120,
                    )
                    response.raise_for_status()
                    data = response.json()
                    answer = data.get("answer", "Ответ не получен")
                    sources = data.get("sources", [])
                except requests.RequestException as exc:
                    answer = f"Не удалось получить ответ от API: {exc}"
                    sources = []

            st.markdown(answer)
            if sources:
                _render_sources(sources)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
            }
        )


def _render_sources(sources: list[dict]) -> None:
    with st.expander(f"Источники ({len(sources)})"):
        for index, source in enumerate(sources, start=1):
            page = source.get("page", "?")
            name = source.get("source", "unknown")
            text = source.get("text", "")
            st.markdown(f"**{index}. {name}** (стр. {page})")
            st.caption(text)
