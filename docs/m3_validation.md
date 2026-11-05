# M3 validation record — 4 November 2026

This is an implementation record, not a completed assessment claim. The attached
semester brief was read during M3 preparation. M2 evidence is unchanged.

## Current environment

- Linux x86_64, Python 3.12.14, 32 GiB cgroup memory limit and four CPU cores of quota.
- Hash-locked dependencies installed using pip; no Docker used.
- Native Ollama **0.40.14**, downloaded from its official GitHub release. The
  archive SHA-256 matched the official release checksum before extraction:
  `993e83d08c3d13d17c55009a3e2664c8a25445e644aec3a68bef5abb6abce67d`.
- Runtime files are outside the checkout; `.venv` and local logs are ignored.

## Recorded checks

| Check | Outcome | Interpretation |
|---|---|---|
| Hash-verified dependency install and `pip check` | Passed | Packages install consistently on this Linux runtime. |
| Fresh source-only setup in a path containing spaces | Packages passed; full setup blocked at model download | New `.venv` created and installed consistently; this is not a fresh Windows/laptop test. |
| Windows x64 / Python 3.12 pip dry run | Passed | Required wheel artifacts were available with matching hashes. This does not execute Windows scripts or install on Windows. |
| `python -m unittest discover -s tests -v` | 39 passed on each Python 3.11-3.15 | Offline input, extraction/retry, counting, UI and launcher tests. Windows installer calls are mocked; this does not prove native Windows installation or real AI. |
| Windows package dry runs on Python 3.11/3.13/3.14/3.15 | Passed | Hash-locked binary packages resolve for Windows on every tested interpreter. Existing 3.12 wheel validation also passed. |
| Live Streamlit HTTP / Chromium browser check | Passed | Page loads; pasted input, valid/invalid CSV and real missing-model error work. No report appears on failure; no browser JavaScript errors. External browser requests were blocked during this test. |
| `bash -n setup.sh start.sh` | Passed | Shell syntax only. |
| Native Ollama startup | Passed | Service API responds; no model installed. |
| Native Python automatic-launch path | Blocked at model pull | Existing dependencies are reused; the real model pull is denied by cloud policy and no ready application is claimed. |
| Real occupied-port check | Passed | A reserved loopback port was avoided and the replacement port could be bound successfully. |
| `scripts/manage.py setup` | Blocked at model pull | Configured proxy denies `registry.ollama.ai` with HTTP 403 / Forbidden. Package install and service startup succeeded first. |
| `scripts/manage.py doctor` and `smoke` | Failed as expected: missing model | Nonzero exit and a specific remedy; no fabricated report. |
| Real M3 extraction and semantic accuracy | Unrun | Requires successful model download and actual inference. |
| Windows/macOS installation | Unrun | This Linux instance cannot establish Windows/macOS compatibility. |
| Another person's laptop / offline restart | Unrun | A team member must perform these checks. |

## Simplified Windows startup

The professor's package is `download/ReviewWise-M3-Windows.zip`, with no outer
source-directory prefix. Its launcher is directly at the ZIP root. GitHub's
generic source ZIP, by comparison, wraps the source in `reviewwise-ai-m3-mvp/`;
Windows Extract All adds the chosen extraction destination around that folder.
The dedicated package avoids the resulting extra navigation level. It is
generated with `git archive` from committed source; `.gitattributes` excludes
the download directory so generated packages do not include older ZIPs.

The student prepares and validates the package. The professor does not run a
packaging command, diagnostics or a script pasted into a terminal.

`START_REVIEWWISE.bat` is the single entry point for first and later launches.
It changes to its own project directory and detects existing 64-bit Python
3.11-3.15 through the project environment, PATH, standard installation folders,
the Python launcher and installed Microsoft Store Python packages. It asks before
installing Python if no compatible interpreter is found. Python install manager
automatic downloads are disabled during detection using its documented
`PYTHON_MANAGER_AUTOMATIC_INSTALL=false` setting. The manager installs Ollama if
needed on Windows, creates
or refreshes `.venv` only when needed, pulls a missing model, starts/reuses
Ollama, chooses an available loopback port and opens Streamlit.

Official `microsoft/winget-pkgs` metadata was checked for `Python.Python.3.12`
3.12.10 and `Ollama.Ollama` 0.40.14: both provide x64 per-user installers and
SHA-256 hashes. No checksum/TLS bypass flags or PowerShell policy changes are
used. WinGet selects the package versions available on the user's machine;
record the installed versions in the laptop test. This verifies metadata and
the intended installation route, not a Windows run.

