"""Check deliverable hashes, DOCX containers and evaluation-case schema (not model quality)."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    directory = ROOT / 'docs' / '课程提交'
    manifest = json.loads((directory / '文件校验SHA256.json').read_text(encoding='utf-8'))
    errors = []
    for name, expected in manifest.items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()):
            errors.append('Invalid manifest path: ' + name)
        elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append('Missing or changed deliverable: ' + name)
        elif path.suffix == '.docx':
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None or 'word/document.xml' not in archive.namelist():
                    errors.append('Invalid DOCX container: ' + name)
    cases = json.loads((ROOT / 'tests/eval_cases.json').read_text(encoding='utf-8'))
    fields = {'id', 'category', 'question', 'expected_tools', 'expected_behavior', 'pass_criteria'}
    if len(cases) != 30 or len({case['id'] for case in cases}) != 30:
        errors.append('Expected 30 unique evaluation cases')
    for case in cases:
        if not fields.issubset(case) or not isinstance(case.get('expected_tools'), list):
            errors.append('Invalid evaluation case: ' + str(case.get('id')))
    print(json.dumps({'deliverables_checked': len(manifest), 'evaluation_cases_schema_checked': len(cases),
                      'status': 'FAIL' if errors else 'PASS', 'errors': errors,
                      'limits': 'Hash/container/schema checks do not establish business validity, visual quality or model accuracy.'},
                     ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
