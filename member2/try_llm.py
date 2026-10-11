from pathlib import Path

from pydantic import BaseModel

from member2.doc_parser import parse_document
from member2.llm_helper import call_llm


class ActorList(BaseModel):
    actors: list[str]


if __name__ == "__main__":
    sample_path = Path(__file__).resolve().parent / "samples" / "sample_scholarship.txt"
    sections = parse_document(sample_path)
    procedure_section = next(
        section
        for section in sections
        if section["title"] and "APPLICATION PROCEDURE" in section["title"]
    )

    result = call_llm(
        system_prompt=(
            "Extract the distinct people or organizational roles that perform actions "
            "in the provided text. Return only the requested structured data."
        ),
        user_prompt=procedure_section["text"],
        response_model=ActorList,
    )

    print(result if result is not None else "FAILED")
