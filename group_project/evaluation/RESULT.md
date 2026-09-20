# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | ragas 0.4.3 (Faithfulness, ResponseRelevancy, LLMContextRecall, LLMContextPrecisionWithReference) |
| Evaluator model                    | gpt-4o-mini (OpenAI), temperature 0 |
| Generator model                    | gpt-4o-mini (OpenAI), temperature 0.3, top_p 0.9 |
| Embedding model                    | BAAI/bge-m3 chạy local qua sentence-transformers, 1024 chiều, cosine distance |
| Corpus version/commit              | 12 tài liệu chuẩn hoá (5 legal + 7 news) → 706 chunk sau khi lọc nhiễu, `CHUNK_SIZE=500`, `CHUNK_OVERLAP=50` |
| Golden dataset size                | 32 câu |
| `top_k`                            | 5 |
| Fallback threshold and calibration | `SCORE_THRESHOLD=0.55`. Hiệu chỉnh bằng 5 câu trong domain (dense top-1 = 0.6194–0.7663) và 5 câu ngoài domain (0.3976–0.4931); hai cụm cách nhau 0.126 nên lấy điểm giữa. Mặc định 0.3 của repo quá thấp: mọi câu ngoài domain đều vượt ngưỡng nên fallback sẽ không bao giờ kích hoạt. |

## Configurations

- **Config A — dense-only:** `retrieve(query, top_k=5, use_reranking=False)`. Chỉ dùng dense search trên ChromaDB, lấy thẳng 5 kết quả đầu, không chạy BM25 và không fuse.
- **Config B — hybrid + RRF:** `retrieve(query, top_k=5, use_reranking=True)`. Chạy song song dense search và BM25 (mỗi nhánh lấy `top_k * 2 = 10`), rồi gộp bằng Reciprocal Rank Fusion `sum(1 / (60 + rank))`, rank bắt đầu từ 1, `rerank_rrf()` được gọi đúng một lần cho mỗi query.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

Cả hai chạy qua cùng một script [`src/evaluate_ab.py`](../../src/evaluate_ab.py), dùng chung `SYSTEM_PROMPT`, `reorder_for_llm()` và `format_context()` của Task 10. Biến duy nhất thay đổi là `use_reranking`.

Fallback vectorless (Task 8 — PageIndex) **không được kích hoạt trong lần chạy này** vì nhóm không có `PAGEINDEX_API_KEY`. `pageindex_search()` được bọc trong `try/except` nên mọi lỗi đều rơi về hybrid; điều này không làm sai lệch so sánh A/B vì nó tác động như nhau lên cả hai config.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   0.7523 |   0.8406 |   +0.0883 |
| Answer relevance  |   0.6022 |   0.6716 |   +0.0694 |
| Context recall    |   0.7500 |   0.7812 |   +0.0312 |
| Context precision |   0.7562 |   0.7573 |   +0.0012 |
| **Average**       |   0.7152 |   0.7627 |   +0.0475 |

## A/B comparison

- **Cấu hình tốt hơn:** Config B — hybrid + RRF.
- **Evidence:** Config B thắng trên **cả 4 metric**, trung bình +0.0475 (+6.6% tương đối). Mức cải thiện tập trung ở faithfulness (+0.0883) và answer relevance (+0.0694), tức khi BM25 được đưa vào, mô hình nhận được context chứa đúng dữ kiện nên bớt phải từ chối và bớt trả lời chung chung. Context recall tăng nhẹ (+0.0312) cho thấy tập chunk lấy về phủ đáp án tốt hơn. Context precision gần như đứng yên (+0.0012): RRF đưa thêm chunk đúng vào top-5 nhưng cũng đẩy vào một số chunk khớp từ khoá mà không mang thông tin trả lời, hai hiệu ứng triệt tiêu nhau.
- **Trade-off về latency/cost:** Config B tốn thêm một lượt BM25 trên toàn bộ 706 chunk cộng một lần fuse RRF cho mỗi query. Cả hai đều chạy local, không gọi API, và thời gian không đáng kể so với một lượt gọi LLM — chi phí token của hai config là như nhau vì `top_k` giống nhau. Đổi lại, Config B phải giữ corpus chunk trong bộ nhớ để dựng BM25 index, làm tăng mức dùng RAM.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | `sleep_008` — Bản tóm tắt *The Sleep Solution* liệt kê ba nhóm giai đoạn ngủ nào? | A và B đều 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | retrieval | Thông tin nằm trong `01_Tom_tat_Sach_Giac_Ngu.md` nhưng ở dạng danh sách gạch đầu dòng ngắn. Splitter cắt theo ký tự làm danh sách bị tách khỏi tiêu đề mục, nên chunk còn lại không còn ngữ cảnh "The Sleep Solution". Cả dense lẫn BM25 đều không lấy được, mô hình trả safe refusal. |
|   2 | `sleep_003` — Bốn phần chính của *Why We Sleep* là gì? | A và B đều 0.125 | 0.00 | 0.00 | 0.00 | 0.50 | retrieval | Đáp án trải trên bốn dòng tiêu đề rời nhau (`Phần 1` … `Phần 4`), mỗi dòng là một câu ngắn. Không chunk đơn lẻ nào chứa đủ cả bốn phần, nên context recall = 0 dù tài liệu có đủ thông tin. |
|   3 | `sleep_026` — Giấc ngủ trưa nên kéo dài tối đa bao lâu? | A: 0.60 · **B: 0.125** | 0.50 | 0.00 | 0.00 | 0.00 | retrieval | Đáp án ("không ngủ trưa quá 1 tiếng đồng hồ") nằm trong `article_03.md`. Đây là câu **duy nhất trong nhóm worst mà Config B kém hơn Config A**: BM25 kéo lên các chunk chứa cụm "ngủ trưa" ở tài liệu khác, đẩy chunk đúng ra khỏi top-5 sau khi fuse. |

