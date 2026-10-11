from io import BytesIO

from openpyxl import Workbook

from app.agents.evidence_extraction import extract_evidence
from app.agents.ingestion_service import ingest_documents
from app.agents.document_ingestion import extract_document


class Upload(BytesIO):
    def __init__(self, name: str, content: bytes):
        super().__init__(content)
        self.name = name


def _xlsx(name: str, rows: list[list[object]]) -> Upload:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Rules"
    for row in rows:
        worksheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return Upload(name, buffer.getvalue())


def test_xlsx_evidence_preserves_worksheet_and_cell_source() -> None:
    upload = _xlsx(
        "rules.xlsx",
        [
            ["Policy statement", "Notes"],
            ["Annual family income must not exceed ₹2,50,000.", "Eligibility"],
        ],
    )
    document = extract_document(upload)
    evidence = extract_evidence(document.sections)

    assert len(evidence) == 1
    item = evidence[0]
    assert item["worksheet_name"] == "Rules"
    assert item["row_number"] == 2
    assert item["cell_references"] == ["A2", "B2"]
    assert "Rules!A2,B2" in item["source_refs"][1]
    assert item["quote"] == "Annual family income must not exceed ₹2,50,000"


def test_xlsx_formula_is_preserved_and_not_executed() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Values"
    worksheet.append(["Amount", "Calculated"])
    worksheet.append([100, "=A2*2"])
    buffer = BytesIO()
    workbook.save(buffer)

    document = extract_document(Upload("formula.xlsx", buffer.getvalue()))

    row = document.sections[1]
    assert row["cells"][1]["value"] == "=A2*2"
    assert "=A2*2" in row["text"]


def test_mixed_valid_and_corrupt_xlsx_files_continue_processing() -> None:
    result = ingest_documents(
        [
            _xlsx(
                "valid.xlsx",
                [["Policy"], ["Minimum attendance of 75% is required."]],
            ),
            Upload("broken.xlsx", b"bad workbook"),
        ]
    )

    assert len(result.documents) == 1
    assert len(result.evidence_items) == 1
    assert result.errors[0].filename == "broken.xlsx"
    assert result.errors[0].code == "corrupt_document"
