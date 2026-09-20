"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""

REFUSAL = (
    "Tôi không thể xác minh thông tin này từ nguồn hiện có. "
    "Câu hỏi nằm ngoài phạm vi tài liệu mà hệ thống đang có."
)


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context.

    LLM chú ý kém nhất ở giữa context (lost-in-the-middle), nên chunk điểm cao
    được đẩy ra hai đầu. Hàm không sửa list gốc.
    """
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label để citation kiểm chứng được."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        header = (
            f"[Document {index} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}"
        )
        url = metadata.get("url")
        if url:
            header += f" | URL: {url}"
        parts.append(f"{header}]\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình trong .env."""
    provider = LLM_PROVIDER.strip().lower()

    if not LLM_MODEL:
        raise ValueError("LLM_MODEL đang trống trong .env")

    if provider == "openai":
        from openai import OpenAI

        response = OpenAI().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content or ""

    if provider == "gemini":
        from google import genai

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_message,
            config={
                "system_instruction": system_prompt,
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
            },
        )
        return response.text or ""

    if provider == "anthropic":
        import anthropic

        response = anthropic.Anthropic().messages.create(
            model=LLM_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )

    raise ValueError(f"LLM_PROVIDER không hỗ trợ: {LLM_PROVIDER}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    chunks = retrieve(query, top_k=top_k)

    # Không có evidence thì từ chối, không bịa.
    if not chunks:
        return {"answer": REFUSAL, "sources": [], "retrieval_source": "none"}

    context = format_context(reorder_for_llm(chunks))
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as error:
        # Provider lỗi cũng không được bịa và không được làm sập UI.
        return {
            "answer": f"{REFUSAL}\n\n(Lỗi khi gọi LLM: {error})",
            "sources": chunks,
            "retrieval_source": chunks[0]["retrieval_method"],
        }

    if not answer.strip():
        answer = REFUSAL

    return {
        "answer": answer,
        "sources": chunks,
        # "hybrid" hoặc "pageindex", lấy từ nhánh retrieval đã thắng.
        "retrieval_source": chunks[0]["retrieval_method"],
    }


if __name__ == "__main__":
    output = generate_with_citation("Người lớn nên ngủ bao nhiêu tiếng mỗi đêm?")
    print(output["answer"])
    print(f"\n--- retrieval_source: {output['retrieval_source']} ---")
    for source in output["sources"]:
        meta = source["metadata"]
        print(f"  {source['score']:.4f}  {meta['title'][:50]}  ({meta['source']})")
