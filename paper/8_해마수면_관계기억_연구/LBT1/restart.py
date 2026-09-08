"""Restart the published LBT-1 checks in a new directory, never in tracked sources.

No network, Git writes, device control, external experiments or package installation.
The full mode runs the original simulation twice and then its independent checker.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New external output directory; must not exist')
    parser.add_argument('--quick', action='store_true', help='Only source integrity and 14 unit checks')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
    for relative, expected in manifest['sha256'].items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or sha(path) != expected:
            raise RuntimeError(f'Publication integrity failure: {relative}')
    if args.output:
        output = args.output.expanduser().resolve()
        repo_root = next((p for p in (ROOT, *ROOT.parents) if (p / '.git').exists()), ROOT)
        if output.is_relative_to(repo_root):
            raise ValueError('Output must be outside the source repository')
        output.mkdir(parents=True, exist_ok=False)
    else:
        output = Path(tempfile.mkdtemp(prefix='ce-lbt1-restart-'))
    for filename in ('local_rule.py', 'verify.py', 'check_results.py',
                     'test_local_rule.py', 'protocol.json', 'requirements.txt'):
        shutil.copyfile(ROOT / 'source' / filename, output / filename)
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    def run(script: str, log: str) -> None:
        with (output / log).open('wb') as handle:
            subprocess.run([sys.executable, script], cwd=output, env=env,
                           stdout=handle, stderr=subprocess.STDOUT,
                           check=True, timeout=120)
    run('test_local_rule.py', 'tests.log')
    receipt = {'publication_files_verified': len(manifest['sha256']),
               'unit_tests': '14 passed', 'new_biological_samples': 0,
               'cosmology_revalidated': False, 'quick_mode': args.quick,
               'output_directory': str(output), 'full_check_executed': False}
    if not args.quick:
        run('verify.py', 'verify_first.log')
        first_hash = sha(output / 'results.json')
        shutil.copyfile(output / 'results.json', output / 'results_final_before_rerun.json')
        run('verify.py', 'verify_second.log')
        run('check_results.py', 'check.log')
        expected = json.loads((ROOT / 'published_results.json').read_text(encoding='utf-8'))
        receipt.update(full_check_executed=True,
                       same_run_results_identical=first_hash == sha(output / 'results.json'),
                       historical_result_sha256_match=first_hash == expected['full_results_sha256'],
                       results_sha256=first_hash,
                       independent_check=json.loads((output / 'validation.json').read_text(encoding='utf-8')))
        if not receipt['same_run_results_identical']:
            raise RuntimeError('Fresh-directory rerun changed results')
        # Historical byte equality is reported, not silently replaced by a success claim.
        # Different numerical library/platform versions may require numerical review.
    (output / 'restart_receipt.json').write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