The new tests cover cold dependency installation, retaining checksum checks,
warm-start reuse without downloads, missing WinGet/manual fallback, installer
failure, missing-model pull and verification, ordering startup after prerequisites,
and selecting an available port. The native `.bat`/WinGet path still requires
execution on a real Windows laptop. The Linux cloud model download remains
blocked; no complete first-launch or real-inference success is claimed.

The original Python 3.12-only restriction was unnecessarily narrow. The lock
now selects NumPy 2.4.6 on Python 3.11 and 2.5.4 on newer Python; all artifact
hashes remain checked. Dependency installation and all 39 offline tests passed
with CPython 3.11.17, 3.12.14, 3.13.16, 3.14.8 and 3.15.0. Three initial parallel
UI test runs hit the runner's three-second timeout during cold imports on the
shared CPU quota; sequential reruns passed with assertions/timeouts unchanged.
This matrix verifies Python compatibility on the development host, not native
Windows installation or AI accuracy.

The cloud draft adds `registry.ollama.ai` to the existing network policy.
Saving does not apply it. Review/save and publish through environment settings
when appropriate, then retry setup. A model-blob redirect may require another
specific hostname; none has yet been observed. This cloud restriction does not
establish a problem on the user's laptop.

## Reproduce the checks

From the repository root on Windows:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\manage.py doctor
.venv\Scripts\python.exe scripts\manage.py smoke --text "The coffee was cold and we waited too long."
```

Use `.venv/bin/python` on Linux/macOS. The smoke command calls real Ollama;
inspect its interpretation manually. Its default hand-written sentence is an
integration example, not evidence collected from a customer. Record permitted
input, actual output, model digest and runtime. Do not overwrite M2 outputs.

## Counting correctness versus AI accuracy

The counting test supplies known extraction labels for the unchanged M2 dataset.
It verifies slow service 3 (1,6,8), cold coffee 2 (4,10), high prices 2 (7,10),
and one each for dirty tables (5), incorrect order (3) and unfriendly staff (9).
Duplicate category mentions within one review cannot inflate the count. One
review can count under multiple categories.

This proves aggregation of supplied labels, not model extraction quality.
For real-model evaluation, compare extracted categories/quotes with human labels,
then compare aggregated counts separately. Preserve actual failures, including
missed Luxembourgish feedback. Do not tune reference labels to the model's output.

## Another-laptop protocol (required before submission)

Give a person the dedicated Windows ZIP and README only. Record any help you provide.

1. Record tester/date, OS/architecture, RAM, free disk and existing Python/Ollama.
   Follow the three Windows README steps (or the five-step manual fallback)
   in a writable path containing spaces. Record
   setup duration, every manual correction and help request.
2. Enter new permitted reviews. Confirm real inference, evidence, complaint counts
   and report download. Record latency and `doctor` output.
3. Stop/restart the app. Disconnect internet after setup and analyze new input.
   Confirm reuse of packages/model without downloads.
4. In a disposable installation/account, safely simulate missing dependencies,
   stopped Ollama and a missing model. Do not delete the tester's existing models
   or packages. Record errors and whether their remedies work.
5. Ask speakers to assess each claimed language. Record actual failures. Confirm
   M2 files are unchanged and keep personal review data out of Git.

| Evidence to complete | Actual result |
|---|---|
| Tester/date/laptop specifications | Pending |
| Setup duration and assistance required | Pending |
| Python/Ollama/model digest | Pending |
| New-input report and correctness assessment | Pending |
| Restart/offline/failure recovery | Pending |
| OS support justified by the run | Pending |

## Weekly-report correction — 4 November 2026

The old ten-review prototype cap has been replaced by a 1,000-review report
limit. The existing 1 MB CSV and 2,000-character-per-review limits remain.
An 80-row file is accepted in full; only its input preview is shortened to
20 rows. The user selects a Monday–Sunday reporting week. This labels the full
input, not an automatic date filter; dates and review authenticity remain
unverified. CSV files and M2 experiment evidence were not changed.

| Check | Verified result | Scope |
|---|---|---|
| `.venv/bin/python -m unittest discover -s tests -v` | **58 passed**, Python 3.12 | Offline input, schema/quotation validation, retries, counting, weekly date labels, session reuse, UI and launcher checks. |
| Production browser upload | 80 rows accepted, action enabled, correct full input count | Chromium, 1440px desktop and 390px mobile; fictional CSV constructed only in browser-test memory. |
| Weekly result, chart and TXT download | All 80 review references retained; known fixture counts 27, 27, 26; selected week and its unverified-date caveat included | Clearly labelled SDK-response fixture; real pipeline validation, counting, report rendering and download. **Not a live model run or speed benchmark.** |
| Repeat report in the same session | 80 validated extractions reused; zero additional extraction calls | SDK-response fixture with a call counter; reuse is labelled in the UI and TXT. Ollama/model identity is still checked. |
| Interrupted report | Failure on review 3 produced no complete report; retry reused the two completed analyses and finished all 80 rows | SDK-response fixture; no fabricated partial success. |
| Cache isolation | Changed model digest, prompt or generation settings cause fresh extraction; corrupted evidence is rejected | Offline tests; an unknown digest disables reuse. Schema is included in the cache key. |
| Weekly selection | Monday–Sunday boundaries, year boundary, cleared-date state and changing week without re-extracting unchanged input passed | Offline logic/UI tests. |
| Rendered UI | Desktop/mobile upload and report inspected; no horizontal overflow, external requests or browser errors | Local Chromium; result states use explicit fixtures. |
| Architecture and summary | Current cache/weekly flow included in exported SVG; refreshed summary draft is one A4 page | Generated from the tracked DOT and Markdown source. |
| Live model readiness | Direct local SDK check reports `qwen2.5:3b` missing | No new model/dependency installation or inference attempt. Current test environment's launcher setup marker is also absent, so `doctor` stops at its setup check. Earlier clean-setup observations above are historical. |

First-run time and accuracy for 80 new reviews on the Windows laptop remain
**unverified**. The existing model, extraction prompt, generation settings and
Python counting rules are preserved. Raising the input limit does not accelerate
new model calls. Reuse only helps identical previously validated input with the
same model/prompt/schema/settings; no cache or report is automatically written
to disk. **Start over** clears the cache. Closing or restarting the app can lose
session state. A class demo must identify reused reports and any cut waiting time.

## Runtime correction in progress — 5 November 2026

The user's Windows screenshots establish a real failure of the previous
package: after a long wait, review 12 failed validation after two attempts and
the 11 completed reviews were not shown as a report. The user reports 8 GB RAM
and an Intel processor; the exact CPU is unknown. This is evidence that the
earlier offline checks did **not** establish usable real-laptop behavior.
The old error did not retain the specific rejected model output, so the precise
validation defect is not known. No successful new real-model run is claimed.

Current source adds a single background worker, incremental validated results,
partial reports with separate failed/pending IDs, cancellation and duplicate-tab
protection. Short reviews are grouped (up to four) and the model returns evidence
IDs; Python copies the actual original passages. Requests use at most two CPU
threads and shorter contexts/output bounds. The same Qwen 3B model is retained.
The launcher reuses its recorded running instance, avoids importing the full app
twice during warm checks, and cleans up its own process metadata on exit.

| Check | Result and scope |
|---|---|
| Offline suite | **67 passed**, Python 3.12. Includes malformed/missing/duplicate IDs, original multilingual source passages, bounded fallback, review-12 failure, stream cancellation, cache isolation, actual worker concurrency, partial export and launcher reuse/cleanup. |
| Request-count reduction | 80 distinct short test reviews used 20 fixture requests; replay used zero additional extraction requests. This is **not** a real latency/accuracy measurement. |
| Actual rendered UI | Desktop/mobile Chromium fixture checks passed. Results appear during processing; a review-12 failure retains 79 results and one explicit failure; partial download includes all original references; stop and duplicate-tab rejection work; the other tab reenables after completion. |
| Fixture provenance | The isolated SDK fixture lives outside the repository, has a visible test banner, and is not shipped. No external requests or browser errors. |
| Source/data preservation | M2 experiments, user/sample CSV files, dependency locks and the model choice are unchanged. |
| Real-model gate | **Blocked.** `qwen2.5:3b` is not installed in this managed environment; active policy does not allow `registry.ollama.ai`. That hostname is already in the saved configuration draft but not the active runtime policy. |
| Release status | Source correction only; the Windows ZIP is still the previous `3569de5` package. It will not be refreshed until a real Qwen request validates the new path. |

The reduced settings are a proposed resource tradeoff for an 8 GB laptop,
not a verified memory/latency guarantee. Stopping a stalled request may wait
until its next streamed chunk or the 60-second read timeout. Cache state remains
session-only. The next required work is a real model/prompt/80-review test after
the pending model-download network setting is applied, followed by a measured
Windows run. The current smoke command returns failure for an incomplete result.
