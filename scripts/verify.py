"""Run reproducible offline checks and retain evidence; exit nonzero on failure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default='artifacts/verification')
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Do not accidentally report counts from an earlier successful invocation.
    (output / 'pytest.xml').unlink(missing_ok=True)
    env = os.environ.copy()
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['DOTENV_DISABLED'] = '1'
    env['LLM_API_KEY'] = env['EMBED_API_KEY'] = 'offline-test'
    env['LLM_BASE_URL'] = env['EMBED_BASE_URL'] = 'http://127.0.0.1:1/v1'
    env['ELIGIBILITY_SECRET'] = 'offline-verification-secret'
    node = shutil.which('node') or 'node'
    commands = [
        ('syntax', [sys.executable, '-m', 'compileall', '-q', 'app', 'scripts', 'tests']),
        ('backend', [sys.executable, '-m', 'pytest', 'tests', '-q',
                     '-o', 'faulthandler_timeout=30', '--junitxml=' + str(output / 'pytest.xml')]),
        ('frontend', [node, '--test', 'tests/test_stream.cjs']),
        ('documents', [sys.executable, 'scripts/verify_docs.py']),
    ]
    checks = []
    for name, command in commands:
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace', timeout=180)
            code, log = result.returncode, result.stdout + result.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            code, log = 1, str(exc)
        (output / (name + '.txt')).write_text(log, encoding='utf-8')
        checks.append({'name': name, 'command': command, 'exit_code': code,
                       'status': 'PASS' if code == 0 else 'FAIL', 'log': name + '.txt'})
        print(name + ': ' + checks[-1]['status'])
    counts = {}
    if (output / 'pytest.xml').exists():
        suites = ET.parse(output / 'pytest.xml').getroot().iter('testsuite')
        for suite in suites:
            for key in ('tests', 'failures', 'errors', 'skipped'):
                counts[key] = counts.get(key, 0) + int(suite.get(key, 0))
    files = sorted(p for folder in ('app', 'scripts', 'tests', 'static')
                   for p in (ROOT / folder).rglob('*')
                   if p.is_file() and p.suffix in ('.py', '.js', '.cjs', '.html', '.css'))
    report = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'python': sys.version, 'checks': checks, 'backend_counts': counts,
              'scope': 'Offline automated checks; no real model, hospital or user acceptance claim.',
              'source_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in files}}
    (output / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return int(any(c['exit_code'] != 0 for c in checks))


if __name__ == '__main__':
    raise SystemExit(main())
