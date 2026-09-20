import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot — Giấc ngủ",
    page_icon="",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_sources(sources: list[dict], retrieval_source: str) -> None:
    """Hiện nguồn, retrieval method và score cho từng chunk đã dùng."""
    if not sources:
        st.info("Không có nguồn nào được dùng cho câu trả lời này.")
        return

    with st.expander(f"Nguồn đã dùng ({len(sources)}) — retrieval: {retrieval_source}"):
        for index, source in enumerate(sources, 1):
            metadata = source["metadata"]
            st.markdown(
                f"**[{index}] {metadata['title']}**  \n"
                f"`{metadata['source']}` · {metadata['doc_type']} · "
                f"chunk {metadata['chunk_index']} · "
                f"method `{source['retrieval_method']}` · "
                f"score `{source['score']:.4f}`"
            )
            url = metadata.get("url")
            if url:
                st.markdown(f"[Xem bài gốc]({url})")
            st.caption(source["content"][:400] + "…")
            if index < len(sources):
                st.divider()


with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Hỏi đáp về giấc ngủ dựa trên tài liệu nhóm tự thu thập")
    top_k = st.slider("Số chunks", 3, 10, 5)
    if st.button("Xoá hội thoại"):
        st.session_state.messages = []
        st.rerun()

st.title("RAG Chatbot — Giấc ngủ")
st.caption("Câu trả lời chỉ dựa trên tài liệu đã index. Ngoài phạm vi sẽ được từ chối.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(
                message.get("sources", []),
                message.get("retrieval_source", "none"),
            )

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm trong tài liệu..."):
            result = generate_with_citation(query, top_k)

        st.markdown(result["answer"])
        render_sources(result["sources"], result["retrieval_source"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "retrieval_source": result["retrieval_source"],
        }
    )
