from pathlib import Path

import pytest

from member2.doc_parser import ParseError, parse_document


def test_valid_txt_parses(tmp_path):
    file_path = tmp_path / "My Scholarship! Demo.txt"
    file_path.write_text(
        "# Overview\n\nApplicants submit transcripts and a statement of interest.\n\n# Requirements\n\nStudents must be enrolled steadily and complete the required forms.",
        encoding="utf-8",
    )

    sections = parse_document(file_path)

    assert len(sections) == 2
    assert sections[0]["document_id"] == "My_Scholarship_Demo"
    assert sections[0]["id"] == "My_Scholarship_Demo_section_1"
    assert sections[0]["section_title"] == "Overview"
    assert set(sections[0]) == {"id", "document_id", "page_number", "section_title", "text"}
    assert "Applicants submit transcripts" in sections[0]["text"]
    assert sections[1]["section_title"] == "Requirements"
    assert sections[1]["page_number"] is None


def test_explicit_document_id_sets_document_and_section_ids(tmp_path):
    file_path = tmp_path / "document.txt"
    file_path.write_text("# First\n\nFirst body.\n\n# Second\n\nSecond body.", encoding="utf-8")

    sections = parse_document(file_path, document_id="DOC-1")

    assert [section["document_id"] for section in sections] == ["DOC-1", "DOC-1"]
    assert [section["id"] for section in sections] == ["DOC-1-S001", "DOC-1-S002"]


def test_numbered_headings_split_sections_and_preserve_paragraphs(tmp_path):
    file_path = tmp_path / "numbered.txt"
    file_path.write_text(
        "1. PURPOSE\n\nFirst paragraph.\n\nSecond paragraph.\n\n"
        "2. ELIGIBILITY\n\nEligibility details.",
        encoding="utf-8",
    )

    sections = parse_document(file_path)

    assert len(sections) == 2
    assert sections[0]["section_title"] == "1. PURPOSE"
    assert sections[0]["text"] == "First paragraph.\n\nSecond paragraph."
    assert sections[1]["section_title"] == "2. ELIGIBILITY"
    assert sections[1]["text"] == "Eligibility details."


def test_markdown_heading_still_works(tmp_path):
    file_path = tmp_path / "markdown.md"
    file_path.write_text("# Title\n\nMarkdown body.", encoding="utf-8")

    sections = parse_document(file_path)

    assert len(sections) == 1
    assert sections[0]["section_title"] == "Title"
    assert sections[0]["text"] == "Markdown body."


def test_text_before_first_heading_becomes_preamble(tmp_path):
    file_path = tmp_path / "preamble.txt"
    file_path.write_text(
        "Introductory paragraph.\n\n1. PURPOSE\n\nPurpose details.",
        encoding="utf-8",
    )

    sections = parse_document(file_path)

    assert len(sections) == 2
    assert sections[0]["section_title"] is None
    assert sections[0]["text"] == "Introductory paragraph."
    assert sections[1]["section_title"] == "1. PURPOSE"
    assert sections[1]["text"] == "Purpose details."


def test_step_line_does_not_start_a_new_section(tmp_path):
    file_path = tmp_path / "steps.txt"
    file_path.write_text(
        "4. APPLICATION PROCEDURE\n\n"
        "Step 1. The student fills in the application form.\n\n"
        "Step 2. The student uploads documents.",
        encoding="utf-8",
    )

    sections = parse_document(file_path)

    assert len(sections) == 1
    assert sections[0]["section_title"] == "4. APPLICATION PROCEDURE"
    assert "Step 1. The student fills in the application form." in sections[0]["text"]
    assert "Step 2. The student uploads documents." in sections[0]["text"]


def test_sample_scholarship_sections_include_all_application_steps():
    sample_path = Path(__file__).resolve().parents[1] / "samples" / "sample_scholarship.txt"

    sections = parse_document(sample_path)

    assert 8 <= len(sections) <= 10
    application_procedure = next(
        section for section in sections if section["section_title"] == "4. APPLICATION PROCEDURE"
    )
    assert "Step 1." in application_procedure["text"]
    assert "Step 8." in application_procedure["text"]


def test_unsupported_extension_raises_parse_error(tmp_path):
    file_path = tmp_path / "notes.csv"
    file_path.write_text("name,value\n", encoding="utf-8")

    with pytest.raises(ParseError, match="Unsupported file extension"):
        parse_document(file_path)


def test_missing_file_raises_parse_error(tmp_path):
    file_path = tmp_path / "missing.txt"

    with pytest.raises(ParseError, match="Missing file"):
        parse_document(file_path)


def test_corrupt_docx_raises_parse_error(tmp_path):
    file_path = tmp_path / "broken.docx"
    file_path.write_bytes(b"not a valid docx file")

    with pytest.raises(ParseError, match="Corrupt DOCX file"):
        parse_document(file_path)
