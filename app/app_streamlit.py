import streamlit as st
from app.ollama_chat import BookWormOllamaRAG

# PYTHONPATH=$PWD streamlit run app/app_streamlit.py to run

st.set_page_config(page_title="Book Worm AI Chat", layout="centered")
st.title("Book Worm AI Chat")

rag = BookWormOllamaRAG()

series = st.text_input("Series filter (optional):")
question = st.text_area("Ask your question:")

if st.button("Ask"):
    if question.strip():
        response = rag.ask(question, series_filter=series if series else None)
        st.markdown("### Response")
        st.write(response)
    else:
        st.warning("Please enter a question.")