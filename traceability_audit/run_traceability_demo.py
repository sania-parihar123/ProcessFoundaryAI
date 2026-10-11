"""Demo. Run from the folder above this one:
    python -m traceability_audit.run_traceability_demo [state_update.json] [requirements.json]
Optional files: your real member2/out/demo_state_update.json and requirements_artifacts/out/demo_requirements.json
(requirements file may be a list, or {"requirements": [...], "tests": [...]}).
"""
import json
import sys
from pathlib import Path

from .audit_log import AuditLog
from .public_api import run_traceability
from .views import impact_report

HERE = Path(__file__).parent


def _load_reqs(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, []
    return data.get("requirements", []), data.get("tests", [])


def main() -> None:
    state_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "samples" / "demo_state_update.json"
    req_path = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "samples" / "demo_requirements.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    reqs, tests = _load_reqs(req_path)
    print(f"State file: {state_path}\nRequirements file: {req_path}")

    audit = AuditLog(state.get("project_id", "project"))
    audit.record("run_started", "system", "workflow")
    result = run_traceability(state, reqs, tests, audit=audit)
    rep = result["report"]
    print("Nodes:", rep["node_counts"])
    print(f"Validation: {'PASS' if rep['ok'] else 'FAIL'} ({rep['errors']} errors, {rep['warnings']} warnings)")
    for f in rep["findings"]:
        print(f"  [{f['severity']}] {f['code']} {f['node_id']}")
    print("Audit events:", len(audit.events), "| chain:", result["audit_verify"])

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    for name, text in result["documents"].items():
        (out / name).write_text(text, encoding="utf-8")
    ev = result["graph"].of_type("evidence")
    if ev:
        (out / "IMPACT_EXAMPLE.md").write_text(impact_report(result["graph"], ev[0]), encoding="utf-8")
    audit.save(out / "audit_log.json")
    print("Wrote:", ", ".join(sorted(p.name for p in out.iterdir())))


if __name__ == "__main__":
    main()
