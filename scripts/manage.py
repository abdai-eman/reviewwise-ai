"""Standard-library setup/start/doctor commands. No Docker or global pip installs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv


ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
STATE = ROOT / ".reviewwise"
MODEL = "qwen2.5:3b"
API = "http://127.0.0.1:11434"
MARKER = VENV / ".reviewwise-requirements.sha256"


class SetupError(Exception):
    pass


def run(command, error):
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SetupError(error) from exc


def check_python():
    if not (3, 11) <= sys.version_info[:2] < (3, 16) or struct.calcsize("P") != 8:
        raise SetupError(
            "ReviewWise needs 64-bit Python 3.11-3.15. Restart START_REVIEWWISE.bat "
            "to use a compatible Python already installed on your computer."
        )


def find_ollama():
    executable = shutil.which("ollama")
    if executable:
        return executable
    candidates = [Path("/usr/local/bin/ollama"), Path("/opt/homebrew/bin/ollama")]
    if os.name == "nt":
        candidates.insert(0, Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Ollama/ollama.exe")
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise SetupError(
        "Ollama was not found. Install Ollama from https://ollama.com/download/windows "
        "(or the installer for your OS), then reopen the terminal and run setup again."
    )


def api_json(path):
    # Review content and loopback readiness requests never go through a proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(API + path, timeout=3) as response:
            return json.load(response)
    except (OSError, urllib.error.URLError, ValueError):
        return None


def ensure_service():
    status = api_json("/api/version")
    if status is None:
        executable = find_ollama()
        STATE.mkdir(exist_ok=True)
        child_env = os.environ.copy()
        child_env.update({
            "OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_NUM_PARALLEL": "1",
            "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_CONTEXT_LENGTH": "4096",
            "OLLAMA_NO_CLOUD": "1",
        })
        options = {"start_new_session": True} if os.name != "nt" else {
            "creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        }
        with (STATE / "ollama.log").open("ab") as log:
            try:
                process = subprocess.Popen(
                    [executable, "serve"], cwd=ROOT, env=child_env,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **options,
                )
            except OSError as exc:
                raise SetupError("Could not start Ollama. Open the Ollama application and retry.") from exc
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            status = api_json("/api/version")
            if status is not None:
                break
            if process.poll() is not None:
                break
            time.sleep(0.25)
        if status is None:
            if process.poll() is None:
                process.terminate()
            raise SetupError(
                "Ollama did not become ready. Open Ollama and retry. "
                "Check .reviewwise/ollama.log for startup details or a port 11434 conflict."
            )
    version = str(status.get("version", ""))
    numbers = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not numbers or tuple(map(int, numbers.groups())) < (0, 5, 7):
        raise SetupError("Ollama is too old or its API is unexpected. Update Ollama and retry.")
    return version


def installed_model():
    tags = api_json("/api/tags")
    if not isinstance(tags, dict) or not isinstance(tags.get("models"), list):
        raise SetupError("Could not read Ollama's model list. Restart Ollama and retry.")
    return next((item for item in tags["models"] if item.get("name") == MODEL), None)


def requirements_digest():
    return hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest()


def check_dependencies():
    if not PYTHON.is_file() or not MARKER.is_file() or MARKER.read_text() != requirements_digest():
        raise SetupError("Python dependencies need setup. Double-click START_REVIEWWISE.bat or run bash setup.sh.")
    run(
        [str(PYTHON), "-c", "import streamlit, ollama, pydantic"],
        "Python dependencies could not be loaded. Rerun setup to repair the virtual environment.",
    )


def ensure_dependencies(force=False):
    """Install only on first launch, after requirements change, or to repair imports."""
    check_python()
    if not force:
        try:
            check_dependencies()
            return
        except SetupError:
            pass
    if not PYTHON.is_file():
        print("Creating the project virtual environment...", flush=True)
        try:
            venv.create(VENV, with_pip=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SetupError("Could not create .venv. Check Python's venv/pip support and free disk space.") from exc
    run(
        [str(PYTHON), "-c", "import sys,struct; assert (3,11) <= sys.version_info[:2] < (3,16) and struct.calcsize('P') == 8"],
        "The existing .venv uses an unsupported Python. Rename it, then rerun the launcher.",
    )
    print("Installing checksum-verified, pinned Python packages...", flush=True)
    run(
        [str(PYTHON), "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
         "--only-binary=:all:", "--require-hashes", "-r", str(ROOT / "requirements.txt")],
        "Dependency installation failed. Check internet access, proxy settings and free disk space. "
        "The detailed pip error is above; do not disable TLS or checksum verification.",
    )
    run([str(PYTHON), "-m", "pip", "check"], "Installed package versions are inconsistent. Rerun setup.")
    MARKER.write_text(requirements_digest())


def install_ollama_if_missing():
    """Use the verified Windows package source; reuse any existing installation."""
    try:
        return find_ollama()
    except SetupError:
        if platform.system() != "Windows":
            raise
    winget = shutil.which("winget")
    if not winget:
        raise SetupError(
            "Windows App Installer (WinGet) is unavailable. Install Ollama from "
            "https://ollama.com/download/windows, then double-click START_REVIEWWISE.bat again."
        )
    print("Installing Ollama for your Windows account. This may take a few minutes...", flush=True)
    run(
        [winget, "install", "--id", "Ollama.Ollama", "--exact", "--source", "winget",
         "--scope", "user", "--architecture", "x64", "--accept-package-agreements",
         "--accept-source-agreements", "--disable-interactivity"],
        "Windows could not install Ollama. Check internet access and your computer's installation "
        "permissions, or install Ollama from https://ollama.com/download/windows, then retry the launcher.",
    )
    return find_ollama()


def ensure_model():
    """Start/reuse local Ollama; a completed installation needs no downloads."""
    if api_json("/api/version") is None:
        install_ollama_if_missing()
    version = ensure_service()
    if installed_model() is None:
        print(f"Downloading {MODEL} (approximately 1.9 GB; internet required)...", flush=True)
        child_env = os.environ.copy()
        child_env["OLLAMA_HOST"] = "127.0.0.1:11434"
        try:
            subprocess.run([install_ollama_if_missing(), "pull", MODEL], cwd=ROOT, env=child_env, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SetupError(
                "Model download failed. Check internet access, proxy/registry permissions and disk space. "
                "Retry the same launcher; Ollama can reuse completed downloads."
            ) from exc
        if installed_model() is None:
            raise SetupError("Ollama did not register the model after download. Restart Ollama and retry the launcher.")
    return version


def setup():
    ensure_dependencies(force=True)
    version = ensure_model()
    print(f"Setup complete. Ollama {version}; model {MODEL}. Run start.bat or bash start.sh.")


def available_port(preferred):
    if not 1024 <= preferred <= 65535:
        raise SetupError("Choose an application port between 1024 and 65535.")
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", preferred))
        except OSError:
            probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def launch(headless=False, port=8501):
    ensure_dependencies()
    print("Checking local Ollama and the review-analysis model...", flush=True)
    ensure_model()
    port = available_port(port)
    print("Opening ReviewWise. Keep this window open while using the application.", flush=True)
    run(
        [str(PYTHON), "-m", "streamlit", "run", str(ROOT / "app.py"),
         "--server.address=127.0.0.1", f"--server.port={port}",
         "--browser.gatherUsageStats=false", "--server.fileWatcherType=none",
         f"--server.headless={'true' if headless else 'false'}"],
        "ReviewWise stopped with an error. Read the message above and restart START_REVIEWWISE.bat.",
    )


def doctor():
    check_python()
    check_dependencies()
    status = api_json("/api/version")
    if status is None:
        raise SetupError("Ollama is not running. Open Ollama or use start.bat / bash start.sh.")
    if installed_model() is None:
        raise SetupError(f"The {MODEL} model is missing. Run setup with internet access.")
    model = installed_model()
    print(json.dumps({
        "python": platform.python_version(), "os": platform.platform(),
        "ollama": status.get("version"), "model": MODEL,
        "digest": model.get("digest"), "model_bytes": model.get("size"),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["launch", "setup", "start", "doctor", "smoke"])
    parser.add_argument("--headless", action="store_true", help="Do not open a browser (start only).")
    parser.add_argument("--port", type=int, default=8501, help="Local application port (start only).")
    parser.add_argument("--text", default="The coffee was cold and we waited too long.", help="Real model smoke-test input.")
    args = parser.parse_args()
    check_python()
    if args.command == "setup":
        setup()
    elif args.command == "doctor":
        doctor()
    elif args.command in ("launch", "start"):
        launch(headless=args.headless, port=args.port)
    elif args.command == "smoke":
        check_dependencies()
        # The entry point also works when called using the system Python.
        if Path(sys.prefix).resolve() != VENV.resolve():
            run([str(PYTHON), str(Path(__file__)), "smoke", "--text", args.text], "The real model smoke test failed.")
            return
        sys.path.insert(0, str(ROOT))
        from reviewwise.pipeline import analyze_reviews, reviews_from_text
        from reviewwise.report import render_report
        ensure_service()
        result = analyze_reviews(reviews_from_text(args.text))
        print(render_report(result))
        print("Real model extraction completed. Check its interpretation manually.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nReviewWise stopped.")
        sys.exit(130)
    except Exception as exc:
        # Network/installation failures should not require reading a Python traceback.
        print(f"\nReviewWise: {exc}", file=sys.stderr)
        sys.exit(1)
