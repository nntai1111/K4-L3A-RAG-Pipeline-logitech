"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.

Chủ đề của nhóm: kiến thức về giấc ngủ.

Corpus legal gồm hai loại, khai báo trong SOURCES bên dưới:
  - Tài liệu nhóm tự tổng hợp (.docx), đưa vào thủ công, không có URL tải về.
  - Tài liệu sưu tầm (.pdf) có thể tải lại bằng module này khi có URL.

CẢNH BÁO: thêm hoặc bớt tài liệu ở đây sẽ đổi corpus, kéo theo phải chạy lại
Task 3, Task 4 và toàn bộ evaluation vì số liệu trong RESULT.md gắn với bản
corpus hiện tại (12 tài liệu -> 706 chunk).
"""

import sys
from pathlib import Path


# Console Windows mặc định là cp1252, không in được tiếng Việt lẫn tên file có dấu.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):  # pragma: no cover - môi trường không hỗ trợ
    pass

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# filename -> (url tải trực tiếp hoặc None nếu đưa vào thủ công, ghi chú nguồn)
SOURCES: dict[str, tuple[str | None, str]] = {
    "01_Tom_tat_Sach_Giac_Ngu.docx": (
        None,
        "Nhóm tự tổng hợp: tóm tắt 3 cuốn Why We Sleep, The Sleep Solution, "
        "Sleep Smarter từ các bài review công khai, không sao chép nguyên văn.",
    ),
    "02_Cam_nang_Ve_sinh_Giac_ngu.docx": (
        None,
        "Nhóm tự tổng hợp từ Mayo Clinic, National Sleep Foundation, AASM, "
        "Harvard Health và Vinmec.",
    ),
    "03_Huong_dan_Y_khoa_va_5_Bai_viet.docx": (
        None,
        "Nhóm tự tổng hợp từ WHO, Mayo Clinic, AASM và Vinmec.",
    ),
    "725770566-GIẤC-NGỦ.pdf": (
        None,
        "Tài liệu sưu tầm do thành viên nhóm đưa vào; chưa xác định được trang "
        "công bố gốc, cần bổ sung nguồn trước khi nộp.",
    ),
    "Sleep Problems_Vietnamese_(Các Vấn Đề Về Giấc Ngủ).pdf": (
        None,
        "Tờ thông tin sức khoẻ bản tiếng Việt do thành viên nhóm đưa vào; "
        "chưa xác định được trang công bố gốc.",
    ),
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:

    """Tải các tài liệu có URL công khai và báo cáo tình trạng từng file.

    Chỉ tải file chưa tồn tại, nên chạy lại nhiều lần không ghi đè dữ liệu
    đang dùng và không tạo bản sao.
    """
    import requests

    missing_source = []
    for filename, (url, note) in SOURCES.items():
        target = DATA_DIR / filename
        exists = target.exists()

        if url is None:
            status = "có sẵn" if exists else "THIẾU FILE"
            print(f"[thủ công] {filename}: {status}")
            print(f"           nguồn: {note}")
            if not exists:
                missing_source.append(filename)
            continue

        if exists:
            print(f"[bỏ qua]   {filename}: đã có, không tải lại")
            continue

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            target.write_bytes(response.content)
            print(f"[tải về]   {filename}: {len(response.content) / 1024:.0f} KB")
        except Exception as error:
            print(f"[lỗi]      {filename}: {error}")
            missing_source.append(filename)

    present = sorted(
        path.name
        for path in DATA_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".doc", ".docx"}
    )
    print(f"\nTổng tài liệu legal hiện có: {len(present)} (yêu cầu tối thiểu 3)")
    if missing_source:
        print("Cần bổ sung thủ công:", ", ".join(missing_source))
if __name__ == "__main__":
    setup_directory()
    download_documents()
