"""SmartStudy RAG — веб-интерфейс для вопросов по учебным материалам."""

from __future__ import annotations

import streamlit as st

from components.chat import render_chat
from components.sidebar import render_sidebar

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
    top_k = st.slider("Чанков для поиска", min_value=1, max_value=10, value=5)
with col_info:
    st.info(
        "Перед первым вопросом нажмите **Переиндексировать** в боковой панели, "
        "если база пуста. Для генерации ответов нужна запущенная Ollama."
    )

render_chat(api_url, top_k)
