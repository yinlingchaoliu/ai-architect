#!/usr/bin/env python3
"""Portable local scaffolding and structural checks. Python 3.10+, standard library only."""
import argparse
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")
SECRET_NAME = re.compile(r"(^\.env($|\.)|(^|[-_.])(secret|credentials?)([-_.]|$)|\.(key|pem|p12|pfx)$)", re.I)
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".agents", ".codex", "logs", "backups"}


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def inside(root, relative):
    relative = str(relative)
    if not relative or Path(relative).is_absolute() or "\\" in relative:
        raise ValueError("A nonempty project-relative POSIX path is required")
    if ".." in Path(relative).parts or any(ord(c) < 32 for c in relative):
        raise ValueError("Parent traversal and control characters are not allowed")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path or symlink escapes the selected root")
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def catalog():
    return json.loads((PACKAGE / "assets/catalog.json").read_text())


def substitute(text, values):
    return TOKEN.sub(lambda m: str(values.get(m.group(1), m.group(0))), text)


def substitute_json(value, values):
    if isinstance(value, str):
        return substitute(value, values)
    if isinstance(value, list):
        return [substitute_json(item, values) for item in value]
    if isinstance(value, dict):
        return {key: substitute_json(item, values) for key, item in value.items()}
    return value


def create_files(files, dry_run=False):
    paths = [path for path, _ in files]
    if len(set(p.resolve() for p in paths)) != len(paths):
        raise ValueError("Duplicate output paths")
    if any(a != b and a.resolve().is_relative_to(b.resolve()) for a in paths for b in paths):
        raise ValueError("A file output is also another output's parent")
    for path in paths:
        if path.exists() or path.is_symlink():
            raise FileExistsError("Refusing to overwrite: " + str(path.name))
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError("Output ancestor is not a directory")
    if dry_run:
        return
    created, directories = [], []
    try:
        for path, data in files:
            missing = [p for p in path.parents if not p.exists()]
            path.parent.mkdir(parents=True, exist_ok=True)
            directories.extend(reversed(missing))
            with path.open("xb") as handle:
                created.append(path)
                handle.write(data)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        for path in reversed(directories):
            try:
                path.rmdir()
            except OSError:
                pass
        raise


def root_for(args):
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise ValueError("Project root must already exist")
    return root


def scaffold(args):
    root = root_for(args)
    data = catalog()
    spec = data["types"][args.type]
    for required in spec.get("requires", []):
        if not getattr(args, required, None):
            raise ValueError("This type requires --" + required)
    if args.step and not re.fullmatch(r"\d{2,}-[a-z0-9]+(?:-[a-z0-9]+)*", args.step):
        raise ValueError("--step must look like 01-example")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.name):
        raise ValueError("--name must be a lowercase slug")
    if not re.fullmatch(r"\d{2,}", args.run_id):
        raise ValueError("--run-id must be at least two digits")
    if args.date:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
            raise ValueError("--date must be YYYY-MM-DD")
        date.fromisoformat(args.date)
    architecture_dir = args.architecture_dir or ("docs/ai-archtect" if (root / "docs/ai-archtect").is_dir() else "docs/architecture")
    values = {"date": args.date or datetime.now().astimezone().date().isoformat(), "project": root.name,
              "title": args.title or (root.name + " · " + args.type), "step": args.step or "",
              "task_id": "S" + args.step.split("-", 1)[0] if args.step else "",
              "run_id": args.run_id, "name": args.name, "architecture_dir": architecture_dir,
              "task_dir": args.task_dir, "current_doc": args.current_doc}
    for key in ["architecture_dir", "task_dir", "current_doc"]:
        inside(root, values[key])
    prepared, report = [], []
    for item in spec["files"]:
        target = inside(root, substitute(item["path"], values))
        template = inside(PACKAGE, item["template"])
        if target.suffix != template.suffix:
            raise ValueError("Output extension must match the template")
        local_values = dict(values)
        if args.step:
            local_values["step_index_link"] = os.path.relpath(root / args.task_dir / args.step / "README.md", target.parent)
            local_values["step_plan_link"] = os.path.relpath(root / args.task_dir / args.step / "plan.md", target.parent)
        if template.suffix == ".json":
            content = json.dumps(substitute_json(json.loads(template.read_text()), local_values),
                                 ensure_ascii=False, indent=2) + "\n"
        else:
            content = substitute(template.read_text(), local_values)
        prepared.append((target, content.encode()))
        report.append({"path": str(target.relative_to(root)), "template": item["template"],
                       "unfilled": sorted(set(TOKEN.findall(content)))})
    create_files(prepared, args.dry_run)
    return {"status": "dry_run" if args.dry_run else "draft_created", "owner": spec["owner"],
            "contributors": spec.get("contributors", []), "files": report,
            "meaning": "Scaffold only; source analysis, authoring and semantic review remain required"}


