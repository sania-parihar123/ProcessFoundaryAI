from pathlib import Path
import json

from requirements_artifacts.document_builder import build_documents
from requirements_artifacts.requirements_builder import build_requirements


def main() -> None:
    artifacts_dir = Path(__file__).resolve().parent
    state_update_path = artifacts_dir / "samples" / "demo_state_update.json"
    state_update = json.loads(state_update_path.read_text(encoding="utf-8"))
    requirements = build_requirements(state_update)
    documents = build_documents(state_update, requirements)

    output_dir = artifacts_dir / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, markdown in documents.items():
        output_path = output_dir / f"{name}.md"
        output_path.write_text(markdown, encoding="utf-8")
        print(f"{output_path.name}: {len(markdown.splitlines())} lines")


if __name__ == "__main__":
    main()
