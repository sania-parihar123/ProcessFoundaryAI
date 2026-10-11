from pathlib import Path

from .doc_parser import parse_document


if __name__ == "__main__":
    file_path = Path(__file__).resolve().parent / "samples" / "sample_scholarship.txt"
    sections = parse_document(file_path)

    for section in sections:
        title = section["section_title"] if section["section_title"] is not None else "<untitled>"
        print(f"{section['id']} | {title}")
