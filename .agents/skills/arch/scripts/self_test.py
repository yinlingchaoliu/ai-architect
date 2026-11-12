#!/usr/bin/env python3
"""Exercise real file effects in a copied package and unrelated temporary project."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parents[1]


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="arch-portable-") as temp:
        area = Path(temp)
        root = area / "另一个项目 with spaces"
        root.mkdir()
        copied = root / ".agents/skills/arch"
        shutil.copytree(PACKAGE, copied, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        script = copied / "scripts/archkit.py"

        def run(*args, code=0):
            result = subprocess.run([sys.executable, str(script), *args], cwd=area,
                                    capture_output=True, text=True, timeout=15)
            assert result.returncode == code, (args, result.returncode, result.stdout, result.stderr)
            return json.loads(result.stdout)

        def passed(name):
            checks.append({"name": name, "status": "passed"})

        package = run("package-check")
        assert package["status"] == "passed" and package["external_document_dependencies"] == []
        passed("copied_package_closed_without_original_project")
        catalog = run("catalog")
        assert set(item["id"] for item in catalog["subskills"]) >= {"arch-source", "arch-current", "arch-step", "arch-run"}
        passed("typed_routes_and_template_owners_available")

        # Dry-run reports exact destinations and makes no project documents.
        before = set(root.rglob("*"))
        run("scaffold", "--root", str(root), "--type", "step", "--step", "01-example", "--dry-run")
        assert set(root.rglob("*")) == before
        passed("dry_run_has_no_file_effects")

        # Every type works with only the copied skill, never the original docs.
        for kind, spec in catalog["types"].items():
            fixture = area / ("type-" + kind)
            fixture.mkdir()
            outcome = run("scaffold", "--root", str(fixture), "--type", kind,
                          "--step", "01-example", "--date", "2026-11-12")
            assert outcome["status"] == "draft_created"
            assert len(outcome["files"]) == len(spec["files"])
            for entry in outcome["files"]:
                assert (fixture / entry["path"]).is_file()
        passed("all_document_types_scaffold_in_independent_empty_projects")

        quoted = area / 'Project "quoted"'
        quoted.mkdir()
        run("scaffold", "--root", str(quoted), "--type", "validation")
        escaped = json.loads((quoted / "docs/architecture/validation.json").read_text())
        assert escaped["project"] == quoted.name
        run("scaffold", "--root", str(quoted), "--type", "current", "--date", "2026-13-40", code=2)
        assert not (quoted / "docs/current-architecture.md").exists()
        passed("json_variables_escaped_and_invalid_date_rejected")

        step = run("scaffold", "--root", str(root), "--type", "step", "--step", "01-example")
        run_record = run("scaffold", "--root", str(root), "--type", "run", "--step", "01-example")
        assert len(step["files"]) == 3 and len(run_record["files"]) == 5
        draft = run("check", "--root", str(root), "--path", "docs/task", "--allow-draft")
        assert draft["status"] == "passed" and draft["semantic_review"] == "required"
        strict = run("check", "--root", str(root), "--path", "docs/task", code=1)
        assert any("unfilled_template" in item["errors"] for item in strict["failures"])
        passed("step_gateway_and_four_run_records_with_draft_rejection")

        # A collision in the last output prevents even the first output write.
        collision = root / "docs/task/02-collision/plan.md"
        collision.parent.mkdir(parents=True)
        collision.write_text("user-owned-original\n")
        result = run("scaffold", "--root", str(root), "--type", "step", "--step", "02-collision", code=2)
        assert result["error_type"] == "FileExistsError"
        assert collision.read_text() == "user-owned-original\n"
        assert not (root / "docs/task/02-collision.md").exists()
        assert not (collision.parent / "README.md").exists()
        passed("group_collision_preserves_user_file_and_writes_nothing")

        run("scaffold", "--root", str(root), "--type", "current", "--current-doc", "../escape.md", code=2)
        assert not (area / "escape.md").exists()
        outside = area / "outside"
        outside.mkdir()
        (root / "linked").symlink_to(outside, target_is_directory=True)
        run("scaffold", "--root", str(root), "--type", "architecture", "--architecture-dir", "linked", code=2)
        assert not list(outside.iterdir())
        passed("traversal_and_symlink_escape_rejected")

        # Selected file hashes are not advertised as a content audit.
        source = root / "src"
        source.mkdir()
        (source / "main.py").write_text("from service import execute\nexecute()\n")
        (source / "service.py").write_text("def execute():\n    return 'local-result'\n")
        (source / ".env").write_text("API_KEY=do-not-copy-fixture\n")
        (source / "credentials.json").write_text('{"token":"do-not-copy-fixture"}\n')
        snap = run("snapshot", "--root", str(root), "--path", "src", "--output", "evidence/source.json")
        record = json.loads((root / "evidence/source.json").read_text())
        assert snap["files"] == 2 and len(snap["excluded"]) == 2
        assert record["head"] is None
        assert all(item["inspection"] == "hash_only" for item in record["files"])
        assert "do-not-copy-fixture" not in (root / "evidence/source.json").read_text()
        passed("non_git_snapshot_excludes_secrets_and_keeps_hash_only_scope")

        report = root / "docs/fixture.md"
        report.write_text("# Fixture\n\nEvidence is selected and hash-only.\n")
        run("check", "--root", str(root), "--path", "docs/fixture.md", "--snapshot", "evidence/source.json")
        (source / "service.py").write_text("def execute():\n    raise RuntimeError('changed')\n")
        drift = run("check", "--root", str(root), "--path", "docs/fixture.md", "--snapshot", "evidence/source.json", code=1)
        assert drift["stale_sources"] == ["src/service.py"]
        passed("source_change_invalidates_snapshot")

        report.write_text("# Fixture\n\n[missing](absent.md)\n")
        broken = run("check", "--root", str(root), "--path", "docs/fixture.md", code=1)
        assert any("missing_link" in error for item in broken["failures"] for error in item["errors"])
        report.write_text("# Fixture\n\n[bad](fixture.md#not-present)\n")
        broken = run("check", "--root", str(root), "--path", "docs/fixture.md", code=1)
        assert any("missing_anchor" in error for item in broken["failures"] for error in item["errors"])
        passed("missing_file_and_heading_links_fail")

        run("check", "--root", str(root), "--path", "src/main.py", code=2)
        passed("empty_document_check_cannot_pass")

        diagram = run("scaffold", "--root", str(root), "--type", "diagram-sequence")
        no_renderer = run("render", "--root", str(root), "--source", diagram["files"][0]["path"],
                          "--output", "rendered.svg", "--mmdc", "arch-missing-renderer-fixture", code=1)
        assert no_renderer["status"] == "not_run" and not (root / "rendered.svg").exists()
        passed("missing_renderer_reports_not_run_without_fake_image")

        template = copied / catalog["types"]["current"]["files"][0]["template"]
        old = template.read_bytes()
        template.unlink()
        broken = run("package-check", code=1)
        assert any("missing_template" in error for error in broken["failures"])
        template.write_bytes(old)
        passed("missing_owned_template_detected")

    print(json.dumps({"status": "passed", "checks": checks, "count": len(checks),
                      "scope": "stdlib helpers, filesystem boundaries and copied-package portability",
                      "independent_model_evaluation": "not_run"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
