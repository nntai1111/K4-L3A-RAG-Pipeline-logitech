"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.

TRẠNG THÁI: nhóm KHÔNG đăng ký PageIndex nên không có PAGEINDEX_API_KEY.
Không có key thì không gọi được API để xem response thật, và viết code parse
theo phỏng đoán tên field sẽ hỏng lúc demo. Vì vậy hai hàm dưới đây trả về
kết quả rỗng một cách có kiểm soát thay vì đoán mò.

Điều này KHÔNG làm hỏng pipeline: Task 9 bọc pageindex_search() trong
try/except và rơi về hybrid khi fallback rỗng hoặc lỗi — xem
test_retrieve_survives_fallback_provider_error. Hạn chế này được ghi rõ trong
group_project/evaluation/RESULT.md.

Để bật lại: điền PAGEINDEX_API_KEY vào .env rồi thay phần thân hai hàm bằng
lời gọi SDK thật, kiểm tra response thực tế trước khi parse.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        print(
            "Bỏ qua upload: chưa có PAGEINDEX_API_KEY trong .env. "
            "Pipeline sẽ chạy bằng hybrid retrieval."
        )
        return

    raise NotImplementedError(
        "Đã có PAGEINDEX_API_KEY: hãy implement upload bằng SDK pageindex và "
        "cache mapping source -> document ID."
    )


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult, hoặc list rỗng khi chưa cấu hình."""
    if not PAGEINDEX_API_KEY:
        # Rỗng thay vì exception: Task 9 coi đây là "fallback không dùng được"
        # và trả hybrid, đúng như contract.
        return []

    raise NotImplementedError(
        "Đã có PAGEINDEX_API_KEY: hãy query document IDs đã upload và parse "
        "retrieved nodes thành SearchResult với retrieval_method='pageindex'."
    )


if __name__ == "__main__":
    upload_documents()