Hai câu kế tiếp (`sleep_016`, `sleep_017`) là dạng **cross-source comparison** — yêu cầu so sánh nội dung giữa `02_Cam_nang_Ve_sinh_Giac_ngu.md` và `article_01.md`. Với `top_k=5`, retrieval hiếm khi lấy đủ chunk từ cả hai tài liệu cùng lúc, nên mô hình chỉ thấy một phía và từ chối trả lời.

Mẫu chung của toàn bộ nhóm worst: **không có câu nào là lỗi generation**. Mô hình không bịa đặt lần nào — nó từ chối đúng lúc không đủ evidence. Toàn bộ điểm mất nằm ở khâu retrieval và ở cách chunking cắt vụn các danh sách ngắn.

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Chunk theo cấu trúc Markdown (tách theo heading) thay vì cắt cứng 500 ký tự, và gắn đường dẫn heading vào đầu mỗi chunk | `sleep_003` và `sleep_008` đều thất bại vì danh sách ngắn bị tách khỏi tiêu đề mục | Context recall tăng rõ nhất ở nhóm câu `book_structure` và `book_fact` | Chạy lại `evaluate_ab.py` trên cùng 32 câu, so context recall trước/sau |
|        2 | Tăng `top_k` từ 5 lên 8–10 cho nhóm câu cross-source, hoặc ép lấy tối thiểu 1 chunk mỗi `doc_type` | `sleep_016` và `sleep_017` cần chunk từ hai tài liệu nhưng top-5 chỉ phủ một | Cải thiện các câu `cross_source_*`, đổi lại context precision có thể giảm | Đo riêng nhóm câu cross-source trước/sau khi đổi `top_k` |
|        3 | Chuẩn hoá dấu tiếng Việt khi tokenize cho BM25, hoặc hạ trọng số nhánh BM25 trong RRF | `sleep_026` là ca Config B thua Config A: BM25 kéo nhầm chunk chỉ khớp bề mặt cụm "ngủ trưa" | Giảm số ca hybrid làm hỏng kết quả mà dense vốn đã đúng | Đếm số câu có điểm B < A trước/sau khi chỉnh |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Lọc nhiễu navigation link ở bước `load_documents()` | Corpus thô 1026 chunk, trong đó 351 chunk (34,2%) có hơn 50% ký tự là markdown link do crawler lấy kèm menu và sidebar | Không đo A/B riêng (áp dụng trước khi chạy evaluation) | Giảm 320 chunk phải embed và tìm kiếm, rút corpus còn 706 chunk và hạ tỉ lệ nhiễu xuống 2,7% | Giữ lại. Trước khi lọc, BM25 thường xuyên trả về chunk chỉ chứa danh sách chuyên mục của Vinmec — vừa chiếm chỗ trong `top_k` vừa kéo context precision xuống |
| Hiệu chỉnh `SCORE_THRESHOLD` từ 0.3 lên 0.55 | Giá trị mặc định 0.3 trong repo | Không đo bằng ragas | Không đáng kể | Giữ lại. Với ngưỡng 0.3, mọi câu ngoài domain (0.3976–0.4931) đều vượt ngưỡng nên nhánh fallback là code chết |
| HyDE / query expansion / reranker nâng cao / conversation memory | — | — | — | Không thực hiện trong phạm vi bài này |

## Hạn chế đã biết

- **Golden dataset lệch về một tài liệu**: 12/32 câu hỏi về `01_Tom_tat_Sach_Giac_Ngu.md`, trong khi `article_04.md` và `article_05.md` (hai tài liệu NCBI tiếng Anh, chiếm phần lớn khối lượng corpus) không có câu hỏi nào. Kết quả A/B vì vậy phản ánh chủ yếu phần tiếng Việt của corpus.
- **Corpus trộn hai ngôn ngữ**: 4 tài liệu tiếng Việt và 3 tài liệu tiếng Anh. BM25 khớp token thô nên với câu hỏi tiếng Việt, nhánh BM25 gần như không bao giờ chạm tới tài liệu tiếng Anh — lợi thế của Config B bị giới hạn ở phần corpus cùng ngôn ngữ với câu hỏi.
- **`ResponseRelevancy` chạy với 1 generation thay vì 3**: `ChatOpenAI` chỉ trả về một lượt sinh cho mỗi yêu cầu, nên điểm answer relevance nhiễu hơn thiết kế gốc của ragas. Ảnh hưởng như nhau lên cả hai config nên không làm lệch kết luận so sánh.
- **Fallback vectorless chưa được kiểm chứng thực tế** vì nhóm không có `PAGEINDEX_API_KEY`; nhánh này chỉ được kiểm tra bằng contract test với hàm giả.
