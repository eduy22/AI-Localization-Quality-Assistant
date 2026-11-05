
import json
from pathlib import Path

import streamlit as st


RESULTS_PATH = Path(__file__).with_name("results.json")

st.set_page_config(
    page_title="Localization AI Evaluation",
    page_icon="📊",
    layout="wide"
)

st.title("Localization AI Evaluation")

if not RESULTS_PATH.exists():
    st.warning(
        "Run evaluation/run_evaluation.py first."
    )
    st.stop()

with open(RESULTS_PATH, encoding="utf-8") as file:
    data = json.load(file)

metrics = data["metrics"]

st.write("**Model:**", data["model"])
st.write("**Dataset size:**", data["dataset_size"])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Precision",
        f"{metrics['precision']:.1%}"
    )

with col2:
    st.metric(
        "Recall",
        f"{metrics['recall']:.1%}"
    )

with col3:
    st.metric(
        "F1-score",
        f"{metrics['f1_score']:.1%}"
    )

with col4:
    st.metric(
        "Accuracy",
        f"{metrics['accuracy']:.1%}"
    )

st.subheader("Confusion matrix counts")

st.bar_chart({
    "True Positive": metrics["true_positives"],
    "False Positive": metrics["false_positives"],
    "True Negative": metrics["true_negatives"],
    "False Negative": metrics["false_negatives"]
})

st.subheader("Individual test results")

for result in data["results"]:
    if result["status"] != "success":
        status = "API error"
    elif result["expected_error"] == result["predicted_error"]:
        status = "Correct classification"
    else:
        status = "Incorrect classification"

    with st.expander(
        f"{result['id']} — {status}"
    ):
        st.write("**Source:**", result["source"])
        st.write("**Translation:**", result["target"])
        st.write(
            "**Expected error:**",
            result["expected_error"]
        )
        st.write(
            "**Predicted error:**",
            result["predicted_error"]
        )
        st.write(
            "**Description:**",
            result["description"]
        )

        if result["status"] == "success":
            st.json(result["assessment"])
        else:
            st.warning(
                "The API request was unsuccessful."
            )

if metrics["failed_requests"]:
    st.warning(
        f"{metrics['failed_requests']} requests failed. "
        "Metrics exclude these examples."
    )

if metrics["evaluated"] == 0:
    st.warning(
        "No successful API responses were available "
        "for evaluation."
    )
