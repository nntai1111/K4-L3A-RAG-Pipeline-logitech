"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "BAAI/bge-m3"
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"

# Tài nguyên nặng được khởi tạo lười (lazy) để import module không chạm mạng:
# tests/test_contracts.py bị cấm gọi network.
_encoder = None
_collection = None

_SOURCE_PATTERN = re.compile(r"^\*\*Source:\*\*\s*(\S+)", re.MULTILINE)
_TITLE_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_LINK_PATTERN = re.compile(r"\[[^\]]*\]\([^)]*\)")

# Dòng có tỉ lệ ký tự nằm trong markdown link vượt ngưỡng này được coi là
# menu/sidebar/"bài viết liên quan" do crawler lấy kèm, không phải nội dung.
NAV_LINK_RATIO = 0.6


def _strip_navigation(text: str) -> str:
    """Bỏ các dòng chỉ chứa link điều hướng mà crawler lấy kèm.

    Đo trước khi lọc: 351/1026 chunk (34%) gần như chỉ có link, chúng chiếm chỗ
    trong top_k và kéo context precision xuống.
    """
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append("")
            continue
        covered = sum(len(m.group(0)) for m in _LINK_PATTERN.finditer(stripped))
        if covered / len(stripped) > NAV_LINK_RATIO:
            continue
        kept.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def _get_encoder():
    """Tải SentenceTransformer một lần rồi tái sử dụng."""
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer

        _encoder = SentenceTransformer(EMBEDDING_MODEL)
    return _encoder


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Hàm embedding DUY NHẤT của dự án — Task 5 phải dùng lại đúng hàm này."""
    texts = list(texts)
    if not texts:
        return []

    provider = EMBEDDING_PROVIDER.strip().lower()

    if provider == "sentence_transformers":
        vectors = _get_encoder().encode(
            texts, batch_size=16, show_progress_bar=len(texts) > 32
        )
        return [vector.tolist() for vector in vectors]

    if provider == "openai":
        from openai import OpenAI

        response = OpenAI().embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    if provider == "gemini":
        from google import genai

        response = genai.Client().models.embed_content(
            model=EMBEDDING_MODEL, contents=texts
        )
        return [list(item.values) for item in response.embeddings]

    raise ValueError(f"EMBEDDING_PROVIDER không hỗ trợ: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    global _collection
    if _collection is None:
        import chromadb

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        # doc_type lấy từ thư mục cha và phải giữ nguyên xuyên suốt pipeline.
        doc_type = "legal" if "legal" in path.parts else "news"

        # Task 3 ghi "**Source:** <url>" ở đầu file news — giữ lại để citation
        # còn truy ngược được về bài gốc.
        url_match = _SOURCE_PATTERN.search(content)
        url = url_match.group(1) if url_match else None

        title_match = _TITLE_PATTERN.search(content)
        title = title_match.group(1).strip() if title_match else path.stem

        # Lọc sau khi đã lấy url/title, vì header cũng nằm trong content.
        content = _strip_navigation(content)
        if not content:
            continue

        documents.append(
            {
                "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
                "content": content,
                "metadata": {
                    "source": path.name,
                    "title": title,
                    "doc_type": doc_type,
                    "url": url,
                },
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id ổn định và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for document in documents:
        pieces = [
            piece.strip()
            for piece in splitter.split_text(document["content"])
            if piece.strip()
        ]
        for index, text in enumerate(pieces):
            chunks.append(
                {
                    "id": f"{document['id']}::chunk-{index}",
                    "content": text,
                    "metadata": {**document["metadata"], "chunk_index": index},
                }
            )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk, giữ nguyên các field khác."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def _to_chroma_metadata(metadata: dict) -> dict:
    """ChromaDB chỉ nhận str/int/float/bool — None bị từ chối."""
    return {
        key: ("" if value is None else value)
        for key, value in metadata.items()
    }


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB (chạy lại không tạo bản sao vì id ổn định)."""
    collection = get_collection()
    batch = 500
    for start in range(0, len(chunks), batch):
        window = chunks[start : start + batch]
        collection.upsert(
            ids=[chunk["id"] for chunk in window],
            documents=[chunk["content"] for chunk in window],
            embeddings=[chunk["embedding"] for chunk in window],
            metadatas=[_to_chroma_metadata(chunk["metadata"]) for chunk in window],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Loaded {len(documents)} documents")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks")
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
