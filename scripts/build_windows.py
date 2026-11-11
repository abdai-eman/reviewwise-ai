"""Build the Windows classroom package in native CI, with Python/dependencies included."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = '3.12.10'
PYTHON_URL = f'https://www.python.org/ftp/python/{VERSION}/python-{VERSION}-embed-amd64.zip'


def run(command, **kwargs):
    subprocess.run([str(item) for item in command], cwd=ROOT, check=True, **kwargs)


def main():
    if sys.platform != 'win32':
        raise RuntimeError('Build this Windows package on native Windows; cross-platform sources remain available separately.')
    staging = ROOT / 'build/windows/ReviewWise classroom package'
    if staging.exists():
        shutil.rmtree(staging)
    runtime = staging / 'runtime'
    runtime.mkdir(parents=True)
    archive = staging.parent / 'python-embedded.zip'
    urllib.request.urlretrieve(PYTHON_URL, archive)
    with zipfile.ZipFile(archive) as package:
        package.extractall(runtime)
    # Verify the PSF executable's Windows publisher signature before executing it.
    script = "$s=Get-AuthenticodeSignature $env:REVIEWWISE_PYTHON_TO_VERIFY; if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'Python Software Foundation') { throw 'Python publisher signature could not be verified' }"
    # Use the runner's current PowerShell edition and its matching module path.
    # Launching legacy Windows PowerShell from pwsh inherits incompatible modules.
    powershell = shutil.which('pwsh') or shutil.which('powershell')
    if not powershell:
        raise RuntimeError('The build machine needs PowerShell for publisher verification.')
    run([powershell, '-NoProfile', '-Command', script],
        env={**os.environ, 'REVIEWWISE_PYTHON_TO_VERIFY': str(runtime / 'python.exe')})
    for folder in ('reviewwise', 'scripts', 'assets', '.streamlit'):
        shutil.copytree(ROOT / folder, staging / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'secrets.toml'))
    for name in ('app.py', 'START_REVIEWWISE.bat', 'README.md', 'requirements.txt', 'LICENSE'):
        if (ROOT / name).is_file():
            shutil.copy2(ROOT / name, staging / name)
    (staging / 'experiments').mkdir()
    shutil.copy2(ROOT / 'experiments/reviews.json', staging / 'experiments/reviews.json')
    verification = staging / 'docs/verification'
    verification.mkdir(parents=True)
    for name in ('architecture.svg', 'architecture.dot', 'm3_validation.md', 'm3_submission.md', 'm3_summary.md', 'm3_summary_draft.pdf'):
        shutil.copy2(ROOT / 'docs' / name, staging / 'docs' / name)
    for source in (ROOT / 'docs/verification').glob('*'):
        if source.is_file():
            shutil.copy2(source, verification / source.name)
    run([sys.executable, '-m', 'pip', 'install', '--target', runtime / 'Lib/site-packages',
         '--only-binary=:all:', '--require-hashes', '--no-compile', '-r', ROOT / 'requirements.txt'])
    (runtime / 'python312._pth').write_text('python312.zip\n.\nLib/site-packages\n..\nimport site\n', encoding='utf-8')
    embedded = runtime / 'python.exe'
    run([embedded, '-c', 'import streamlit,ollama,pydantic,pandas,pyarrow; from reviewwise.storage import load_report; print("Bundled runtime imports passed")'])
    run([embedded, '-X', 'utf8', '-c',
         'import sys; from streamlit.testing.v1 import AppTest; '
         'app=AppTest.from_file(sys.argv[1], default_timeout=20).run(); '
         'assert not app.exception, app.exception; '
         'app.radio(key="workspace_view").set_value("Saved reports").run(); '
         'next(b for b in app.button if b.label=="Explore a recorded AI example").click().run(); '
         'assert not app.exception, app.exception; '
         'assert any("Your weekly feedback report" in s.value for s in app.subheader); '
         'print("Bundled UI and recorded real-AI report passed")', staging / 'app.py'])
    # Start the actual packaged launcher and make a loopback readiness request.
    log_path = staging.parent / 'portable-startup.log'
    started = time.perf_counter()
    with log_path.open('w', encoding='utf-8') as log:
        child = subprocess.Popen(['cmd.exe', '/d', '/c', 'START_REVIEWWISE.bat',
                                  '--headless', '--port', '18501'], cwd=staging, stdout=log, stderr=log)
        try:
            ready = False
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _ in range(60):
                if child.poll() is not None:
                    raise RuntimeError('The portable launcher exited: ' + log_path.read_text(encoding='utf-8'))
                try:
                    with opener.open('http://127.0.0.1:18501/_stcore/health', timeout=1) as response:
                        ready = response.status == 200
                except OSError:
                    pass
                if ready:
                    break
                time.sleep(.5)
            if not ready:
                raise RuntimeError('The bundled application did not become ready: ' + log_path.read_text(encoding='utf-8'))
            startup_seconds = time.perf_counter() - started
        finally:
            # Only terminate this test's launcher and its own child process tree.
            subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], capture_output=True)
    state = staging / '.reviewwise'
    if state.exists():
        shutil.rmtree(state)
    manifest = {
        'source_commit': os.environ.get('GITHUB_SHA', ''), 'python_version': VERSION,
        'python_source': PYTHON_URL, 'python_archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'python_publisher_signature': 'Valid — Python Software Foundation',
        'requirements_sha256': hashlib.sha256((ROOT / 'requirements.txt').read_bytes()).hexdigest(),
        'native_portable_startup_seconds': round(startup_seconds, 3),
        'native_portable_imports': True, 'native_portable_health_request': True,
        'laptop_test': 'Not performed by CI; must be completed on another person’s laptop.',
    }
    (staging / 'build-info.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (verification / 'windows-package.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # The installed edition has a short entry document; source development stays in GitHub.
    (staging / 'README.md').write_text(
        '# ReviewWise — Windows classroom edition\n\n'
        '1. Download the Windows ZIP.\n'
        '2. Right-click it → Extract All, then open the extracted folder.\n'
        '3. Double-click **START_REVIEWWISE.bat** and keep its window open.\n\n'
        'Python and the exact app packages are included. No terminal commands or pip installation are needed. '
        'Existing Ollama and qwen2.5:3b are reused. Missing Ollama/model files are prepared in the background; '
        'initial downloads need internet and may take several minutes (model approximately 1.9 GB). '
        'If WinGet is unavailable, install Ollama from https://ollama.com/download/windows first: four setup steps total.\n\n'
        'For a presentation, open **Saved reports → Explore a recorded AI example**. '
        'It is a genuine recorded result, clearly labelled; it does not run new inference. '
        'Use **Analyse reviews** for new input and **Save this report** to keep your own results. '
        'A new 80-review analysis can still take minutes on a laptop.\n\n'
        'Next time, double-click the same launcher. To stop, press Ctrl+C in its window. '
        'Quit Ollama from the Windows tray or use Release AI memory when finished.\n\n'
        'Windows x64; Windows Server 2022 CI verified. Another person’s laptop test is still required. '
        '8 GB RAM can be limiting; 16 GB is a recommendation, not a verified minimum. '
        'Remove personal details from input. Saved reports are stored only when explicitly saved.\n\n'
        'Package checks: build-info.json. Architecture: docs/architecture.svg. '
        'Full source and documentation: https://github.com/abdai-eman/reviewwise-ai/tree/m3-mvp\n', encoding='utf-8')
    output = ROOT / 'download/ReviewWise-M3-Windows.zip'
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in sorted(staging.rglob('*')):
            relative = path.relative_to(staging)
            if not path.is_file() or '__pycache__' in relative.parts or path.suffix == '.pyc':
                continue
            if 'site-packages' in relative.parts and any(part in {'tests','test'} for part in relative.parts):
                continue
            package.write(path, relative.as_posix())
    manifest.update(package_bytes=output.stat().st_size, package_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    (ROOT / 'docs/verification/windows-package.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    if output.stat().st_size >= 95 * 1024 * 1024:
        raise RuntimeError('Package exceeds the source-download size limit. Use the CI artifact; do not commit this large archive.')


if __name__ == '__main__':
    main()
