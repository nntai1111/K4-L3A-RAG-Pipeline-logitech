"""
Checkpoint 6 — Chạy A/B evaluation trên golden dataset.

Hai config chỉ khác nhau đúng một biến: retrieval strategy.
    Config A — dense-only   : retrieve(..., use_reranking=False)
    Config B — hybrid + RRF : retrieve(..., use_reranking=True)
Golden dataset, generator, prompt và top_k giữ nguyên ở cả hai.

Bốn metric: faithfulness, answer relevance, context recall, context precision.

Chạy:
    python -m src.evaluate_ab --limit 2          # thử rẻ trước
    python -m src.evaluate_ab                    # chạy full
    python -m src.evaluate_ab --config A         # chỉ một config

Kết quả ghi ra group_project/evaluation/ab_results.json để điền RESULT.md.
"""

import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from .task9_retrieval_pipeline import SCORE_THRESHOLD, retrieve
from .task10_generation import (
    REFUSAL,
    SYSTEM_PROMPT,
    call_llm,
    format_context,
    reorder_for_llm,
)
from .task4_chunking_indexing import EMBEDDING_MODEL


load_dotenv()

ROOT = Path(__file__).parent.parent
EVALUATION_DIR = ROOT / "group_project" / "evaluation"
GOLDEN_PATH = EVALUATION_DIR / "golden_dataset.json"
OUTPUT_PATH = EVALUATION_DIR / "ab_results.json"

TOP_K = 5

CONFIGS = {
    "A": {"label": "dense-only", "use_reranking": False},
    "B": {"label": "hybrid + RRF", "use_reranking": True},
}

METRIC_LABELS = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Answer relevance",
    "context_recall": "Context recall",
    "llm_context_precision_with_reference": "Context precision",
}


