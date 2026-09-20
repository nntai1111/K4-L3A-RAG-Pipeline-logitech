"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re


# Để rỗng có chủ đích: contract test monkeypatch biến này bằng corpus giả, còn
# khi chạy thật thì lexical_search() nạp đúng chunks Task 4 đã index.
CORPUS: list[dict] = []

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Tách token có giữ dấu tiếng Việt (\\w+ với cờ UNICODE)."""
    return _TOKEN_PATTERN.findall(text.lower())


def load_corpus() -> list[dict]:
    """Đọc lại chunks từ ChromaDB để BM25 và dense dùng CHUNG một corpus."""
    from .task4_chunking_indexing import get_collection

    data = get_collection().get(include=["documents", "metadatas"])
    return [
        {"id": item_id, "content": content, "metadata": metadata}
        for item_id, content, metadata in zip(
            data["ids"], data["documents"], data["metadatas"]
        )
    ]


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi

    return BM25Okapi([_tokenize(item["content"]) for item in corpus])


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if not query.strip() or top_k <= 0:
        return []

    # Đọc CORPUS tại thời điểm gọi, không cache ở module level, để test
    # monkeypatch được và để corpus thật luôn khớp với bản đã index.
    corpus = CORPUS or load_corpus()
    if not corpus:
        return []

    query_tokens = _tokenize(query)
    bm25 = build_bm25_index(corpus)
    scores = bm25.get_scores(query_tokens)

    # Trên corpus rất nhỏ, IDF của BM25 có thể bằng 0 dù tài liệu khớp từ khoá,
    # nên không loại theo score mà loại theo "không chia sẻ token nào với query".
    wanted = set(query_tokens)
    overlaps = [
        len(wanted & set(_tokenize(item["content"]))) for item in corpus
    ]

    ranked = sorted(
        range(len(corpus)),
        key=lambda i: (scores[i], overlaps[i]),
        reverse=True,
    )

    results = []
    for index in ranked[:top_k]:
        if scores[index] <= 0 and overlaps[index] == 0:
            continue
        item = corpus[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": float(scores[index]),
                "metadata": item["metadata"],
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("mất ngủ melatonin", top_k=3):
        print(f"{result['score']:.4f}  {result['id']}")
        print(f"   {result['content'][:120]}...")
