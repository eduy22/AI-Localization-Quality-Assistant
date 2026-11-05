
import pytest

from terminology_checker import (
    contains_term,
    parse_glossary,
    check_terminology
)


def test_case_insensitive_matching():
    assert contains_term(
        "The DEVICE is ready.",
        "device"
    )


def test_whole_word_matching():
    assert contains_term(
        "The device is ready.",
        "device"
    )

    assert not contains_term(
        "Several devices are ready.",
        "device"
    )


def test_glossary_parsing():
    glossary = (
        "device = dispositivo\n"
        "power supply = fuente de alimentación"
    )

    entries, invalid_lines = parse_glossary(glossary)

    assert len(entries) == 2
    assert invalid_lines == []
    assert entries[0]["source_term"] == "device"


def test_invalid_glossary_lines():
    glossary = (
        "device = dispositivo\n"
        "invalid entry\n"
        "power supply ="
    )

    entries, invalid_lines = parse_glossary(glossary)

    assert len(entries) == 1
    assert invalid_lines == [2, 3]


@pytest.mark.parametrize(
    "source,target,expected_rate,expected_issues",
    [
        (
            "The device is connected to the power supply.",
            "El dispositivo está conectado "
            "a la fuente de alimentación.",
            100.0,
            0
        ),
        (
            "The device is connected to the power supply.",
            "El dispositivo está conectado "
            "a la alimentación.",
            50.0,
            1
        ),
        (
            "The device is connected to the power supply.",
            "El aparato está conectado "
            "a la alimentación.",
            0.0,
            2
        ),
        (
            "The system is ready.",
            "El sistema está listo.",
            None,
            0
        )
    ]
)
def test_terminology_compliance(
    source,
    target,
    expected_rate,
    expected_issues
):
    glossary = (
        "device = dispositivo\n"
        "power supply = fuente de alimentación"
    )

    result = check_terminology(
        source,
        target,
        glossary
    )

    assert result["compliance_rate"] == expected_rate
    assert len(result["issues"]) == expected_issues
