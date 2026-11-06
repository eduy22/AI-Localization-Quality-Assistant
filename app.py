from ai_analyzer import analyze_translation
from terminology_agent import run_terminology_agent
import streamlit as st
from terminology_checker import check_terminology
from report_generator import (
    generate_report,
    export_json,
    export_csv
)

import streamlit as st
import altair as alt
import pandas as pd

from ai_analyzer import analyze_translation
from terminology_checker import check_terminology
from terminology_agent import run_terminology_agent
from report_generator import generate_report, export_json, export_csv

# Configuración general de la aplicación
st.set_page_config(
    page_title="AI Localization Quality Assistant",
    page_icon="🌐",
    layout="wide"
)

# Encabezado
st.title("🌐 AI Localization Quality Assistant")

st.write(
    "An AI-powered tool for translation quality assessment "
    "and terminology compliance."
)

st.divider()

# Selección de idiomas
col1, col2 = st.columns(2)

with col1:
    source_language = st.selectbox(
        "Source language",
        ["English", "Spanish", "French", "German"],
        index=0
    )

with col2:
    target_language = st.selectbox(
        "Target language",
        ["Spanish", "English", "French", "German"],
        index=0
    )

# Campos de texto
col1, col2 = st.columns(2)

with col1:
    source_text = st.text_area(
        "Source text",
        placeholder="Enter the original text...",
        height=200
    )

with col2:
    target_text = st.text_area(
        "Translated text",
        placeholder="Enter the translated text...",
        height=200
    )

# Glosario terminológico
st.subheader("Terminology glossary")

glossary = st.text_area(
    "Enter terminology pairs (one per line)",
    placeholder=(
        "power supply = fuente de alimentación\n"
        "device = dispositivo"
    ),
    height=120
)

st.divider()

# Botón principal


# Persistent results across Streamlit reruns
if "review_result" not in st.session_state:
    st.session_state.review_result = None

if "review_mode" not in st.session_state:
    st.session_state.review_mode = None


def validate_inputs():
    if not source_text.strip() or not target_text.strip():
        st.warning("Please provide both source and target texts.")
        return False

    if source_language == target_language:
        st.warning("Source and target languages must be different.")
        return False

    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Gemini API key not found.")
        return False

    return True


# Two side-by-side analysis buttons
col1, col2 = st.columns(2)

with col1:
    analyze_clicked = st.button(
        "Analyze Translation",
        type="primary",
        use_container_width=True
    )

with col2:
    agent_clicked = st.button(
        "Run AI Agent",
        use_container_width=True
    )


if analyze_clicked or agent_clicked:

    # Clear previous results before starting a new review
    st.session_state.review_result = None
    st.session_state.review_mode = None

    if validate_inputs():

        try:
            if analyze_clicked:
                with st.spinner("Analyzing translation with Gemini..."):

                    ai_result = analyze_translation(
                        source_text=source_text,
                        target_text=target_text,
                        source_language=source_language,
                        target_language=target_language,
                        glossary=glossary,
                        api_key=st.secrets["GEMINI_API_KEY"]
                    )

                    terminology_result = check_terminology(
                        source_text,
                        target_text,
                        glossary
                    )

                    report = generate_report(
                        ai_result=ai_result,
                        terminology_result=terminology_result,
                        source_language=source_language,
                        target_language=target_language
                    )

                    report["review_mode"] = "full_analysis"

                    st.session_state.review_result = {
                        "report": report,
                        "ai_result": ai_result,
                        "terminology_result": terminology_result
                    }

                    st.session_state.review_mode = "full"

            elif agent_clicked:
                with st.spinner("Running Gemini terminology agent..."):

                    agent_result = run_terminology_agent(
                        source_text=source_text,
                        target_text=target_text,
                        source_language=source_language,
                        target_language=target_language,
                        glossary=glossary,
                        api_key=st.secrets["GEMINI_API_KEY"]
                    )

                    terminology_result = agent_result["tool_result"]

                    # Reuse the report generator without
                    # claiming a full linguistic assessment.
                    agent_assessment = {
                        "overall_assessment": agent_result["assessment"],
                        "issues": []
                    }

                    report = generate_report(
                        ai_result=agent_assessment,
                        terminology_result=terminology_result,
                        source_language=source_language,
                        target_language=target_language
                    )

                    report["review_mode"] = "agent_terminology_review"
                    report["tool_used"] = agent_result["tool_name"]

                    st.session_state.review_result = {
                        "report": report,
                        "agent_result": agent_result,
                        "terminology_result": terminology_result
                    }

                    st.session_state.review_mode = "agent"

        except Exception as error:
            st.error("The review could not be completed.")
            st.caption(type(error).__name__)
            st.code(str(error))


