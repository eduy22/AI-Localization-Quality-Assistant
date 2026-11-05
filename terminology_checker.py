
import re
import unicodedata


def normalize_text(text):
    """
    Normalize Unicode, case and whitespace.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_term(text, term):
    """
    Find a term without matching inside another word.
    """
    normalized_text = normalize_text(text)
    normalized_term = normalize_text(term)

    if not normalized_term:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(normalized_term)
        + r"(?!\w)"
    )

    return re.search(pattern, normalized_text) is not None


def parse_glossary(glossary_text):
    """
    Parse glossary entries in the format:
    source term = target term
    """
    entries = []
    invalid_lines = []

    for line_number, line in enumerate(
        glossary_text.splitlines(), start=1
    ):
        line = line.strip()

        if not line:
            continue

        if "=" not in line:
            invalid_lines.append(line_number)
            continue

        source_term, target_term = line.split("=", 1)

        source_term = source_term.strip()
        target_term = target_term.strip()

        if not source_term or not target_term:
            invalid_lines.append(line_number)
            continue

        entries.append({
            "source_term": source_term,
            "target_term": target_term
        })

    return entries, invalid_lines


def check_terminology(source_text, target_text, glossary_text):
    """
    Check whether required glossary translations
    appear when their source terms are present.
    """
    entries, invalid_lines = parse_glossary(glossary_text)

    issues = []
    checked_terms = 0
    compliant_terms = 0

    for entry in entries:
        source_term = entry["source_term"]
        target_term = entry["target_term"]

        if not contains_term(source_text, source_term):
            continue

        checked_terms += 1

        if contains_term(target_text, target_term):
            compliant_terms += 1
        else:
            issues.append({
                "category": "Terminology",
                "severity": "Major",
                "source_excerpt": source_term,
                "target_excerpt": target_term,
                "explanation": (
                    f"The source term '{source_term}' appears "
                    "in the original, but the required "
                    f"translation '{target_term}' was not found."
                ),
                "suggestion": (
                    f"Review the translation and use "
                    f"'{target_term}' where appropriate."
                )
            })

    compliance_rate = (
        round(compliant_terms / checked_terms * 100, 1)
        if checked_terms > 0
        else None
    )

    return {
        "issues": issues,
        "checked_terms": checked_terms,
        "compliant_terms": compliant_terms,
        "compliance_rate": compliance_rate,
        "invalid_lines": invalid_lines
    }
