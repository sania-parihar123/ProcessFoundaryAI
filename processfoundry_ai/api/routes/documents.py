
"""API routes for uploading and listing project documents."""

import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.models.document import DocumentCreate, DocumentRead
from processfoundry_ai.repositories.document_repository import DocumentRepository
from processfoundry_ai.repositories.project_repository import ProjectRepository


router = APIRouter()

# Store uploaded files in the project root.
UPLOAD_DIR = Path("storage") / "uploads"

# Maximum upload size: 10 MB.
MAX_FILE_SIZE = 10 * 1024 * 1024

# Supported file extensions and MIME types.
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
    ".xls": "application/vnd.ms-excel",
    ".txt": "text/plain",
}

ALLOWED_EXTENSIONS = set(MIME_TYPES)


def get_config() -> DatabaseConfig:
    """Load database configuration."""
    return DatabaseConfig.from_env()


def validate_file(filename: str, content: bytes) -> str:
    """Validate the file extension, content signature, and size."""

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Supported file types: PDF, DOCX, TXT, XLSX, and XLS.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB.",
        )

    # Check basic file signatures.
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not look like a PDF.",
        )

    if extension in {".docx", ".xlsx"} and not content.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not look like a valid Office file.",
        )

    if extension == ".xls" and not content.startswith(
        b"\xD0\xCF\x11\xE0"
    ):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not look like an XLS file.",
        )

    if extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content.decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file does not look like valid text.",
                )

    return extension


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
):
    """Upload a supported document and save its metadata."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    # Prevent directory traversal through the supplied filename.
    filename = file.filename.replace("\\", "/").split("/")[-1]

    if not filename or filename in {".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    try:
        # Read at most 10 MB plus one byte to detect oversized uploads.
        content = await file.read(MAX_FILE_SIZE + 1)
        extension = validate_file(filename, content)

        config = get_config()

        # Ensure the target project exists.
        project = ProjectRepository(config).get_by_id(project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        document_id = str(uuid4())
        checksum = hashlib.sha256(content).hexdigest()

        # Store files using generated names, not user-supplied paths.
        project_dir = UPLOAD_DIR / document_id
        file_path = project_dir / f"{document_id}{extension}"

        document = DocumentCreate(
            id=document_id,
            project_id=project_id,
            filename=filename,
            mime_type=MIME_TYPES[extension],
            checksum=checksum,
            version="1",
            storage_path=file_path.as_posix(),
        )

        # Save the file, then its metadata.
        project_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        try:
            saved_document = DocumentRepository(config).create(document)
            return saved_document

        except SQLAlchemyError:
            # Remove the file if the metadata could not be saved.
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=503,
                detail="Could not save document metadata to the database.",
            )

    except HTTPException:
        raise

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not access the project or database.",
        )

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Could not store the uploaded file.",
        )

    finally:
        await file.close()


@router.get("", response_model=list[DocumentRead])
def list_project_documents(project_id: str):
    """List documents belonging to a project."""

    config = get_config()

    try:
        project = ProjectRepository(config).get_by_id(project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        return DocumentRepository(config).list_by_project(project_id)

    except HTTPException:
        raise

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve project documents.",
        )
