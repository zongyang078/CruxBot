import streamlit as st
from src.rag_pipeline import answer

CHROMA_PATH = "data/chroma"

st.set_page_config(page_title="CruxBot", page_icon="🧗", layout="wide")

st.title("🧗 CruxBot")
st.caption("Your AI rock climbing assistant — powered by RAG + Llama3")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Sources to retrieve", min_value=1, max_value=10, value=5)
    st.divider()
    st.markdown("**How it works**")
    st.markdown(
        "1. Your question is embedded and matched against a climbing knowledge base\n"
        "2. The top relevant passages are retrieved from ChromaDB\n"
        "3. Llama3 (via Ollama) generates an answer grounded in those passages"
    )

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"Sources ({len(msg['sources'])} retrieved)"):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(f"**[{i}]** {src['url'] or '_no url_'}")
                    st.caption(src["snippet"])

# Input
query = st.chat_input("Ask me anything about rock climbing...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = answer(query, top_k=top_k, chroma_path=CHROMA_PATH)
                st.markdown(result["answer"])

                sources = [
                    {"url": s["url"], "snippet": s["text_snippet"]}
                    for s in result["sources"]
                ]
                if sources:
                    with st.expander(f"Sources ({len(sources)} retrieved)"):
                        for i, src in enumerate(sources, 1):
                            st.markdown(f"**[{i}]** {src['url'] or '_no url_'}")
                            st.caption(src["snippet"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": sources,
                })

            except ConnectionError:
                err = "Could not connect to Ollama. Make sure it's running: `ollama serve`"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err, "sources": []})
            except Exception as e:
                err = f"Error: {e}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err, "sources": []})
