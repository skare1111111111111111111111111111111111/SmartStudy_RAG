"""SmartStudy RAG — веб-интерфейс для вопросов по учебным материалам."""

from __future__ import annotations

import os

import streamlit as st

from components.chat import render_chat
from components.sidebar import render_sidebar

DEFAULT_TOP_K = int(os.getenv("TOP_K", "5"))
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "100"))

st.set_page_config(
    page_title="SmartStudy RAG",
    page_icon="📚",
    layout="wide",
)

st.title("📚 SmartStudy RAG")
st.caption("Задавайте вопросы по загруженным лекциям и методичкам")

api_url = render_sidebar()

col_settings, col_info = st.columns([1, 3])
with col_settings:
    top_k = st.slider(
        "Чанков для поиска",
        min_value=1,
        max_value=MAX_TOP_K,
        value=min(DEFAULT_TOP_K, MAX_TOP_K),
    )
with col_info:
    st.info(
        "Для ответа LLM используются **топ-6** самых релевантных чанков. "
        "Слайдер влияет на число источников в результате. "
        "На слабом ПК держите значение **5–10**."
    )

render_chat(api_url, top_k)
