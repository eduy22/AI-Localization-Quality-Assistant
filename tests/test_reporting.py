
import csv
import io
import json

import pytest
from pydantic import ValidationError

from quality_models import validate_assessment
from report_generator import (
    generate_report,
    export_json,
    export_csv
)


@pytest.fixture
def sample_results():
    ai_result = {
        "overall_assessment": "One critical error detected.",
        "issues": [
            {
                "category": "Mistranslation",
                "severity": "Critical",
                "source_excerpt": "must",
                "target_excerpt": "puede",
                "explanation": "Obligation changed.",
                "suggestion": "Use debe."
            }
        ]
    }

    terminology_result = {
        "issues": [
            {
                "category": "Terminology",
                "severity": "Major",
                "source_excerpt": "power supply",
                "target_excerpt": "fuente de alimentación",
                "explanation": "Required term missing.",
                "suggestion": "Use the required term."
            }
        ],
        "checked_terms": 2,
        "compliant_terms": 1,
        "compliance_rate": 50.0,
        "invalid_lines": []
    }

    return ai_result, terminology_result


def test_valid_assessment(sample_results):
    ai_result, _ = sample_results

    validated = validate_assessment(ai_result)

    assert len(validated["issues"]) == 1
    assert validated["issues"][0]["severity"] == "Critical"


def test_invalid_severity(sample_results):
    ai_result, _ = sample_results

    ai_result["issues"][0]["severity"] = "Very Bad"

    with pytest.raises(ValidationError):
        validate_assessment(ai_result)


def test_unified_report(sample_results):
    ai_result, terminology_result = sample_results

    report = generate_report(
        ai_result,
        terminology_result,
        "English",
        "Spanish"
    )

    assert report["metrics"]["total_issues"] == 2
    assert report["metrics"]["critical"] == 1
    assert report["metrics"]["major"] == 1
    assert report["metrics"]["terminology_compliance"] == 50.0
    assert len(report["issues"]) == 2


def test_json_export(sample_results):
    ai_result, terminology_result = sample_results

    report = generate_report(
        ai_result,
        terminology_result,
        "English",
        "Spanish"
    )

    exported = export_json(report)
    parsed = json.loads(exported)

    assert parsed["metrics"]["total_issues"] == 2


def test_csv_export(sample_results):
    ai_result, terminology_result = sample_results

    report = generate_report(
        ai_result,
        terminology_result,
        "English",
        "Spanish"
    )

    exported = export_csv(report)

    decoded = exported.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(decoded)))

    assert len(rows) == 2
    assert rows[0]["detected_by"] == "Gemini"
    assert rows[1]["detected_by"] == "Terminology Checker"
