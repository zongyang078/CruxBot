import streamlit as st
from src.rag_pipeline import answer
from src.retrieval import is_specific_url

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
    st.divider()
    st.markdown("**Example queries**")
    examples = [
        "Recommend a 5.10 sport route in California",
        "How should I train finger strength?",
        "What are common belaying mistakes?",
        "Best belay device for multi-pitch?",
        "What happened in climbing accidents at Red River Gorge?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
            st.session_state["prefill_query"] = ex

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"📚 Sources ({len(msg['sources'])} retrieved)"):
                for i, src in enumerate(msg["sources"], 1):
                    url = src.get("url", "")
                    specific = src.get("is_specific", True)
                    if url and specific:
                        st.markdown(f"**[{i}]** [{url}]({url})")
                    elif url:
                        st.markdown(f"**[{i}]** {url} _(general forum page)_")
                    else:
                        st.markdown(f"**[{i}]** _no URL available_")
                    st.caption(src.get("snippet", ""))

# Handle prefilled query from sidebar
prefill = st.session_state.pop("prefill_query", None)

# Input
query = st.chat_input("Ask me anything about rock climbing...")
if prefill and not query:
    query = prefill

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Searching climbing knowledge base..."):
            try:
                result = answer(query, top_k=top_k, chroma_path=CHROMA_PATH)
                st.markdown(result["answer"])

                sources = [
                    {
                        "url": s["url"],
                        "snippet": s["text_snippet"],
                        "is_specific": s.get("is_specific", True),
                    }
                    for s in result["sources"]
                ]
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)} retrieved)"):
                        for i, src in enumerate(sources, 1):
                            url = src.get("url", "")
                            specific = src.get("is_specific", True)
                            if url and specific:
                                st.markdown(f"**[{i}]** [{url}]({url})")
                            elif url:
                                st.markdown(f"**[{i}]** {url} _(general forum page)_")
                            else:
                                st.markdown(f"**[{i}]** _no URL available_")
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
