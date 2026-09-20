# Individual contribution report

---

## Thông tin

- Họ và tên: Nguyễn Công Vinh
- Mã học viên: 2A202602519
- Nhóm: K4-L3A — Sleep Science & Sleep Optimization (logitech)

## Phần việc đã thực hiện

Phân công: **Data** (cùng Nguyễn Như Tài) và **Chunking, embedding, indexing** (cùng Lò Văn Long).

| Module/deliverable              | Việc em trực tiếp làm                                                                                       | File/commit/PR                                                                                       | Trạng thái |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------- |
| Thu thập dữ liệu giấc ngủ       | Thu thập/đưa vào repo tài liệu legal (≥3) và crawl/chuẩn bị news (≥5 JSON)                                  | `data/landing/legal/`, `data/landing/news/`; commit `0086d3b` (_complete data collect_)              | Done       |
| Convert Markdown                | Chuyển PDF/DOCX/JSON → Markdown chuẩn hóa, giữ Source/Title                                                 | `src/task3_convert_markdown.py`, `data/standardized/`; commit `384fd00` (_convert data to markdown_) | Done       |
| Chunking / Embedding / Indexing | Cùng Long triển khai `load_documents` → `chunk_documents` → `embed_chunks` → ChromaDB; lọc navigation noise | `src/task4_chunking_indexing.py`, `chroma_db/`                                                       | Done       |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** `CHUNK_SIZE = 500`, `CHUNK_OVERLAP = 50`, method recursive; embedding `BAAI/bge-m3` (dim 1024).  
   **Lý do/evidence:** Tài liệu sách cần đủ ngữ cảnh (REM/NREM, vệ sinh giấc ngủ); overlap giữ liên kết giữa đoạn; bge-m3 phù hợp đa ngôn ngữ Việt–Anh trong corpus.  
   **Trade-off:** Chunk lớn hơn → ít chunk hơn nhưng tốn token hơn khi đưa vào LLM; model local nặng hơn API nhỏ.

2. **Quyết định:** ID chunk ổn định dạng `{doc_id}::chunk-{index}` và strip navigation trước khi embed.  
   **Lý do/evidence:** Tránh duplicate khi re-index; crawler thường kéo menu/sidebar làm nhiễu semantic search.  
   **Trade-off:** Thêm bước preprocessing; nếu threshold lọc sai có thể mất vài đoạn hợp lệ.

## Kiểm thử và kết quả

- Test hoặc query em đã dùng: `python -m src.task4_chunking_indexing`; `pytest tests/test_contracts.py -k test_task4`.
- Kết quả trước/sau nếu có: Sau khi làm sạch nav + chunk ổn định, collection Chroma có thể query dense được; trước đó nhiều hit là menu bệnh viện/không liên quan giấc ngủ.
- Lỗi đã phát hiện và cách xử lý: Markdown news lẫn link navigation → thêm `_strip_navigation` theo tỉ lệ link trong dòng.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần em làm: Một số bài news vẫn còn boilerplate footer sau convert; chất lượng phụ thuộc nguồn crawl.
- Nếu có thêm thời gian, thay đổi đầu tiên em sẽ thực hiện: Viết lại bộ lọc nội dung chính (main article only) và đo lại số chunk / độ dài trung bình trước khi re-index.

## Xác nhận đóng góp

Em xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Công Vinh
