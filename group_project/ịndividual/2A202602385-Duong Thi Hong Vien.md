# Individual contribution report

---

## Thông tin

- Họ và tên: Dương Thị Hồng Viên
- Mã học viên: 2A202602385
- Nhóm: K4-L3A — Sleep Science & Sleep Optimization (logitech)

## Phần việc đã thực hiện

Phân công: **Đánh giá và test** (golden dataset, metrics, A/B, contract/acceptance tests).

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Golden dataset | Soạn/tổng hợp ≥15 Q&A về giấc ngủ (REM, adenosine/caffeine, vệ sinh giấc ngủ, thiếu ngủ, circadian…) bám corpus nhóm | `group_project/evaluation/golden_dataset.json` (hoặc tương đương) | Partial |
| Đánh giá 4 metrics | Chạy Faithfulness, Answer Relevance, Context Recall, Context Precision trên cùng generator/prompt/`top_k` | `group_project/evaluation/RESULT.md` | Partial |
| A/B testing | So sánh Config A (dense-only) vs Config B (hybrid + RRF); ghi delta và worst cases | `group_project/evaluation/RESULT.md`, `reports/RESULT.md` | Partial |
| Kiểm thử pipeline | Chạy contract/acceptance; báo lỗi schema `SearchResult`, threshold, citation cho thành viên phụ trách module | `tests/test_contracts.py`, `tests/test_acceptance.py` | Done / Partial |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** A/B chỉ đổi retrieval strategy; giữ nguyên golden set, LLM, prompt, embedding, `top_k`.  
   **Lý do/evidence:** Rubric yêu cầu so sánh công bằng; nếu đổi nhiều biến cùng lúc không kết luận được hybrid có tốt hơn dense hay không.  
   **Trade-off:** Không đo hết mọi tối ưu (chunk size, prompt); tập trung đúng câu hỏi “hybrid có cải thiện metric không?”.

2. **Quyết định:** Phân loại failure theo giai đoạn (retrieval / generation / data) khi ghi worst performers.  
   **Lý do/evidence:** Câu sai có thể do chunk thiếu, RRF xếp nhầm, hoặc LLM bịa ngoài context — cần gốc nguyên nhân để recommend.  
   **Trade-off:** Chấm tay tốn thời gian hơn chỉ nhìn điểm trung bình.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: bộ câu hỏi in-domain (ví dụ vai trò REM, melatonin/ánh sáng xanh) và out-of-domain (đăng ký môn, du lịch) để kiểm Safe Refusal; `pytest -q`.
- Kết quả trước/sau nếu có: Config B (hybrid) kỳ vọng cải thiện Context Recall/Precision trên câu có thuật ngữ chuyên ngành; số liệu chi tiết điền vào `RESULT.md` sau khi chạy evaluator đủ.
- Lỗi đã phát hiện và cách xử lý: Phát hiện câu trả lời “đúng cảm giác” nhưng không bám chunk → ghi giảm Faithfulness và yêu cầu siết citation/Safe Refusal ở Task 10.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Bảng điểm trong `RESULT.md` còn TODO — chưa có đủ run evaluator ổn định trên toàn bộ 15+ câu.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Chốt golden dataset 15+, chạy đủ A/B một lần, điền toàn bộ metric/delta/worst-3 và 3 recommendation có evidence.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Dương Thị Hồng Viên
