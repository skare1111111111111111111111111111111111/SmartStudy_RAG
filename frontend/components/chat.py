"""Чат: история сообщений и отправка вопросов."""

from __future__ import annotations

import os

import requests
import streamlit as st

ASK_TIMEOUT = int(os.getenv("ASK_TIMEOUT", "180"))


def _extract_top_k_limit(error: requests.RequestException) -> int | None:
    response = getattr(error, "response", None)
    if response is None or response.status_code != 422:
        return None

    try:
        payload = response.json()
    except ValueError:
        return None

    for item in payload.get("detail", []):
        loc = item.get("loc", [])
        if loc and loc[-1] == "top_k":
            limit = (item.get("ctx") or {}).get("le")
            if isinstance(limit, (int, float)):
                return int(limit)
    return None


def _format_request_error(error: requests.RequestException) -> str:
    response = getattr(error, "response", None)
    if response is None:
        return str(error)

    try:
        payload = response.json()
    except ValueError:
        return str(error)

    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            msg = first.get("msg")
            if isinstance(msg, str):
                return msg
    return str(error)


def _build_ask_payload(question: str, top_k: int, answer_language: str | None) -> dict:
    payload = {"question": question, "top_k": top_k}
    if answer_language:
        payload["answer_language"] = answer_language
    return payload

def init_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_chat(api_url: str, top_k: int, answer_language: str | None = None) -> None:
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
                    payload = _build_ask_payload(question, top_k, answer_language)
                    response = requests.post(
                        f"{api_url}/ask",
                        json=payload,
                        timeout=ASK_TIMEOUT,
                    )
                    response.raise_for_status()
                    data = response.json()
                    answer = data.get("answer", "Ответ не получен")
                    sources = data.get("sources", [])
                except requests.Timeout:
                    answer = (
                        "Запрос занял слишком много времени. "
                        "Уменьшите «Чанков для поиска» до 5–10 или подождите — "
                        "первый ответ после запуска может быть медленным."
                    )
                    sources = []
                except requests.RequestException as exc:
                    limit = _extract_top_k_limit(exc)
                    if limit is not None and top_k > limit:
                        try:
                            retry_payload = _build_ask_payload(question, limit, answer_language)
                            retry_response = requests.post(
                                f"{api_url}/ask",
                                json=retry_payload,
                                timeout=ASK_TIMEOUT,
                            )
                            retry_response.raise_for_status()
                            retry_data = retry_response.json()
                            answer = retry_data.get("answer", "Ответ не получен")
                            sources = retry_data.get("sources", [])
                            st.caption(f"top_k автоматически снижен до {limit} (лимит API).")
                        except requests.RequestException as retry_exc:
                            answer = (
                                "Не удалось получить ответ от API: "
                                f"{_format_request_error(retry_exc)}"
                            )
                            sources = []
                    else:
                        answer = (
                            "Не удалось получить ответ от API: "
                            f"{_format_request_error(exc)}"
                        )
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
