"""Local design checks only: no model calls, no private configuration reads.

Only writes evidence files under this LLM v2 directory. It observes other
worktree paths via metadata and validates explicitly selected source hashes.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

OUT = Path(__file__).resolve().parent
DESIGN = OUT.parents[1]
ROOT = DESIGN.parents[3]
PREFIX = str(DESIGN.relative_to(ROOT)) + "/"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def run() -> None:
    baseline = json.loads((OUT / "baseline.json").read_text())
    observations = []
    for name, initial in baseline["outside_files_metadata_only"].items():
        path = ROOT / name
        if not path.exists():
            observations.append({"path": name, "observation": "missing_since_initial_metadata"})
        elif path.is_file():
            stat = path.stat()
            if stat.st_size != initial["size"] or stat.st_mtime_ns != initial["mtime_ns"]:
                observations.append({"path": name, "observation": "metadata_changed"})
    write_json("outside-observations.json", {
        "scope": "metadata only; no attribution from metadata",
        "handled": "observed parallel work preserved; dependency declarations reread; no restore performed",
        "paths": observations,
    })

    structural = subprocess.run([
        sys.executable, str(ROOT / ".agents/skills/arch/scripts/archkit.py"), "check",
        "--root", str(ROOT), "--path", str(DESIGN.relative_to(ROOT)),
    ], capture_output=True, text=True)
    structure = json.loads(structural.stdout)
    errors = []
    if structural.returncode != 0:
        errors.append({"kind": "archkit", "details": structure})

    sources = json.loads((OUT / "sources.json").read_text())
    source_drift = []
    for entry in sources["selected_sources"]:
        path = Path(entry["path"])
        if not path.is_file() or digest(path) != entry["sha256"]:
            source_drift.append(entry["path"])
    if source_drift:
        errors.append({"kind": "selected_source_drift", "paths": source_drift})

    python_files = []
    for path in DESIGN.rglob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
        python_files.append(str(path.relative_to(ROOT)))
    python_blocks = 0
    for path in DESIGN.rglob("*.md"):
        for block in re.findall(r"```python\n(.*?)\n```", path.read_text(), flags=re.S):
            ast.parse(block, filename=str(path) + ":example")
            python_blocks += 1

    config = yaml.safe_load((DESIGN / "examples/profiles.yaml").read_text())
    assert config["mode"] == "development"
    assert config["profiles"][0]["reasoning"]["mode"] == "off"
    assert config["transports"][0]["sdk_max_retries"] == 0
    providers = {p["revision"] for p in config["providers"]}
    profiles = {p["revision"] for p in config["profiles"]}
    assert all(p["provider_revision"] in providers for p in config["profiles"])
    assert all(value in profiles for value in config["aliases"].values())
    policy = config["policies"][0]
    assert policy["admission"]["rpm"] is policy["admission"]["tpm"] is None
    assert policy["timeouts"]["total_ms"] > policy["timeouts"]["queue_ms"]
    assert config["providers"][0]["credential_ref"].startswith("env:")

    diagram_pairs = {
        "layers": "02-layered-architecture.md",
        "deployment": "02-layered-architecture.md",
        "invocation": "03-contracts-and-api.md",
        "call-state": "05-concurrency-and-reliability.md",
        "config-lifecycle": "06-config-and-lifecycle.md",
    }
    diagrams = []
    for name, document in diagram_pairs.items():
        source = (DESIGN / "diagrams" / (name + ".mmd")).read_text().strip()
        assert source in (DESIGN / document).read_text(), name
        diagrams.append({"name": name, "embedded_source_matches": True})

    secret_pattern_paths, whitespace_paths, placeholders = [], [], []
    for path in DESIGN.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text()
        if re.search(r"sk-[A-Za-z0-9_-]{20,}", text):
            secret_pattern_paths.append(str(path.relative_to(ROOT)))
        if any(line.rstrip(" \t") != line for line in text.splitlines()):
            whitespace_paths.append(str(path.relative_to(ROOT)))
        if "{{" in text or "}}" in text:
            # JSON/dict source can contain adjacent braces; only template variables count.
            if re.search(r"\{\{\s*[A-Za-z_][A-Za-z_0-9]*\s*\}\}", text):
                placeholders.append(str(path.relative_to(ROOT)))
    if secret_pattern_paths or whitespace_paths or placeholders:
        errors.append({"kind": "artifact_content", "secret_pattern_paths": secret_pattern_paths,
                       "whitespace_paths": whitespace_paths, "template_paths": placeholders})

    probe = json.loads((OUT / "langchain-payload-probe.json").read_text())
    assert probe["provider_called"] is False
    assert probe["input_has_reasoning_content"] is True
    assert probe["payload_has_reasoning_content"] is False
    assert probe["payload_has_tool_call"] is True

    manifest_path = OUT / "write-set.json"
    report_path = OUT / "document-check.json"
    manifest = {
        "kind": "design_artifact_write_set",
        "allowed_repository_prefix": PREFIX,
        "scope": "only these design artifacts were written; parallel work is listed separately",
        "self_excluded": [str(manifest_path.relative_to(ROOT)), str(report_path.relative_to(ROOT))],
        "files": [{"path": str(path.relative_to(ROOT)), "sha256": digest(path), "bytes": path.stat().st_size}
                  for path in sorted(DESIGN.rglob("*"))
                  if path.is_file() and path not in (manifest_path, report_path)],
    }
    assert all(entry["path"].startswith(PREFIX) for entry in manifest["files"])
    write_json("write-set.json", manifest)
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not errors else "failed",
        "kind": "design_review_only",
        "archkit_structural": structure,
        "selected_source_fingerprints": {"count": len(sources["selected_sources"]), "drift": source_drift},
        "python_sources_ast_only": python_files,
        "markdown_python_examples_ast_only": python_blocks,
        "yaml": {"parsed": True, "references_checked": True, "mode": "development", "production_ready": False},
        "mermaid_embedded_sources": diagrams,
        "mermaid_parser_render_visual": "not_run; mmdc unavailable; manual semantic review only",
        "new_secret_pattern_scan": {"matches": secret_pattern_paths, "private_files_read": False},
        "parallel_outside_metadata_observations": len(observations),
        "repository_write_prefix": PREFIX,
        "manifest_sha256": digest(manifest_path),
        "semantic_review": {"mode": "self_review", "status": "completed", "independent_review": "not_run", "user_acceptance": "pending"},
        "implementation": "not_run",
        "runtime_regression_tests": "not_run",
        "provider_calls": "not_run",
        "performance_load_tests": "not_run",
        "errors": errors,
    }
    write_json("document-check.json", report)
    print(json.dumps({"status": report["status"], "documents_checked": structure["documents_checked"],
                      "source_fingerprints": len(sources["selected_sources"]),
                      "python_example_blocks": python_blocks,
                      "diagram_pairs": len(diagrams),
                      "write_set_files": len(manifest["files"]),
                      "parallel_observations": len(observations), "errors": errors}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
