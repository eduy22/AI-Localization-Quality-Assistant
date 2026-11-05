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

if st.button("Analyze translation", type="primary"):

    if not source_text.strip() or not target_text.strip():
        st.warning("Please provide both texts.")

    elif source_language == target_language:
        st.warning("Source and target languages must be different.")

    elif "GEMINI_API_KEY" not in st.secrets:
        st.error("Gemini API key not found.")

    else:
        with st.spinner("Analyzing translation with Gemini..."):

            try:
                result = analyze_translation(
                    source_text=source_text,
                    target_text=target_text,
                    source_language=source_language,
                    target_language=target_language,
                    glossary=glossary,
                    api_key=st.secrets["GEMINI_API_KEY"]
                )

            except Exception as error:
                st.error("The AI analysis could not be completed.")
                st.caption(f"Error: {type(error).__name__}")
                st.code(str(error))

            
            else:
                st.success("AI analysis completed!")

                # Gemini linguistic quality analysis
                st.subheader("AI Linguistic Quality Assessment")

                st.write(
                    result.get(
                        "overall_assessment",
                        "No assessment available."
                    )
                )

                issues = result.get("issues", [])

                st.write(f"**AI-detected issues:** {len(issues)}")

                for index, issue in enumerate(issues, start=1):

                    category = issue.get("category", "Other")
                    severity = issue.get("severity", "Unknown")

                    with st.expander(
                        f"Issue {index}: {category} ({severity})",
                        expanded=True
                    ):
                        st.write(
                            "**Source:**",
                            issue.get("source_excerpt", "")
                        )
                        st.write(
                            "**Translation:**",
                            issue.get("target_excerpt", "")
                        )
                        st.write(
                            "**Explanation:**",
                            issue.get("explanation", "")
                        )
                        st.write(
                            "**Suggested correction:**",
                            issue.get("suggestion", "")
                        )

                st.divider()

                # Deterministic terminology validation
                st.subheader("Terminology Compliance")

                terminology_result = check_terminology(
                    source_text,
                    target_text,
                    glossary
                )

                invalid_lines = terminology_result["invalid_lines"]

                if invalid_lines:
                    st.warning(
                        "Invalid glossary entries on lines: "
                        + ", ".join(map(str, invalid_lines))
                    )

                checked = terminology_result["checked_terms"]
                compliant = terminology_result["compliant_terms"]
                rate = terminology_result["compliance_rate"]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Terms checked", checked)

                with col2:
                    st.metric("Compliant terms", compliant)

                with col3:
                    st.metric(
                        "Compliance rate",
                        f"{rate}%" if rate is not None else "N/A"
                    )

                terminology_issues = terminology_result["issues"]

                if terminology_issues:
                    st.warning(
                        f"{len(terminology_issues)} potential "
                        "terminology issue(s) detected."
                    )

                    for issue in terminology_issues:
                        with st.expander(
                            "Terminology: "
                            + issue["source_excerpt"],
                            expanded=True
                        ):
                            st.write(
                                "**Required translation:**",
                                issue["target_excerpt"]
                            )
                            st.write(
                                "**Explanation:**",
                                issue["explanation"]
                            )
                            st.write(
                                "**Suggestion:**",
                                issue["suggestion"]
                            )

                elif checked > 0:
                    st.success(
                        "All applicable glossary terms "
                        "were found in the translation."
                    )

                else:
                    st.info(
                        "No applicable glossary terms to check."
                    )

                st.caption(
                    "Terminology checks use exact normalized "
                    "matching. Results may require human review."
                )

                
                st.divider()

                # Unified quality report
                st.subheader("Unified Quality Report")

                report = generate_report(
                    ai_result=result,
                    terminology_result=terminology_result,
                    source_language=source_language,
                    target_language=target_language
                )

                metrics = report["metrics"]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Total findings",
                        metrics["total_issues"]
                    )

                with col2:
                    st.metric(
                        "Critical",
                        metrics["critical"]
                    )

                with col3:
                    st.metric(
                        "Major",
                        metrics["major"]
                    )

                with col4:
                    st.metric(
                        "Minor",
                        metrics["minor"]
                    )

                st.subheader("Findings by category")

                if metrics["categories"]:
                    st.bar_chart(metrics["categories"])
                else:
                    st.info("No findings to display.")

                st.caption(
                    "These are raw findings from two "
                    "independent checks. The same problem "
                    "may appear more than once."
                )

                st.subheader("Export report")

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        label="Download JSON report",
                        data=export_json(report),
                        file_name="localization_report.json",
                        mime="application/json"
                    )

                with col2:
                    st.download_button(
                        label="Download CSV report",
                        data=export_csv(report),
                        file_name="localization_report.csv",
                        mime="text/csv"
                    )


st.divider()

st.header("AI Terminology Agent")

st.write(
    "Run a Gemini agent that requests a Python "
    "terminology-checking tool and uses its results "
    "to produce a review."
)

if st.button("Run Terminology Agent"):

    if not source_text.strip() or not target_text.strip():
        st.warning(
            "Please provide both source and target texts."
        )

    elif source_language == target_language:
        st.warning(
            "Source and target languages must be different."
        )

    elif "GEMINI_API_KEY" not in st.secrets:
        st.error("Gemini API key not found.")

    else:
        with st.spinner(
            "Gemini agent is reviewing terminology..."
        ):
            try:
                agent_result = run_terminology_agent(
                    source_text=source_text,
                    target_text=target_text,
                    source_language=source_language,
                    target_language=target_language,
                    glossary=glossary,
                    api_key=st.secrets["GEMINI_API_KEY"]
                )

            except Exception as error:
                st.error(
                    "The terminology agent could not "
                    "complete its review."
                )
                st.caption(type(error).__name__)
                st.code(str(error))

            else:
                st.success("Agent review completed!")

                st.subheader("Agent Assessment")

                st.write(agent_result["assessment"])

                st.subheader("Tool Execution")

                st.write(
                    "**Tool requested:**",
                    agent_result["tool_name"]
                )

                st.write(
                    "**Tool arguments:**",
                    agent_result["tool_arguments"]
                )

                st.write("**Tool result:**")

                st.json(agent_result["tool_result"])

                st.caption(
                    "The tool was executed locally "
                    "by Python. Gemini used its output "
                    "to prepare the final assessment."
                )


