
import csv
import io
import json
from collections import Counter
from datetime import datetime, timezone


def generate_report(
    ai_result,
    terminology_result,
    source_language,
    target_language
):
    """
    Combine AI and terminology assessments
    into a single structured report.
    """

    ai_issues = [
        {**issue, "detected_by": "Gemini"}
        for issue in ai_result["issues"]
    ]

    terminology_issues = [
        {**issue, "detected_by": "Terminology Checker"}
        for issue in terminology_result["issues"]
    ]

    all_issues = ai_issues + terminology_issues

    severity_counts = Counter(
        issue["severity"] for issue in all_issues
    )

    category_counts = Counter(
        issue["category"] for issue in all_issues
    )

    return {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "source_language": source_language,
        "target_language": target_language,
        "overall_assessment": ai_result["overall_assessment"],
        "metrics": {
            "total_issues": len(all_issues),
            "critical": severity_counts["Critical"],
            "major": severity_counts["Major"],
            "minor": severity_counts["Minor"],
            "categories": dict(category_counts),
            "terminology_compliance": (
                terminology_result["compliance_rate"]
            ),
            "terms_checked": (
                terminology_result["checked_terms"]
            )
        },
        "issues": all_issues
    }


def export_json(report):
    """
    Export the complete report as formatted JSON.
    """
    return json.dumps(
        report,
        indent=2,
        ensure_ascii=False
    )


def export_csv(report):
    """
    Export the issue list as a CSV file.
    """
    output = io.StringIO()

    fieldnames = [
        "detected_by",
        "category",
        "severity",
        "source_excerpt",
        "target_excerpt",
        "explanation",
        "suggestion"
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(report["issues"])

    return output.getvalue().encode("utf-8-sig")
