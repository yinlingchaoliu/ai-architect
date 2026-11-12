"""Check this documentation rewrite only. No product imports, model/network calls, or env reads."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import tarfile
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[6]
BASE = ROOT / 'docs/task/02-platform-contracts-and-skeleton'
DESIGN = BASE / 'llm'
RUN = BASE / 'run-01/rewrite-01'
EVIDENCE = RUN / 'evidence'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text())

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

# Receipts are created last; placeholders make self-references valid on the first run.
for name in ['document-check.json', 'write-set.json']:
    fp = EVIDENCE / name
    if not fp.exists():
        dump(fp, {})

baseline = load(EVIDENCE / 'baseline.json')
sources = load(DESIGN / 'source-baseline.json')
refs = load(DESIGN / 'reference-snapshot.json')
formal_files = sorted(x for x in DESIGN.rglob('*') if x.is_file())
run_files = sorted(x for x in RUN.rglob('*') if x.is_file())
markdowns = [x for x in formal_files + run_files if x.suffix == '.md'] + [BASE / 'run-01/README.md']
errors = []
link_count = 0
python_blocks = 0
mermaid_blocks = []
for fp in markdowns:
    text = fp.read_text()
    fences = list(re.finditer(r'^```([^\n]*)\n', text, re.M))
    if len(fences) % 2:
        errors.append(f'unbalanced code fences: {fp.relative_to(ROOT)}')
    for i in range(0, len(fences) - 1, 2):
        label = fences[i].group(1).strip()
        body = text[fences[i].end():fences[i + 1].start()]
        if label == 'python':
            python_blocks += 1
            try:
                ast.parse(body)
            except SyntaxError as exc:
                errors.append(f'python syntax {fp.relative_to(ROOT)}: {exc}')
        if label == 'mermaid' and fp.is_relative_to(DESIGN):
            mermaid_blocks.append((fp, body.strip()))
    for label, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text):
        target = target.strip().strip('<>')
        if target.startswith(('http://', 'https://', 'mailto:', 'plugin:', 'artifact:')):
            continue
        local = target.split('#', 1)[0]
        if not local:
            continue
        path = Path(unquote(local))
        path = path if path.is_absolute() else fp.parent / path
        link_count += 1
        if not path.exists():
            errors.append(f'broken link {fp.relative_to(ROOT)}: {target}')
    if re.search(r'\{\{[^}]+\}\}', text):
        errors.append(f'unfilled template {fp.relative_to(ROOT)}')
    if any(line.rstrip() != line for line in text.splitlines()):
        errors.append(f'trailing whitespace {fp.relative_to(ROOT)}')

diagrams = sorted((DESIGN / 'diagrams').glob('*.mmd'))
for fp in diagrams:
    matches = [str(md.relative_to(ROOT)) for md, text in mermaid_blocks if text == fp.read_text().strip()]
    if len(matches) != 1:
        errors.append(f'diagram has {len(matches)} exact inline matches: {fp.name}')
if len(diagrams) != 5 or len(mermaid_blocks) != 5:
    errors.append('expected exactly five diagram sources and five inline diagrams')

json_files = [x for x in formal_files + run_files if x.suffix == '.json']
for fp in json_files:
    try:
        load(fp)
    except (ValueError, UnicodeDecodeError) as exc:
        errors.append(f'JSON {fp.relative_to(ROOT)}: {exc}')
examples = load(DESIGN / 'examples/unified-model-requests.json')
expected_types = {'llm', 'text-embedding', 'rerank', 'speech2text', 'moderation', 'tts'}
requests = examples['requests']
if len(requests) != 6 or {x['model_type'] for x in requests} != expected_types:
    errors.append('six model type examples not covered exactly once')
required_fields = {'llm': {'messages'}, 'text-embedding': {'texts', 'purpose'}, 'rerank': {'query', 'documents'}, 'speech2text': {'audio_ref'}, 'moderation': {'items'}, 'tts': {'text'}}
for req in requests:
    if not required_fields[req['model_type']] <= req.keys():
        errors.append(f'example fields missing for {req["model_type"]}')
    if not req.get('model_ref') or not isinstance(req.get('parameters'), dict):
        errors.append(f'typed config missing for {req["model_type"]}')
if examples['status'] != 'design_examples_only':
    errors.append('examples must remain explicitly design only')

textual = [x for x in formal_files + run_files if x.suffix in {'.md', '.json', '.mmd', '.py'}]
secret_hits = []
for fp in textual:
    if re.search(r'\bsk-[A-Za-z0-9_-]{20,}\b', fp.read_text()):
        secret_hits.append(str(fp.relative_to(ROOT)))
if secret_hits:
    errors.append('credential-like string found in authorized textual artifacts')
formal_texts = [(x, x.read_text()) for x in formal_files if x.suffix in {'.md', '.json', '.mmd'}]
future_mentions = [(str(x.relative_to(DESIGN)), line) for x, text in formal_texts for line in text.splitlines() if 'LiteLLM' in line]
if len(future_mentions) != 1 or future_mentions[0][0] != '05-open-source-reference.md':
    errors.append('future extension must be one reference-only mention')
for fp, text in formal_texts:
    if re.search(r'Bifrost|bifrost|Portkey|portkey|GatewayDriver|ProviderDriver|GatewayMode', text):
        errors.append(f'obsolete gateway design in {fp.relative_to(ROOT)}')

source_mismatches = [x['path'] for x in baseline['sources'] if sha(ROOT / x['path']) != x['sha256']]
source_mismatches += [x['path'] for x in sources['files'] if sha(ROOT / x['path']) != x['sha256']]
if source_mismatches:
    errors.append(f'project source drift: {sorted(set(source_mismatches))}')
reference_root = Path(refs['deepseek_harness']['root'])
reference_mismatches = [x['path'] for x in refs['deepseek_harness']['files'] if sha(reference_root / x['path']) != x['sha256']]
framework_mismatches = [x['path'] for x in refs['langchain']['files'] if sha(Path(x['path'])) != x['sha256']]
if reference_mismatches or framework_mismatches:
    errors.append('reference/framework fingerprint drift')
current_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
reference_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=reference_root, text=True).strip()
reference_status = subprocess.check_output(['git', 'status', '--short'], cwd=reference_root, text=True)
if current_head != baseline['head'] or reference_head != baseline['reference_head'] or reference_status:
    errors.append('source/reference HEAD or reference status drift')

archive_entries = {}
with tarfile.open(EVIDENCE / 'llm-before.tar.gz', 'r:gz') as archive:
    for member in archive.getmembers():
        if member.isfile():
            archive_entries[member.name] = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
for entry in baseline['llm_before']:
    key = str(Path(entry['path']).relative_to(DESIGN.relative_to(ROOT)))
    if archive_entries.get(key) != entry['sha256']:
        errors.append(f'archive mismatch {key}')
if len(archive_entries) != len(baseline['llm_before']):
    errors.append('archive member count differs')

observed_drift = []
for x in baseline['protected_other_docs']:
    current = sha(ROOT / x['path'])
    if current != x['sha256']:
        observed_drift.append({'path': x['path'], 'before_sha256': x['sha256'], 'observed_sha256': current})
known_drift = load(EVIDENCE / 'outside-write-set-observations.json')['all_observed_changes']
known_drift_core = [{k: x[k] for k in ['path', 'before_sha256', 'observed_sha256']} for x in known_drift]
if observed_drift != known_drift_core:
    errors.append('unrecorded protected-doc drift; preserve and inspect before finishing')

summary = {
    'date': '2026-11-12', 'design_version': '0.2',
    'status': 'passed' if not errors else 'failed',
    'scope': 'documentation consistency and source/backup integrity only',
    'review_mode': 'self_review',
    'checks': {
        'markdown_files': len(markdowns), 'local_links_checked': link_count,
        'python_examples_ast_only': python_blocks, 'json_files_parsed': len(json_files),
        'diagram_sources_equal_inline': len(diagrams), 'model_type_examples': len(requests),
        'formal_design_files': len(formal_files), 'project_source_files': len(sources['files']),
        'reference_source_files': len(refs['deepseek_harness']['files']),
        'framework_source_files': len(refs['langchain']['files']),
        'archive_files_verified': len(archive_entries),
        'future_extension_reference_mentions': len(future_mentions),
        'credential_pattern_hits': len(secret_hits),
        'protected_docs_checked': len(baseline['protected_other_docs']),
        'protected_docs_unchanged': len(baseline['protected_other_docs']) - len(observed_drift),
    },
    'outside_write_set_observations': observed_drift,
    'outside_observation_action': 'preserved; writer not determined; this run did not write/revert those paths',
    'errors': errors,
    'not_run': ['API imports/execution of proposed model service', 'new product tests', 'new provider calls', 'reference TypeScript tests', 'load/concurrency tests', 'billing/persistence/fault tests', 'Mermaid render/visual review', 'independent review', 'production or business validation'],
    'historical_probe': {'path': '../run-01/evidence/langchain-mechanism-results.json', 'rerun': False, 'scope': 'three offline framework mechanism observations only'},
}
dump(DESIGN / 'design-validation.json', summary)
manifest_files = [x for x in formal_files if x.name != 'design-manifest.json']
manifest = {'date': '2026-11-12', 'design_version': '0.2', 'scope': 'current formal llm design; manifest itself excluded', 'files': [{'path': str(x.relative_to(DESIGN)), 'sha256': sha(x)} for x in manifest_files]}
dump(DESIGN / 'design-manifest.json', manifest)
dump(EVIDENCE / 'document-check.json', dict(summary, formal_manifest_sha256=sha(DESIGN / 'design-manifest.json'), checker_sha256=sha(Path(__file__))))
owned = sorted(set(formal_files + run_files + [BASE / 'run-01/README.md']))
write_set = {'date': '2026-11-12', 'scope': 'paths written by this documentation rewrite; write-set receipt itself excluded from fingerprints', 'files': [{'path': str(x.relative_to(ROOT)), 'sha256': sha(x)} for x in owned if x != EVIDENCE / 'write-set.json'], 'excluded_observed_drift': [x['path'] for x in observed_drift], 'no_product_or_other_task_writes': True}
dump(EVIDENCE / 'write-set.json', write_set)
# Independent read-back after receipts and manifest have been written.
for entry in load(DESIGN / 'design-manifest.json')['files']:
    assert sha(DESIGN / entry['path']) == entry['sha256']
for entry in load(EVIDENCE / 'write-set.json')['files']:
    assert sha(ROOT / entry['path']) == entry['sha256']
print(json.dumps({'status': summary['status'], 'checks': summary['checks'], 'outside_observations': [x['path'] for x in observed_drift], 'errors': errors}, ensure_ascii=False))
raise SystemExit(1 if errors else 0)
