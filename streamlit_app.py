import re
import streamlit as st
from src.rag_pipeline import answer_stream
from src.retrieval import is_specific_url

CHROMA_PATH = "data/chroma"

st.set_page_config(page_title="CruxBot", page_icon="🧗", layout="wide")

st.title("🧗 CruxBot")
st.caption("Your AI rock climbing assistant — powered by RAG + Llama3")


# ============================================================
# Keyword highlighting helper
# ============================================================

def highlight_snippet(snippet: str, query: str) -> str:
    """
    Highlight query keywords in source snippet using markdown bold.
    Returns markdown string with **keyword** wrapped around matches.
    """
    # Extract meaningful keywords from query (3+ chars, skip stop words)
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "for", "and", "nor", "but",
        "or", "yet", "so", "in", "on", "at", "to", "from", "by", "with",
        "about", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again", "further",
        "then", "once", "here", "there", "when", "where", "why", "how", "all",
        "each", "every", "both", "few", "more", "most", "other", "some", "such",
        "what", "which", "who", "whom", "this", "that", "these", "those", "i",
        "me", "my", "myself", "we", "our", "you", "your", "he", "him", "his",
        "she", "her", "it", "its", "they", "them", "their", "not", "no",
        "best", "good", "recommend", "find", "tell", "give", "show", "help",
    }

    words = re.findall(r"[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*", query)
    keywords = [w for w in words if len(w) >= 3 and w.lower() not in stop_words]

    if not keywords:
        return snippet

    # Build regex pattern for all keywords (case insensitive)
    pattern = "|".join(re.escape(kw) for kw in keywords)
    # Replace matches with bold markdown, preserving original case
    highlighted = re.sub(
        f"({pattern})",
        r"<b>\1</b>",
        snippet,
        flags=re.IGNORECASE,
    )
    return highlighted


# ============================================================
# Source display helper
# ============================================================

def render_sources(sources: list[dict], query: str):
    """Render source list with URL validation and keyword highlighting."""
    if not sources:
        return

    with st.expander(f"📚 Sources ({len(sources)} retrieved)"):
        for i, src in enumerate(sources, 1):
            url = src.get("url", "")
            specific = src.get("is_specific", True)
            snippet = src.get("snippet", "")

            # URL display
            if url and specific:
                st.markdown(f"**[{i}]** [{url}]({url})")
            elif url:
                st.markdown(f"**[{i}]** {url} _(general forum page)_")
            else:
                st.markdown(f"**[{i}]** _no URL available_")

            # Highlighted snippet
            if snippet:
                highlighted = highlight_snippet(snippet, query)
                st.markdown(
                    f'<p style="color: gray; font-size: 0.85em; margin-top: -8px;">{highlighted}</p>',
                    unsafe_allow_html=True,
                )


# ============================================================
# Sidebar
# ============================================================

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


# ============================================================
# Chat history
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            render_sources(msg["sources"], msg.get("query", ""))


# ============================================================
# Input handling
# ============================================================

prefill = st.session_state.pop("prefill_query", None)
query = st.chat_input("Ask me anything about rock climbing...")
if prefill and not query:
    query = prefill

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        try:
            # Show retrieval spinner briefly
            with st.spinner("Searching climbing knowledge base..."):
                result = answer_stream(query, top_k=top_k, chroma_path=CHROMA_PATH)

            # Stream the LLM response token by token
            response_text = st.write_stream(result["stream"])

            # Build source list
            sources = [
                {
                    "url": s["url"],
                    "snippet": s["text_snippet"],
                    "is_specific": s.get("is_specific", True),
                }
                for s in result["sources"]
            ]

            # Render sources with highlighting
            render_sources(sources, query)

            # Save to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "sources": sources,
                "query": query,
            })

        except ConnectionError:
            err = "Could not connect to Ollama. Make sure it's running: `ollama serve`"
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err, "sources": []})
        except Exception as e:
            err = f"Error: {e}"
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err, "sources": []})