# Display stored results
if st.session_state.review_result is not None:

    stored = st.session_state.review_result
    report = stored["report"]
    metrics = report["metrics"]
    mode = st.session_state.review_mode

    st.divider()

    if mode == "full":
        st.header("Translation Quality Report")
        st.write(stored["ai_result"]["overall_assessment"])

    else:
        st.header("Agent Terminology Review")
        st.write(stored["agent_result"]["assessment"])

        with st.expander("Agent tool execution"):
            st.write(
                "**Tool requested:**",
                stored["agent_result"]["tool_name"]
            )
            st.json(stored["agent_result"]["tool_result"])

    st.subheader("Quality Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total findings", metrics["total_issues"])

    with col2:
        st.metric("Critical", metrics["critical"])

    with col3:
        st.metric("Major", metrics["major"])

    with col4:
        st.metric("Minor", metrics["minor"])

    terminology_result = stored["terminology_result"]

    st.subheader("Terminology Compliance")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Terms checked",
            terminology_result["checked_terms"]
        )

    with col2:
        rate = terminology_result["compliance_rate"]
        st.metric(
            "Compliance rate",
            f"{rate}%" if rate is not None else "N/A"
        )

    if terminology_result["invalid_lines"]:
        st.warning(
            "Invalid glossary lines: "
            + ", ".join(
                map(str, terminology_result["invalid_lines"])
            )
        )

    
    st.subheader("Findings by Category")

    categories = metrics["categories"]

    if categories:
        chart_data = pd.DataFrame(
            [
                {"Category": name, "Findings": count}
                for name, count in categories.items()
            ]
        )

        max_count = int(chart_data["Findings"].max())

        bars = (
            alt.Chart(chart_data)
            .mark_bar(
                size=18,
                cornerRadiusEnd=4,
                color="#3978B8"
            )
            .encode(
                y=alt.Y(
                    "Category:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(
                        labelAngle=0,
                        labelFontSize=13,
                        labelLimit=180
                    )
                ),
                x=alt.X(
                    "Findings:Q",
                    title=None,
                    scale=alt.Scale(
                        domain=[0, max(2, max_count + 1)],
                        nice=False
                    ),
                    axis=alt.Axis(
                        tickMinStep=1,
                        format="d",
                        grid=False
                    )
                ),
                tooltip=["Category", "Findings"]
            )
        )

        labels = (
            alt.Chart(chart_data)
            .mark_text(
                align="left",
                baseline="middle",
                dx=8,
                fontSize=13
            )
            .encode(
                y=alt.Y("Category:N", sort="-x"),
                x=alt.X("Findings:Q"),
                text="Findings:Q"
            )
        )

        chart = (
            (bars + labels)
            .properties(
                height=max(130, len(categories) * 65)
            )
        )

        st.altair_chart(
            chart,
            use_container_width=True
        )

    else:
        st.info("No findings detected.")


    
    st.subheader("Detected Issues")

    ai_issues = [
        issue for issue in report["issues"]
        if issue["detected_by"] == "Gemini"
    ]

    terminology_issues = [
        issue for issue in report["issues"]
        if issue["detected_by"] == "Terminology Checker"
    ]

    # AI findings
    if mode == "full":
        st.markdown(
            f"#### AI Linguistic Assessment "
            f"({len(ai_issues)} findings)"
        )

        if ai_issues:
            for index, issue in enumerate(ai_issues, start=1):
                with st.expander(
                    f"{index}. {issue['category']} "
                    f"({issue['severity']})",
                    expanded=True
                ):
                    st.write(
                        "**Source excerpt:**",
                        issue["source_excerpt"]
                    )
                    st.write(
                        "**Translation excerpt:**",
                        issue["target_excerpt"]
                    )
                    st.write(
                        "**Explanation:**",
                        issue["explanation"]
                    )
                    st.write(
                        "**Suggested correction:**",
                        issue["suggestion"]
                    )
        else:
            st.success("No linguistic issues detected by Gemini.")

    # Rule-based terminology findings
    st.markdown(
        f"#### Rule-Based Terminology Check "
        f"({len(terminology_issues)} findings)"
    )

    if terminology_issues:
        for index, issue in enumerate(terminology_issues, start=1):
            with st.expander(
                f"{index}. Missing required term: "
                f"{issue['source_excerpt']}",
                expanded=True
            ):
                st.write(
                    "**Source term:**",
                    issue["source_excerpt"]
                )
                st.write(
                    "**Required translation:**",
                    issue["target_excerpt"]
                )
                st.write(
                    "**Explanation:**",
                    issue["explanation"]
                )
                st.write(
                    "**Recommendation:**",
                    issue["suggestion"]
                )
    else:
        st.success(
            "No terminology issues detected "
            "by the rule-based checker."
        )


    st.caption(
        "Findings from different checks may overlap. "
        "Human review is recommended."
    )

    st.subheader("Export Report")

    col1, col2 = st.columns(2)

    filename = (
        "agent_terminology_report"
        if mode == "agent"
        else "translation_quality_report"
    )

    with col1:
        st.download_button(
            "Download JSON",
            data=export_json(report),
            file_name=f"{filename}.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        st.download_button(
            "Download CSV",
            data=export_csv(report),
            file_name=f"{filename}.csv",
            mime="text/csv",
            use_container_width=True
        )



