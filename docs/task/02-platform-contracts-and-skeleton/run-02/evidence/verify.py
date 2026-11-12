"""Read back the scoped delivery, without loading or copying private config."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent
RUN = OUT.parent.relative_to(ROOT).as_posix() + "/"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def scoped(path):
    return (path.startswith(("lib_llm/", "lib_request/", RUN))
            or path in {"requirements.txt", "tests/s01/test_ui_rag.py"})


def main():
    baseline = json.loads((OUT / "baseline.json").read_text())
    checks = {}
    failures = []
    tracked_changes = git("diff", "--name-only", "HEAD", "-z").decode().strip("\0").split("\0")
    new = git("ls-files", "--others", "--exclude-standard", "-z").decode().strip("\0").split("\0")
    candidates = sorted(set(p for p in tracked_changes + new if p))
    outside = [p for p in candidates if not scoped(p)]
    approved = {p: h for p, h in baseline["selected_before_hashes"].items()
                if "/llmv2/" in p}
    checks["approved_design_unchanged"] = bool(approved) and all(
        (ROOT / p).is_file() and digest((ROOT / p).read_bytes()) == h for p, h in approved.items())
    checks["approved_design_files"] = len(approved)
    before_requirements = git("show", baseline["head"] + ":requirements.txt")
    checks["requirements_only_local_entry"] = ((ROOT / "requirements.txt").read_bytes()
        == before_requirements.replace(b"-e ./lib_request", b"-e ./lib_llm\n-e ./lib_request", 1))
    before_test = git("show", baseline["head"] + ":tests/s01/test_ui_rag.py").decode()
    after_test = (ROOT / "tests/s01/test_ui_rag.py").read_text()
    marker = "def test_request_sdk_uses_configured_model_without_logging_credentials"
    checks["s01_only_affected_test_changed"] = before_test.split(marker)[0] == after_test.split(marker)[0]
    sources = list((ROOT / "lib_llm/src").rglob("*.py")) + list((ROOT / "lib_request/src/lib_request").rglob("*.py"))
    for p in sources:
        tree = ast.parse(p.read_text())
        if "lib_request/src/" in p.as_posix():
            for n in ast.walk(tree):
                modules = [x.name for x in n.names] if isinstance(n, ast.Import) else [n.module or ""] if isinstance(n, ast.ImportFrom) else []
                if any(m.split(".")[0] in {"os", "dotenv", "openai", "requests"} for m in modules):
                    failures.append("lib_request dependency boundary: " + str(p.relative_to(ROOT)))
        elif p.name != "config.py":
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and n.module in {"os", "dotenv"}:
                    failures.append("environment import outside config: " + str(p.relative_to(ROOT)))
                if isinstance(n, ast.Attribute) and n.attr in {"getenv", "environ", "dotenv_values", "load_dotenv"}:
                    failures.append("environment access outside config: " + str(p.relative_to(ROOT)))
    checks["python_source_parsed"] = len(sources)
    checks["source_dependency_boundary"] = not failures
    checks["package_toml_parsed"] = all(tomllib.loads((ROOT / p).read_text()) for p in
                                          ["lib_llm/pyproject.toml", "lib_request/pyproject.toml"])
    installed = {}
    for name in ["lib-llm", "lib_request-sdk", "langchain", "langchain-core", "langchain-openai", "langgraph", "openai", "httpx"]:
        d = metadata.distribution(name)
        installed[name] = {"version": d.version, "requires": d.requires}
        if name in {"lib-llm", "lib_request-sdk"}:
            installed[name]["direct_url"] = json.loads(d.read_text("direct_url.json"))
    write("installed-packages.json", installed)
    checks["editable_install_source_parity"] = all(
        installed[name]["direct_url"].get("dir_info", {}).get("editable") is True
        and installed[name]["direct_url"]["url"] == (ROOT / folder).as_uri()
        for name, folder in [("lib-llm", "lib_llm"), ("lib_request-sdk", "lib_request")])
    checks["pip_check"] = (OUT / "pip-check.log").read_text().strip() == "No broken requirements found."
    xml = ET.parse(OUT / "tests.xml").getroot()
    cases = xml.findall(".//testcase")
    tests = {"tests": len(cases), "failures": len(xml.findall(".//failure")),
             "errors": len(xml.findall(".//error")), "skipped": len(xml.findall(".//skipped"))}
    write("test-summary.json", tests)
    checks["regression"] = tests["tests"] == 56 and not any(tests[k] for k in ("failures", "errors", "skipped"))
    live = json.loads((OUT / "live-model.json").read_text())
    checks["live_candidate_sources_match"] = bool(live.get("candidate_sources")) and all(
        digest((ROOT / p).read_bytes()) == h for p, h in live["candidate_sources"].items())
    checks["live_three_checks"] = (live["status"] == "passed" and len(live["checks"]) == 3
        and all(c["passed"] for c in live["checks"]) and live.get("runtime_closed") is True)
    restored = []
    with tempfile.TemporaryDirectory(prefix="s02-rollback-proof-") as temp:
        for p in tracked_changes:
            if not scoped(p) or p.startswith(RUN):
                continue
            blob = git("show", baseline["head"] + ":" + p)
            dest = Path(temp) / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(blob)
            assert digest(dest.read_bytes()) == digest(blob)
            restored.append(p)
        assert b"-e ./lib_llm" not in (Path(temp) / "requirements.txt").read_bytes()
    checks["rollback_restore"] = {"status": "passed", "method": "HEAD blobs restored in temporary directory only",
                                  "files": restored, "working_tree_rolled_back": False}
    own = [p for p in candidates if scoped(p) and (ROOT / p).is_file()]
    # Exclude self-referential reports from the candidate fingerprint.
    exclude = {str((OUT / n).relative_to(ROOT)) for n in ["verification.json", "write-set.json", "doc-check.log"]}
    fingerprint = {p: digest((ROOT / p).read_bytes()) for p in own if p not in exclude}
    suspicious = []
    for p in own:
        if re.search(rb"sk-[a-f0-9]{30,}", (ROOT / p).read_bytes()):
            suspicious.append(p)
    checks["credential_pattern_scan"] = not suspicious
    semantic_paths = [p for p in tracked_changes if scoped(p) and not p.startswith(RUN + "evidence/")]
    diff = subprocess.run(["git", "diff", "--check", "HEAD", "--", *semantic_paths], cwd=ROOT,
                          capture_output=True, text=True)
    checks["tracked_diff_whitespace"] = diff.returncode == 0
    (OUT / "diff-check.log").write_text(diff.stdout + diff.stderr)
    doc = json.loads((OUT / "doc-check.log").read_text())
    checks["document_structure"] = doc["status"] == "passed"
    for name, value in checks.items():
        if value is False:
            failures.append(name)
    write("write-set.json", {"baseline_head": baseline["head"], "hashes": fingerprint,
        "fingerprint_exclusions": sorted(exclude), "outside_scope_preserved": outside,
        "note": "Scope membership is not authorship; parallel additions inside scope may be included. Private and ignored files excluded."})
    receipt = {"status": "passed" if not failures else "failed", "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks, "failures": failures, "test_summary": tests,
        "outside_scope_changes_preserved": outside, "private_configuration": "not opened or hashed",
        "semantic_review": "current executing Agent self-review, see 03-review.md",
        "production_validation": "not_run", "independent_review": "not_run"}
    write("verification.json", receipt)
    # Independent byte read-back of every fingerprinted candidate artifact.
    readback = json.loads((OUT / "write-set.json").read_text())["hashes"]
    assert all(digest((ROOT / p).read_bytes()) == h for p, h in readback.items())
    print(json.dumps({"status": receipt["status"], "tests": tests, "failures": failures,
                      "outside_scope_preserved": outside, "fingerprinted_files": len(readback)}))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
