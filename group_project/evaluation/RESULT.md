# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | RAGAS 0.4.3 & Pytest 8.0 |
| Evaluator model                    | gpt-4o-mini / gemini-1.5-flash |
| Generator model                    | gpt-4o-mini |
| Embedding model                    | BAAI/bge-m3 |
| Corpus version/commit              | 384fd00 (13 standardized markdown docs) |
| Golden dataset size                | 15 QA pairs |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.65 (Cosine Similarity calibrated on 15 golden + 5 out-of-domain queries) |

## Configurations

- **Config A — dense-only:** Sử dụng vector search đơn thuần trên ChromaDB với mô hình `BAAI/bge-m3`, khoảng cách cosine, lấy top 5 chunks có độ tương đồng cao nhất.
- **Config B — hybrid + RRF:** Kết hợp đồng thời Dense retrieval (`BAAI/bge-m3`) và Lexical retrieval (`rank-bm25`), sau đó áp dụng Reciprocal Rank Fusion (RRF với hằng số $k=60$) để gộp và tái xếp hạng ra top 5 chunks.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |     0.86 |     0.94 |     +0.08 |
| Answer relevance  |     0.82 |     0.91 |     +0.09 |
| Context recall    |     0.73 |     0.89 |     +0.16 |
| Context precision |     0.77 |     0.87 |     +0.10 |
| **Average**       |    0.795 |    0.903 |    +0.108 |

## A/B comparison

- Cấu hình tốt hơn: **Config B (Hybrid + RRF)**.
- Evidence: Điểm trung bình tổng thể tăng $0.108$ điểm (từ $0.795$ lên $0.903$). Đáng chú ý nhất là chỉ số **Context Recall** tăng vọt $+0.16$ (đạt $0.89$), giải quyết triệt để vấn đề bỏ sót các từ khóa chuyên ngành y học như tên thuật ngữ viết tắt (OSA, CPAP), tên riêng nhà khoa học (Peter Hauri) hoặc các con số mốc cụ thể (14-15h, 20 phút, 15-20°C).
- Trade-off về latency/cost: Config B mất thêm khoảng $45-65\text{ ms}$ cho mỗi lượt truy vấn do bước tính toán BM25 song song và thuật toán RRF trong Python. Tuy nhiên mức chi phí gọi LLM không tăng vì cùng giữ nguyên $top\_k = 5$ chunks đầu vào cho prompt generation.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Vệ sinh giấc ngủ được ai hệ thống hóa và từ năm nào? | Config A | 0.80 | 0.82 | 0.40 | 0.50 | retrieval | Dense model BGE-M3 coi cụm từ "Peter Hauri" và "năm 1977" là các thực thể hiếm, dẫn đến chunk liên quan bị tụt xuống vị trí top 8. |
|   2 | Trước giờ đi ngủ bao lâu thì nên tắt thiết bị ánh sáng xanh? | Config A | 0.85 | 0.86 | 0.60 | 0.70 | retrieval | Từ khóa "ánh sáng xanh" xuất hiện rải rác ở nhiều bài viết, dense search trả về các bài viết giải thích cơ chế thay vì bài checklist khuyến nghị thời gian cụ thể (60-90 phút). |
|   3 | Hội chứng ngưng thở khi ngủ do tắc nghẽn (OSA) là gì? | Config A | 0.88 | 0.85 | 0.65 | 0.72 | data/retrieval | File tài liệu y khoa có nhiều đoạn lặp lại thuật ngữ ngưng thở, dẫn đến các chunk bị trùng lặp nội dung tương tự nhau. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Duy trì cấu hình Hybrid BM25 + Dense RRF làm chuẩn mặc định cho hệ thống | Context recall tăng từ 0.73 lên 0.89 trên tập 15 golden cases | Nâng cao độ chính xác truy xuất và loại bỏ hiện tượng sót thông tin y khoa | Chạy lại script benchmark RAGAS trên tập golden dataset |
|        2 | Tinh chỉnh Chunk Size từ 500 xuống 350-400 ký tự với các tài liệu Checklist | Các câu hỏi về mốc thời gian ngắn (20 phút, 14-15h) thường nằm trong các gạch đầu dòng | Tăng Context Precision lên > 0.90 do giảm bớt các câu không liên quan trong chunk | Đánh giá metric Context Precision sau khi re-index |
|        3 | Thêm Cross-Encoder Reranker trước khi đưa vào LLM Generation | 2 trường hợp câu trả lời đúng bị trôi xuống vị trí top 4-5 | Đưa các chunk có độ tương quan ngữ nghĩa cao nhất lên top 1-2 | Chạy A/B testing so sánh giữa RRF thuần túy và RRF + BGE-Reranker |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Tăng $top\_k$ từ 5 lên 8 | Config B ($top\_k = 5$) | Recall $+0.04$, Precision $-0.06$ | Latency $+120\text{ ms}$, token cost $+35\%$ | Không nên tăng vì làm tăng context window và gây loãng thông tin dẫn đến giảm Context Precision |
| Thay đổi hằng số RRF $k=20$ thay vì $k=60$ | Config B ($k=60$) | Recall $-0.02$, Relevance $-0.01$ | Latency không đổi | Giá trị chuẩn $k=60$ cho độ ổn định cao hơn, giảm độ nhạy cảm thái quá với các thứ hạng cực đoan |
