"""Evaluation script for the RAG pipeline.

Runs a suite of test questions through the RAG class and reports
retrieval accuracy, answer faithfulness, and abstention accuracy.
"""

import os
import sys
from typing import Any, Dict, List

# Allow running this script directly from the tests/ directory or project root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.rag import RAG


TEST_CASES: List[Dict[str, Any]] = [
    {
        "question": "What problem does the Transformer architecture solve?",
        "expected_source": "attention.pdf",
        "expected_keywords": ["sequential", "recurrence"],
        "should_answer": True,
    },
    {
        "question": "What is scaled dot-product attention?",
        "expected_source": "attention.pdf",
        "expected_keywords": ["query", "key", "value"],
        "should_answer": True,
    },
    {
        "question": "What does BERT stand for?",
        "expected_source": "bert.pdf",
        "expected_keywords": ["Bidirectional", "Encoder", "Representations", "Transformers"],
        "should_answer": True,
    },
    {
        "question": "What is masked language modeling?",
        "expected_source": "bert.pdf",
        "expected_keywords": ["mask", "predict", "token"],
        "should_answer": True,
    },
    {
        "question": "What are the two steps in BERT's framework?",
        "expected_source": "bert.pdf",
        "expected_keywords": ["pre-training", "fine-tuning"],
        "should_answer": True,
    },
    {
        "question": "What problem does RAG solve?",
        "expected_source": "rag.pdf",
        "expected_keywords": ["knowledge", "parametric", "retrieval"],
        "should_answer": True,
    },
    {
        "question": "How does RAG combine retrieval with generation?",
        "expected_source": "rag.pdf",
        "expected_keywords": ["retriever", "generator", "document"],
        "should_answer": True,
    },
    {
        "question": "How many encoder layers does the base Transformer use?",
        "expected_source": "attention.pdf",
        "expected_keywords": ["6"],
        "should_answer": True,
    },
    {
        "question": "What optimizer was used to train the Transformer?",
        "expected_source": "attention.pdf",
        "expected_keywords": ["Adam"],
        "should_answer": True,
    },
    {
        "question": "What is positional encoding used for?",
        "expected_source": "attention.pdf",
        "expected_keywords": ["position", "sequence"],
        "should_answer": True,
    },
    {
        "question": "What datasets were used to evaluate RAG?",
        "expected_source": "rag.pdf",
        "expected_keywords": ["Natural Questions", "TriviaQA"],
        "should_answer": True,
    },
    {
        "question": "What tasks was BERT evaluated on?",
        "expected_source": "bert.pdf",
        "expected_keywords": ["GLUE", "SQuAD"],
        "should_answer": True,
    },
    {
        "question": "What is the capital of New Zealand?",
        "expected_source": None,
        "expected_keywords": [],
        "should_answer": False,
    },
    {
        "question": "Who invented Docker?",
        "expected_source": None,
        "expected_keywords": [],
        "should_answer": False,
    },
    {
        "question": "What is the price of Bitcoin?",
        "expected_source": None,
        "expected_keywords": [],
        "should_answer": False,
    },
]

NUM_RETRIEVAL_TESTS = 12
NUM_FAITHFULNESS_TESTS = 12
NUM_ABSTENTION_TESTS = 3
NUM_TOTAL_CHECKS = NUM_RETRIEVAL_TESTS + NUM_FAITHFULNESS_TESTS + NUM_ABSTENTION_TESTS


def contains_keyword(answer: str, keyword: str) -> bool:
    """Case-insensitive keyword containment check."""
    return keyword.lower() in answer.lower()


def check_abstention(answer: str) -> bool:
    """Check whether the answer signals abstention ('don't know')."""
    return "don't know" in answer.lower()


def run_evaluation(rag: RAG, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run all test cases and collect metrics."""
    results = []
    retrieval_passes = 0
    faithfulness_passes = 0
    abstention_passes = 0

    for idx, case in enumerate(cases, start=1):
        question = case["question"]
        expected_source = case.get("expected_source")
        expected_keywords = case.get("expected_keywords", [])
        should_answer = case["should_answer"]

        print(f"\n{'='*60}")
        print(f"Test {idx}/15: {question}")
        print(f"{'='*60}")

        try:
            response = rag.answer(question)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append(
                {
                    "idx": idx,
                    "question": question,
                    "retrieval_pass": False,
                    "faithfulness_pass": False,
                    "abstention_pass": False,
                    "error": str(exc),
                }
            )
            continue

        answer_text = response.get("answer", "")
        sources = response.get("sources", [])

        # --- Retrieval accuracy ---
        if should_answer:
            retrieval_pass = expected_source.lower() in (s.lower() for s in sources)
            if retrieval_pass:
                retrieval_passes += 1
        else:
            retrieval_pass = True  # N/A for guardrail tests

        # --- Answer faithfulness ---
        if should_answer:
            faithfulness_pass = any(
                contains_keyword(answer_text, kw) for kw in expected_keywords
            )
            if faithfulness_pass:
                faithfulness_passes += 1
        else:
            faithfulness_pass = True  # N/A for guardrail tests

        # --- Abstention accuracy ---
        if not should_answer:
            abstention_pass = check_abstention(answer_text)
            if abstention_pass:
                abstention_passes += 1
        else:
            abstention_pass = True  # N/A for non-guardrail tests

        print(f"  Sources retrieved : {sources}")
        print(f"  Answer            : {answer_text[:200]}{'...' if len(answer_text) > 200 else ''}")
        print(f"  Retrieval         : {'PASS' if retrieval_pass else 'FAIL'}")
        print(f"  Faithfulness      : {'PASS' if faithfulness_pass else 'FAIL'}")
        print(f"  Abstention        : {'PASS' if abstention_pass else 'FAIL'}")

        results.append(
            {
                "idx": idx,
                "question": question,
                "retrieval_pass": retrieval_pass,
                "faithfulness_pass": faithfulness_pass,
                "abstention_pass": abstention_pass,
                "sources": sources,
                "answer": answer_text,
            }
        )

    overall = (
        (retrieval_passes + faithfulness_passes + abstention_passes)
        / NUM_TOTAL_CHECKS
        * 100
    )

    return {
        "results": results,
        "retrieval_passes": retrieval_passes,
        "faithfulness_passes": faithfulness_passes,
        "abstention_passes": abstention_passes,
        "overall_score": overall,
    }


def print_summary(metrics: Dict[str, Any]) -> None:
    """Print the final evaluation summary."""
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"  Retrieval accuracy   : {metrics['retrieval_passes']}/{NUM_RETRIEVAL_TESTS}")
    print(f"  Answer faithfulness  : {metrics['faithfulness_passes']}/{NUM_FAITHFULNESS_TESTS}")
    print(f"  Abstention accuracy  : {metrics['abstention_passes']}/{NUM_ABSTENTION_TESTS}")
    print(f"  Overall score        : {metrics['overall_score']:.1f}%")
    print(f"{'='*60}\n")


def main() -> None:
    rag = RAG()
    metrics = run_evaluation(rag, TEST_CASES)
    print_summary(metrics)


if __name__ == "__main__":
    main()
