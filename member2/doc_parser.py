from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pymupdf
from docx import Document


class ParseError(ValueError):
    """Raised when a document cannot be parsed."""


def _safe_document_id(file_path: str | Path) -> str:
    raw_name = Path(file_path).name
    stem = Path(raw_name).stem
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", stem)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "document"


def _normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()


def _make_section(document_id: str, section_index: int, *, page_number: int | None, title: str | None, text: str) -> dict[str, Any]:
    return {
        "id": f"{document_id}_section_{section_index}",
        "document_id": document_id,
        "page_number": page_number,
        "section_title": title,
        "text": text,
    }


def _use_custom_section_ids(sections: list[dict[str, Any]], document_id: str) -> list[dict[str, Any]]:
    for index, section in enumerate(sections, start=1):
        section["id"] = f"{document_id}-S{index:03d}"
    return sections


def _parse_text_sections(raw_text: str, document_id: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_title: str | None = None
    current_paragraph_lines: list[str] = []
    current_paragraphs: list[str] = []

    def flush_paragraph() -> None:
        nonlocal current_paragraph_lines
        if current_paragraph_lines:
            current_paragraphs.append("\n".join(current_paragraph_lines))
            current_paragraph_lines = []

    def finalize_current() -> None:
        nonlocal current_title, current_paragraphs
        flush_paragraph()
        if current_title is None and not current_paragraphs:
            return

        section_index = len(sections) + 1
        sections.append(
            _make_section(
                document_id,
                section_index,
                page_number=None,
                title=current_title,
                text=_normalize_text("\n\n".join(current_paragraphs)),
            )
        )
        current_title = None
        current_paragraphs = []

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue

        numbered_heading = re.match(r"^\d+\.\s+\S", line)
        uppercase_heading = (
            len(line) < 80
            and re.fullmatch(r"[A-Z\s]+", line) is not None
        )
        if line.startswith("#") or numbered_heading or uppercase_heading:
            flush_paragraph()
            finalize_current()
            current_title = re.sub(r"^#+\s*", "", line).strip() if line.startswith("#") else line
            continue

        current_paragraph_lines.append(line)

    finalize_current()
    return sections


def _parse_docx_sections(file_path: str | Path, document_id: str) -> list[dict[str, Any]]:
    try:
        document = Document(str(file_path))
    except Exception as exc:  # pragma: no cover - exercised by pytest via corrupted DOCX
        raise ParseError(f"Corrupt DOCX file: {file_path}. Unable to read document: {exc}") from exc

    sections: list[dict[str, Any]] = []
    section_index = 0
    current_title: str | None = None
    current_lines: list[str] = []

    def finalize_current() -> None:
        nonlocal section_index, current_title, current_lines

        if not current_lines and current_title is None:
            return

        section_index += 1
        text = _normalize_text("\n".join(current_lines))
        sections.append(
            _make_section(
                document_id,
                section_index,
                page_number=None,
                title=current_title,
                text=text,
            )
        )
        current_title = None
        current_lines = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        style_name = (paragraph.style.name or "").lower()
        if style_name.startswith("heading"):
            if current_title is not None or current_lines:
                finalize_current()
            current_title = text
            continue

        current_lines.append(text)

    finalize_current()

    if not sections:
        sections.append(
            _make_section(
                document_id,
                1,
                page_number=None,
                title=None,
                text="",
            )
        )

    return sections


def _parse_pdf_sections(file_path: str | Path, document_id: str) -> list[dict[str, Any]]:
    try:
        document = pymupdf.open(str(file_path))
    except Exception as exc:
        raise ParseError(f"Corrupt file: {file_path}. Unable to open PDF: {exc}") from exc

    sections: list[dict[str, Any]] = []
    found_text = False

    try:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True)
            cleaned = _normalize_text(text)
            if not cleaned:
                continue
            found_text = True
            sections.append(
                _make_section(
                    document_id,
                    page_number,
                    page_number=page_number,
                    title=None,
                    text=cleaned,
                )
            )
    finally:
        document.close()

    if not found_text:
        raise ParseError(f"Scanned PDFs are out of scope: {file_path}. No text found on the document.")

    return sections


def parse_document(file_path: str | Path, document_id: str | None = None) -> list[dict[str, Any]]:
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise ParseError(f"Missing file: {file_path}")

    custom_document_id = document_id is not None
    document_id = document_id if custom_document_id else _safe_document_id(path)
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md"}:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ParseError(f"Corrupt file: {file_path}. Unable to decode text content.") from exc
        except OSError as exc:
            raise ParseError(f"Corrupt file: {file_path}. Unable to read file: {exc}") from exc
        sections = _parse_text_sections(content, document_id)
        return _use_custom_section_ids(sections, document_id) if custom_document_id else sections

    if suffix == ".pdf":
        sections = _parse_pdf_sections(path, document_id)
        return _use_custom_section_ids(sections, document_id) if custom_document_id else sections

    if suffix == ".docx":
        sections = _parse_docx_sections(path, document_id)
        return _use_custom_section_ids(sections, document_id) if custom_document_id else sections

    raise ParseError(
        f"Unsupported file extension: {suffix or '[none]'} for {path.name}. Supported extensions: .txt, .md, .pdf, .docx"
    )
