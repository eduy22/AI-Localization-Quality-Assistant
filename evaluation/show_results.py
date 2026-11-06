
import json
from pathlib import Path

import streamlit as st

import altair as alt
import pandas as pd


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


st.subheader("Confusion Matrix")

matrix_data = pd.DataFrame(
    [
        {
            "Actual": "Error",
            "Predicted": "Error",
            "Count": metrics["true_positives"]
        },
        {
            "Actual": "Error",
            "Predicted": "No error",
            "Count": metrics["false_negatives"]
        },
        {
            "Actual": "No error",
            "Predicted": "Error",
            "Count": metrics["false_positives"]
        },
        {
            "Actual": "No error",
            "Predicted": "No error",
            "Count": metrics["true_negatives"]
        }
    ]
)

heatmap = (
    alt.Chart(matrix_data)
    .mark_rect(cornerRadius=5)
    .encode(
        x=alt.X(
            "Predicted:N",
            title="Predicted classification",
            sort=["Error", "No error"]
        ),
        y=alt.Y(
            "Actual:N",
            title="Actual classification",
            sort=["Error", "No error"]
        ),
        color=alt.Color(
            "Count:Q",
            scale=alt.Scale(scheme="blues"),
            legend=None
        ),
        tooltip=["Actual", "Predicted", "Count"]
    )
)

labels = heatmap.mark_text(
    fontSize=20,
    fontWeight="bold"
).encode(
    text="Count:Q",
    color=alt.value("#111827")
)

st.altair_chart(
    (heatmap + labels).properties(height=230),
    use_container_width=True
)


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