def build_evaluator():
    """LLM chấm điểm bám theo LLM_PROVIDER; embedding chấm điểm chạy local.

    Evaluator phải dùng đúng provider với generator, nếu không thì đổi .env sang
    OpenAI mà phần chấm điểm vẫn gọi Gemini.
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("LLM_MODEL", "")
    if not model:
        raise SystemExit("Thiếu LLM_MODEL trong .env")

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise SystemExit("Thiếu OPENAI_API_KEY trong .env")
        chat = ChatOpenAI(model=model, api_key=api_key, temperature=0)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise SystemExit("Thiếu GEMINI_API_KEY trong .env")
        chat = ChatGoogleGenerativeAI(
            model=model, google_api_key=api_key, temperature=0
        )

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as error:
            raise SystemExit(
                "Cần cài thêm: python -m pip install langchain-anthropic"
            ) from error

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise SystemExit("Thiếu ANTHROPIC_API_KEY trong .env")
        chat = ChatAnthropic(model=model, api_key=api_key, temperature=0)

    else:
        raise SystemExit(f"LLM_PROVIDER không hỗ trợ: {provider}")

    print(f"  evaluator: {provider} / {model}")
    llm = LangchainLLMWrapper(chat)
    # Metric của ragas gọi embed_query(), mà BaseRagasEmbedding mới chỉ có
    # embed_text(). Bọc embeddings của LangChain là cách duy nhất khớp interface.
    # Chạy local nên không tốn quota API.
    embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    )
    return llm, embeddings


def build_metrics():
    from ragas.metrics._answer_relevance import ResponseRelevancy
    from ragas.metrics._context_precision import LLMContextPrecisionWithReference
    from ragas.metrics._context_recall import LLMContextRecall
    from ragas.metrics._faithfulness import Faithfulness

    return [
        Faithfulness(),
        ResponseRelevancy(),
        LLMContextRecall(),
        LLMContextPrecisionWithReference(),
    ]


def answer_one(question: str, use_reranking: bool, delay: float) -> tuple[str, list[str]]:
    """Chạy đúng pipeline thật, chỉ đổi retrieval strategy."""
    chunks = retrieve(question, top_k=TOP_K, use_reranking=use_reranking)
    contexts = [chunk["content"] for chunk in chunks]

    if not chunks:
        return REFUSAL, []

    context = format_context(reorder_for_llm(chunks))
    try:
        answer = call_llm(SYSTEM_PROMPT, f"Context:\n{context}\n\nQuestion: {question}")
    except Exception as error:
        print(f"    ! lỗi gọi LLM: {error}")
        answer = REFUSAL
    time.sleep(delay)  # né rate limit của free tier
    return (answer.strip() or REFUSAL), contexts


def run_config(key: str, golden: list[dict], delay: float) -> dict:
    from ragas import EvaluationDataset, SingleTurnSample, evaluate

    config = CONFIGS[key]
    print(f"\n=== Config {key} — {config['label']} ===")

    samples, rows = [], []
    for index, item in enumerate(golden, 1):
        question = item["question"]
        print(f"  [{index}/{len(golden)}] {question[:60]}...")
        answer, contexts = answer_one(question, config["use_reranking"], delay)
        samples.append(
            SingleTurnSample(
                user_input=question,
                retrieved_contexts=contexts,
                response=answer,
                reference=item["expected_answer"],
            )
        )
        rows.append({"id": item.get("id"), "question": question, "answer": answer})

    llm, embeddings = build_evaluator()
    print("  → đang chấm điểm bằng ragas...")
    result = evaluate(
        dataset=EvaluationDataset(samples=samples),
        metrics=build_metrics(),
        llm=llm,
        embeddings=embeddings,
        show_progress=True,
    )

    scores = {}
    frame = result.to_pandas()
    for column in frame.columns:
        if column in METRIC_LABELS:
            scores[column] = float(frame[column].mean(skipna=True))
        elif column in rows[0]:
            continue

    for position, row in enumerate(rows):
        for column in METRIC_LABELS:
            if column in frame.columns:
                row[column] = float(frame[column].iloc[position])

    return {"label": config["label"], "scores": scores, "per_question": rows}


def print_comparison(results: dict) -> None:
    print("\n" + "=" * 68)
    print(f"{'Metric':<20}{'Config A':>12}{'Config B':>12}{'Delta B-A':>14}")
    print("-" * 68)
    averages = {}
    for column, label in METRIC_LABELS.items():
        a = results.get("A", {}).get("scores", {}).get(column)
        b = results.get("B", {}).get("scores", {}).get(column)
        if a is None and b is None:
            continue
        delta = (b - a) if (a is not None and b is not None) else None
        print(
            f"{label:<20}{_fmt(a):>12}{_fmt(b):>12}"
            f"{(f'{delta:+.4f}' if delta is not None else '—'):>14}"
        )
    for key in ("A", "B"):
        values = list(results.get(key, {}).get("scores", {}).values())
        averages[key] = sum(values) / len(values) if values else None
    delta = (
        averages["B"] - averages["A"]
        if averages.get("A") is not None and averages.get("B") is not None
        else None
    )
    print("-" * 68)
    print(
        f"{'Average':<20}{_fmt(averages.get('A')):>12}{_fmt(averages.get('B')):>12}"
        f"{(f'{delta:+.4f}' if delta is not None else '—'):>14}"
    )
    print("=" * 68)


def _fmt(value) -> str:
    return "—" if value is None else f"{value:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B evaluation cho RAG pipeline")
    parser.add_argument("--limit", type=int, default=0, help="chỉ chạy N câu đầu")
    parser.add_argument("--config", choices=["A", "B"], help="chỉ chạy một config")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="giây nghỉ giữa 2 lần gọi LLM"
    )
    args = parser.parse_args()

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    if args.limit:
        golden = golden[: args.limit]
    print(f"Golden dataset: {len(golden)} câu | top_k={TOP_K} | threshold={SCORE_THRESHOLD}")

    keys = [args.config] if args.config else ["A", "B"]
    results = {key: run_config(key, golden, args.delay) for key in keys}

    print_comparison(results)

    payload = {
        "evaluation_date": date.today().isoformat(),
        "golden_dataset_size": len(golden),
        "top_k": TOP_K,
        "score_threshold": SCORE_THRESHOLD,
        "generator_model": os.getenv("LLM_MODEL"),
        "evaluator_model": os.getenv("LLM_MODEL"),
        "embedding_model": EMBEDDING_MODEL,
        "configs": results,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nĐã ghi: {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
