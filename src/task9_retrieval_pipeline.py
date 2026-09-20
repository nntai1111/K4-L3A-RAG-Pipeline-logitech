"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

import os

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


load_dotenv()

# Hiệu chỉnh trên corpus giấc ngủ (706 chunk, embedding BAAI/bge-m3):
#   5 câu trong domain  : 0.6194 – 0.7663
#   5 câu ngoài domain  : 0.3976 – 0.4931
# Hai cụm tách nhau 0.126 nên lấy điểm giữa. Mặc định 0.3 của repo quá thấp:
# mọi câu ngoài domain đều vượt, pipeline sẽ không bao giờ fallback.
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD") or 0.55)
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    if not query.strip() or top_k <= 0:
        return []

    # Lấy dư gấp đôi ở mỗi nhánh để RRF có đủ ứng viên mà gộp.
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    # rerank_rrf CHỈ được gọi ở đúng dòng này, đúng một lần cho mỗi query.
    hybrid = (
        rerank_rrf([dense, sparse], top_k=top_k)
        if use_reranking
        else dense[:top_k]
    )

    # So với cosine similarity GỐC của dense, không phải điểm RRF:
    # RRF score chỉ phản ánh thứ hạng và luôn rất nhỏ (~0.03).
    best_dense_score = dense[0]["score"] if dense else 0.0

    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback[:top_k]
        except Exception:
            # Provider ngoài lỗi không được làm sập UI — rơi về hybrid.
            pass

    return hybrid[:top_k]


if __name__ == "__main__":
    for result in retrieve("Người lớn nên ngủ bao nhiêu tiếng?", top_k=3):
        print(f"{result['score']:.4f}  [{result['retrieval_method']}]  {result['id']}")
        print(f"   {result['content'][:120]}...")
