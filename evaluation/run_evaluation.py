
import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_analyzer import analyze_translation


DATASET_PATH = ROOT / "evaluation" / "dataset.json"
RESULTS_PATH = ROOT / "evaluation" / "results.json"


def calculate_metrics(results):
    evaluated = [
        item for item in results
        if item["status"] == "success"
    ]

    tp = fp = tn = fn = 0

    for item in evaluated:
        expected = item["expected_error"]
        predicted = item["predicted_error"]

        if expected and predicted:
            tp += 1
        elif not expected and predicted:
            fp += 1
        elif not expected and not predicted:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    accuracy = (
        (tp + tn) / len(evaluated)
        if evaluated
        else 0.0
    )

    return {
        "evaluated": len(evaluated),
        "failed_requests": len(results) - len(evaluated),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "accuracy": round(accuracy, 3)
    }


def main():
    with open(DATASET_PATH, encoding="utf-8") as file:
        dataset = json.load(file)

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or st.secrets["GEMINI_API_KEY"]
    )

    results = []

    for index, example in enumerate(dataset, start=1):
        print(
            f"Evaluating {index}/{len(dataset)}: "
            f"{example['id']}"
        )

        try:
            assessment = analyze_translation(
                source_text=example["source"],
                target_text=example["target"],
                source_language="English",
                target_language="Spanish",
                glossary="",
                api_key=api_key
            )

            predicted_error = bool(
                assessment.get("issues", [])
            )

            result = {
                **example,
                "status": "success",
                "predicted_error": predicted_error,
                "assessment": assessment
            }

        except Exception as error:
            print(
                f"  API error: {type(error).__name__}"
            )

            result = {
                **example,
                "status": "error",
                "predicted_error": None,
                "error_type": type(error).__name__
            }

        results.append(result)

        if index < len(dataset):
            time.sleep(2)

    metrics = calculate_metrics(results)

    output = {
        "model": "gemini-3.1-flash-lite",
        "dataset_size": len(dataset),
        "metrics": metrics,
        "results": results
    }

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nEvaluation completed.")
    print(json.dumps(metrics, indent=2))

    print(f"\nResults saved to: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