def source_allowed(root, path):
    rel = path.relative_to(root)
    return (path.is_file() and not path.is_symlink() and not any(p in SKIP_DIRS for p in rel.parts)
            and not SECRET_NAME.search(path.name) and path.stat().st_size <= 5 * 1024 * 1024)


def snapshot(args):
    root = root_for(args)
    selected = set()
    excluded = []
    for name in args.path:
        path = inside(root, name)
        if not path.exists():
            raise ValueError("Selected source does not exist: " + name)
        candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
        for candidate in candidates:
            inside(root, candidate.relative_to(root))
            if source_allowed(root, candidate):
                selected.add(candidate)
            elif candidate.is_file():
                excluded.append(str(candidate.relative_to(root)))
    output = inside(root, args.output)
    if output in selected:
        raise ValueError("Snapshot cannot include its own output")
    if not selected:
        raise ValueError("No eligible source files selected")
    def git(*parts):
        try:
            result = subprocess.run(["git", "-C", str(root), *parts], capture_output=True, text=True)
        except FileNotFoundError:
            return None
        return result.stdout.strip() if result.returncode == 0 else None
    result = {"schema": "arch.snapshot.v1", "created_at": datetime.now().astimezone().isoformat(),
              "head": git("rev-parse", "HEAD"), "git_status": git("status", "--porcelain=v1"),
              "coverage": "selected file fingerprints only; not evidence of content inspection",
              "files": [{"path": str(p.relative_to(root)), "sha256": digest(p),
                         "bytes": p.stat().st_size, "inspection": "hash_only"} for p in sorted(selected)],
              "excluded": sorted(set(excluded))}
    create_files([(output, (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode())], args.dry_run)
    return {"status": "dry_run" if args.dry_run else "snapshot_created", "output": args.output,
            "files": len(selected), "excluded": result["excluded"], "content_inspection": "not_proven"}


def prose(text):
    """Ignore fenced code when resolving documentation links."""
    result, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None:
            result.append(line)
    return "\n".join(result)


def anchors(text):
    counts, result = {}, set()
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", prose(text), re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        result.add(slug + ("-" + str(number) if number else ""))
    return result


def document_errors(root, path, allow_draft=False):
    from urllib.parse import unquote
    text = path.read_text()
    errors = []
    if not allow_draft and TOKEN.search(text):
        errors.append("unfilled_template")
    if path.suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError:
            errors.append("invalid_json")
    if path.suffix == ".md":
        for target in re.findall(r"\]\(([^)]+)\)", prose(text)):
            target = target.strip().strip("<>")
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*://|mailto:", target):
                continue
            name, _, anchor = unquote(target).partition("#")
            name = re.sub(r":\d+$", "", name)
            relative = (path.parent / name) if name else path
            resolved = relative.resolve()
            if not resolved.is_relative_to(root.resolve()):
                errors.append("link_escapes_root: " + target)
            elif not relative.exists():
                errors.append("missing_link: " + target)
            elif anchor and relative.is_file() and relative.suffix == ".md" and anchor not in anchors(relative.read_text()):
                errors.append("missing_anchor: " + target)
    return errors


def check(args):
    root = root_for(args)
    files = set()
    for name in args.path:
        path = inside(root, name)
        if not path.exists():
            raise ValueError("Check input missing: " + name)
        candidates = path.rglob("*") if path.is_dir() else [path]
        for candidate in candidates:
            inside(root, candidate.relative_to(root))
            if candidate.is_file() and candidate.suffix in {".md", ".mmd", ".json"}:
                files.add(candidate)
    failures = []
    if not files:
        raise ValueError("No Markdown, Mermaid or JSON documents selected")
    for path in sorted(files):
        errors = document_errors(root, path, args.allow_draft)
        if errors:
            failures.append({"path": str(path.relative_to(root)), "errors": errors})
    stale = []
    if args.snapshot:
        record = json.loads(inside(root, args.snapshot).read_text())
        if record.get("schema") != "arch.snapshot.v1":
            raise ValueError("Unsupported snapshot schema; do not treat legacy snapshots as current proof")
        for item in record["files"]:
            path = inside(root, item["path"])
            if not path.is_file() or digest(path) != item["sha256"]:
                stale.append(item["path"])
    return {"status": "failed" if failures or stale else "passed", "structural_only": True,
            "documents_checked": len(files), "failures": failures, "stale_sources": stale,
            "semantic_review": "required", "mermaid_syntax_and_visual_review": "not_run"}


def package_check(args):
    data = catalog()
    failures = []
    registered = {item["id"] for item in data["subskills"]}
    for item in data["subskills"]:
        path = inside(PACKAGE, item["entry"])
        if not path.is_file() or not re.search(r"^name: " + re.escape(item["id"]) + r"$", path.read_text(), re.M):
            failures.append("invalid_subskill: " + item["id"])
    owned = set()
    for kind, spec in data["types"].items():
        if spec["owner"] not in registered or any(owner not in registered for owner in spec.get("contributors", [])):
            failures.append("unregistered_owner: " + kind)
        for item in spec["files"]:
            template = inside(PACKAGE, item["template"])
            template_parts = Path(item["template"]).parts
            if (len(template_parts) < 2 or template_parts[0] != "subskills"
                    or template_parts[1] not in {spec["owner"], *spec.get("contributors", [])}):
                failures.append("template_owner_mismatch: " + kind)
            owned.add(template)
            if not template.is_file():
                failures.append("missing_template: " + item["template"])
            elif template.suffix == ".json":
                json.loads(template.read_text())
    physical = set(PACKAGE.glob("subskills/*/assets/templates/*"))
    if physical != owned:
        failures.append("template_catalog_mismatch")
    for path in PACKAGE.rglob("*.md"):
        # Template links are resolved at their output location, checked by the
        # scaffold scenarios; they are not package-internal dependencies.
        if "templates" in path.parts and "assets" in path.parts:
            continue
        for error in document_errors(PACKAGE, path, allow_draft=True):
            failures.append(str(path.relative_to(PACKAGE)) + ": " + error)
    symlinks = [str(p.relative_to(PACKAGE)) for p in PACKAGE.rglob("*") if p.is_symlink()]
    if symlinks:
        failures.append("package_contains_symlinks")
    return {"status": "failed" if failures else "passed", "subskills": len(registered),
            "templates": len(owned), "scaffold_types": len(data["types"]), "failures": failures,
            "external_document_dependencies": [], "structural_only": True,
            "semantic_review": "required"}


def render(args):
    root = root_for(args)
    source, output = inside(root, args.source), inside(root, args.output)
    if source.suffix != ".mmd" or output.suffix not in {".svg", ".png"}:
        raise ValueError("Render expects .mmd input and .svg/.png output")
    if not source.is_file() or TOKEN.search(source.read_text()):
        raise ValueError("Render source is missing or unfilled")
    if output.exists() or output.is_symlink():
        raise FileExistsError("Refusing to overwrite render output")
    binary = shutil.which(args.mmdc) if args.mmdc else shutil.which("mmdc")
    if not binary:
        return {"status": "not_run", "reason": "mmdc_unavailable", "source_retained": args.source,
                "visual_review": "not_run"}
    with tempfile.TemporaryDirectory(prefix="arch-render-") as temp:
        temporary = Path(temp) / ("diagram" + output.suffix)
        command = [binary, "-i", str(source), "-o", str(temporary), "-c", str(PACKAGE / "assets/mermaid-config.json")]
        if args.puppeteer_config:
            command.extend(["-p", str(inside(root, args.puppeteer_config))])
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode or not temporary.exists():
            return {"status": "failed", "exit_code": result.returncode, "render_log": (result.stdout + result.stderr)[-2500:], "visual_review": "not_run"}
        create_files([(output, temporary.read_bytes())])
    return {"status": "passed", "source": args.source, "output": args.output,
            "source_sha256": digest(source), "output_sha256": digest(output), "visual_review": "not_run"}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog")
    commands.add_parser("package-check")
    p = commands.add_parser("scaffold")
    p.add_argument("--root", required=True)
    p.add_argument("--type", choices=sorted(catalog()["types"]), required=True)
    p.add_argument("--step")
    p.add_argument("--run-id", default="01")
    p.add_argument("--name", default="example")
    p.add_argument("--title")
    p.add_argument("--date", help="Client-local YYYY-MM-DD; pass explicitly if host timezone differs")
    p.add_argument("--architecture-dir")
    p.add_argument("--task-dir", default="docs/task")
    p.add_argument("--current-doc", default="docs/current-architecture.md")
    p.add_argument("--dry-run", action="store_true")
    p = commands.add_parser("snapshot")
    p.add_argument("--root", required=True)
    p.add_argument("--path", action="append", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--dry-run", action="store_true")
    p = commands.add_parser("check")
    p.add_argument("--root", required=True)
    p.add_argument("--path", action="append", required=True)
    p.add_argument("--snapshot")
    p.add_argument("--allow-draft", action="store_true")
    p = commands.add_parser("render")
    p.add_argument("--root", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--mmdc")
    p.add_argument("--puppeteer-config")
    return result


def main():
    args = parser().parse_args()
    handlers = {"catalog": lambda _: catalog(), "scaffold": scaffold, "snapshot": snapshot,
                "check": check, "package-check": package_check, "render": render}
    try:
        outcome = handlers[args.command](args)
        emit(outcome)
        return 1 if outcome.get("status") in {"failed", "not_run"} else 0
    except (ValueError, FileNotFoundError, FileExistsError, OSError, subprocess.TimeoutExpired, KeyError) as error:
        emit({"status": "error", "error_type": type(error).__name__, "message": str(error)})
        return 2


if __name__ == "__main__":
    sys.exit(main())
