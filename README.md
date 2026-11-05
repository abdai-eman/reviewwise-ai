# ReviewWise — weekly guest feedback

ReviewWise turns supplied café reviews into complaint counts, original evidence
and practical next steps. It runs locally with Python, Streamlit, Ollama and
**qwen2.5:3b**. M2 experiments, prompts, datasets and saved outputs are preserved.
Development is on **[m3-mvp](https://github.com/abdai-eman/reviewwise-ai/tree/m3-mvp)**; `main` is unchanged.

## Run on Windows — three steps

1. **Download the 90 MiB [ReviewWise-M3-Windows.zip](https://github.com/abdai-eman/reviewwise-ai/raw/refs/heads/m3-mvp/download/ReviewWise-M3-Windows.zip).** Use this Windows package, not GitHub's generic source ZIP. The ready-to-run build includes Python 3.12.10 and the exact app dependencies. See [package verification](docs/verification/windows-package.json) for the packaged source commit, checksum, size and native Windows checks.
2. **Right-click the ZIP → Extract All.** Open the extracted folder. `START_REVIEWWISE.bat` must be directly inside it. Extract the entire archive into a writable location such as Desktop; do not run a file from the archive preview.
3. **Double-click `START_REVIEWWISE.bat`.** Keep its window open. The app opens in your browser. Use **Analyse reviews** for new input or **Saved reports → Explore a recorded AI example** to inspect a clearly labelled, genuine recorded result immediately.

**First use:** the ready-to-run edition does not install Python or run pip.
It reuses existing Ollama and the model. If Ollama is missing, it installs the
official per-user WinGet package; if the model is missing, it downloads it.
These checks run in the background while the interface and recorded reports
remain available. The sidebar distinguishes preparation, download and errors.
New AI analysis becomes available after preparation finishes.

Internet is required to download the project and, if missing, Ollama and its
model. The model download is approximately **1.9 GB**, as observed in the native
Windows verification log. Allow several GB of free disk for the app, runtime,
model and extraction; exact peak disk/RAM use is unmeasured. There is no API key,
Docker, Git, Node.js, VS Code or terminal-command prerequisite. Installer/source
agreements are accepted by the automatic Ollama installation. A managed computer
may require permission to install software.

**If WinGet is unavailable:** install [Ollama for Windows](https://ollama.com/download/windows)
first, then follow the three steps above: **four steps total**. Missing internet,
installation permission or model registry access must be resolved on that machine.
The launcher reports the cause and keeps saved reports available.

**Start again:** double-click the **same** `START_REVIEWWISE.bat`. An existing app
instance is reopened. Installed dependencies and model files are reused; no pip
install occurs in the ready-to-run edition. New reviews still need real inference.
Stop the app with Ctrl+C in its launcher. Quit Ollama from the Windows system
tray when finished, or use **Local AI controls → Release AI memory** in the app.

**Operating systems:** Windows x64 is the packaged target. Native verification
uses Windows Server 2022 and Python 3.12.10; this is not a Windows 11 laptop test.
Windows 11 x64 is the intended classroom target. Windows 10 depends on current
Ollama support and is unverified. macOS/Linux can use the source scripts described
below; they have no bundled Windows runtime and no current human laptop test.
An 8 GB Windows laptop may be slow or run short of free memory. **16 GB RAM is a
planning recommendation, not a verified minimum.** No dedicated GPU is required
by our CPU request path; performance on a particular CPU remains unverified.

## Use it and present it

Choose a reporting week and paste one review per line or upload a UTF-8 CSV with
a `review` column. Up to **1,000 reviews**, **1 MB per CSV**, and **2,000 characters
per review** are accepted. All accepted rows are tracked, including an 80-row
weekly file. Preview shows the first 20 only. The selected Monday–Sunday week is
a label: dates and business identity are not automatically checked or filtered.
Supply the correct week's reviews yourself. Other CSV columns are ignored.

Select **Find my next improvements**. A background worker sends up to four short
reviews per real Ollama call. AI returns complaint categories and numbered source
passages; Python validates the structure, IDs and original quotations, then counts
distinct reviews per category. One review can belong to several categories but
cannot inflate one category through repeated mentions. Invalid groups are isolated;
a repeatedly invalid review is marked **needs attention** and processing continues.
Timeouts or connection loss retain a partial report with explicit pending reviews.
Results appear while work continues. **Stop analysis** preserves completed work;
a stalled stream may take up to its 60-second read timeout to stop. Another tab
cannot start a simultaneous model run in the same app process.

The report shows complaint counts, evidence, praise and up to three category-based
actions. Actions are deterministic suggestions; AI does the extraction. Counts
reflect extracted labels, so traceable quotations do not establish semantic truth.

**Save this report** stores it explicitly on your computer. **Saved reports**
reopens it without inference, even after restarting the app. Export its JSON to
move it to another computer, or download the readable TXT report. Imported reports
are checked and counts are recomputed. The imported file's provenance is supplied
by its author, not independently authenticated. Delete local reports from Manage.
On Windows they are under `%LOCALAPPDATA%\ReviewWise\reports`; other systems use
`.reviewwise/reports`. Reviews are not automatically saved to report files.
The in-memory extraction cache is separate: it is checked against the model digest,
prompt, schema and settings and is lost when its session ends or Start over is used.

**For class:** prepare an actual report beforehand, save it, and open it in Saved
reports. Clearly identify it as recorded. Demonstrate a small fresh input live;
keep the full weekly report for inspection. Do not claim that an instant saved
report is instant AI inference or hide a time cut in the video.

## Verified results and remaining work

The [native Windows run](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42022332321)
used actual Ollama 0.40.14 and Qwen 3B, without response fixtures:

- One new review with two complaints: **9.97 seconds**, both expected categories.
- Preserved fictional multilingual M2 sample: **10 validated reviews, 7 requests, 41.25 seconds**.
- Identical repeat: **0 new model calls, 0.21 seconds**.

The [complete Windows check](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42028444818) also passed 79 offline tests, fresh input through the actual UI/AI worker, bundled UI rendering and the real Windows launcher. Its already-tested artifact was [published separately](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42030511585) after a concurrent evidence update blocked the first delivery. No new inference was claimed by that delivery job.

These are CI measurements, **not your 8 GB laptop's performance**, customer-data
evaluation or proof of accurate extraction. The sample misses some positive
feedback. A first 80-review laptop run and another person's laptop test remain
outstanding. [Raw evidence](docs/verification/windows-ai.json),
[validation record](docs/m3_validation.md), and the current
[architecture diagram](docs/architecture.svg) distinguish real AI from fixture tests.

Known limitations include incorrect/missed multilingual feedback (especially
Luxembourgish), slow CPU inference and memory pressure, six café categories plus
an ambiguous “other”, manual selection of the week's reviews, and session-only
extraction reuse. Saved reports persist explicitly, but there is no automatic
cross-session inference cache or date filtering. No automatic scraping, account
system or database is included.

Before submission the team must test the package on another person's laptop,
measure the full weekly input, assess real permitted input and language accuracy,
record/upload the three-minute video, confirm who did what, and replace pending
links. See the [submission checklist](docs/m3_submission.md) and
[one-page summary source](docs/m3_summary.md). No video, tag or submission is claimed.

## Source development (not required for the Windows package)

Use 64-bit Python **3.11–3.15** with pip. The exact, hashed dependency versions are
in `requirements.txt`; Streamlit 1.66.1, Pydantic 2.14.2 and Ollama's Python client
0.6.3 are pinned. Install [Ollama](https://ollama.com/download) for your OS.

On Windows, open the actual source folder and double-click `START_REVIEWWISE.bat`.
This source-only path reuses a compatible installed Python, or asks before a
WinGet Python 3.12 install; it creates/reuses a virtual environment and shows pip
progress. New extracted copies can reuse a completed matching environment from
nearby ReviewWise folders; keep the original environment folder if reused.

On macOS/Linux, install Python and Ollama, download/extract the source, then run
`bash setup.sh` and `bash start.sh` in that folder: **five steps including both
prerequisites**. This is the developer fallback, not a tested human laptop claim.

Checks for developers, from the source repository root:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\manage.py doctor
.venv\Scripts\python.exe scripts\manage.py smoke --text "The coffee was cold and the service was slow."
```

Use `.venv/bin/python` on macOS/Linux. Offline tests use explicit fixtures and do
not establish AI speed/accuracy. The smoke command calls the actual local model
and fails for incomplete coverage. `scripts/build_windows.py` builds the bundled
Windows edition in native CI from official publisher-verified Python and
hash-locked wheels. The professor runs none of these development commands.

**Who did what since M2:** team confirmation pending. Codex assisted with M3 code,
tests and documentation; that does not establish an individual student's work.
The team remains MAKNI Abdourrahmane, HAFT Benjamin and ABDAI Eman.
