# Individual contribution report

---

## Thông tin

- Họ và tên: Nguyễn Như Tài
- Mã học viên: 2A202602976
- Nhóm: K4-L3A — Sleep Science & Sleep Optimization (logitech)

## Phần việc đã thực hiện

Phân công: **Data** (cùng Nguyễn Công Vinh) và **Retrieval + sản phẩm** (cùng Lò Văn Long).

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập và chuẩn hóa dữ liệu | Cùng Vinh chọn tài liệu về giấc ngủ, kiểm tra dữ liệu và chuyển sang Markdown | `data/landing/`, `data/standardized/`, `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py` | Hoàn thành |
| Tìm kiếm tài liệu | Cùng nhóm kiểm tra cách tìm tài liệu bằng cả ý nghĩa câu hỏi và từ khóa, sau đó gộp kết quả | `src/task5_semantic_search.py`, `src/task6_lexical_search.py`, `src/task7_reranking.py`, `src/task9_retrieval_pipeline.py` | Hoàn thành một phần |
| Trả lời và giao diện | Tham gia viết prompt, thêm nguồn trích dẫn và kết nối với chatbot Streamlit | `src/task10_generation.py`, `app.py` | Hoàn thành một phần |

## Một số lựa chọn của nhóm

1. Nhóm dùng hai cách tìm kiếm: tìm theo ý nghĩa của câu hỏi và tìm theo từ khóa. Sau đó nhóm gộp hai kết quả để tìm được tài liệu phù hợp hơn.

2. Nhóm chỉ giữ lại nội dung chính về giấc ngủ và bỏ các phần menu hoặc thông tin thừa trong bài viết. Cách này giúp chatbot tìm và trả lời dễ hơn.

## Kiểm thử và kết quả

- Câu hỏi đã thử: *"Giai đoạn REM có vai trò gì?"* và *"Cách đăng ký môn học đại học?"*.
- Kết quả: Câu hỏi về giấc ngủ được tìm tài liệu để trả lời. Câu hỏi ngoài chủ đề được chuyển sang thông báo không có thông tin phù hợp.
- Lỗi đã phát hiện: Có lúc hệ thống chọn nhầm tài liệu khi câu hỏi không liên quan. Nhóm đã thêm bước kiểm tra để hạn chế lỗi này.

## Điều còn hạn chế

- Một hạn chế của phần tôi làm: Phần giao diện và hiển thị nguồn vẫn cần kiểm tra thêm.
- Nếu có thêm thời gian: Tôi sẽ hoàn thiện phần hiển thị nguồn và thử chatbot với nhiều câu hỏi hơn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Như Tài
