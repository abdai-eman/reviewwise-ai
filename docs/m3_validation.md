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
| `python -m unittest discover -s tests -v` | 24 passed | Offline input, validation/retry, counting, setup-error and Streamlit UI tests. Fixtures/mocks do not validate real AI. |
| Live Streamlit HTTP / Chromium browser check | Passed | Page loads; pasted input, valid/invalid CSV and real missing-model error work. No report appears on failure; no browser JavaScript errors. External browser requests were blocked during this test. |
| `bash -n setup.sh start.sh` | Passed | Shell syntax only. |
| Native Ollama startup | Passed | Service API responds; no model installed. |
| `scripts/manage.py setup` | Blocked at model pull | Configured proxy denies `registry.ollama.ai` with HTTP 403 / Forbidden. Package install and service startup succeeded first. |
| `scripts/manage.py doctor` and `smoke` | Failed as expected: missing model | Nonzero exit and a specific remedy; no fabricated report. |
| Real M3 extraction and semantic accuracy | Unrun | Requires successful model download and actual inference. |
| Windows/macOS installation | Unrun | This Linux instance cannot establish Windows/macOS compatibility. |
| Another person's laptop / offline restart | Unrun | A team member must perform these checks. |

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

Give a person the final ZIP and README only. Record any help you provide.

1. Record tester/date, OS/architecture, RAM, free disk and existing Python/Ollama.
   Follow the five README steps in a writable path containing spaces. Record
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
