# M3 verification — 5 November 2026

M3 is not submitted. M2 experiment scripts, prompts, dataset and saved evidence,
and all CSV files are unchanged by this correction. Changes are on `m3-mvp`.

## Actual Windows AI execution

[Native Windows run 42022332321](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42022332321)
used Windows Server 2022 x64, Python 3.12.10, official checksum-verified Ollama
0.40.14, the exact hash-locked dependencies and real local `qwen2.5:3b`.
No SDK-response fixture was used in its integration step.
[Raw outputs, model digest and stage outcomes](verification/windows-ai.json)
are retained separately from M2. Inputs are fictional evaluation sentences,
not customer reviews or an accuracy benchmark.

| Check | Actual result |
|---|---|
| Native package installation and `pip check` | Passed |
| Native offline tests at commit a0be8fd | 71 passed; includes explicit response fixtures, not real AI evidence |
| New two-complaint sentence | 1 validated review, both expected categories, 1 model request, 9.97 s |
| Unchanged multilingual M2 input | 10 validated reviews, 7 model requests, 41.25 s |
| Identical repeat with matching session cache | 10 reused, 0 additional model requests, 0.21 s |
| Recorded report | Actual result saved with source commit, model identity, timestamp and fictional-data provenance |
| Fresh input through the real UI (model already warm) | 1 actual model request, complete two-complaint report displayed, 3.12 s |
| Bundled Windows batch launcher | Health endpoint ready in 1.61 s on CI; UI/report rendered separately; not a laptop timing claim |
| Published package | 94,388,738 bytes (90 MiB); SHA-256 and source recorded in windows-package.json |
| Another person's laptop | Not yet performed |
| Full 80 new reviews on the user's 8 GB laptop | Not measured |
| Real permitted customer input / human language assessment | Outstanding |

Successful structural validation does not establish semantic accuracy. This
run missed some positive phrases. The deterministic counts are correct for the
labels actually extracted, not guaranteed correct interpretations of the reviews.
Timing on a CI runner cannot predict timing on the user's laptop.

Two earlier CI attempts installed dependencies and passed offline tests but
failed to keep the model server alive across step boundaries. Their failure
records remain in Git history. The successful correction starts the server,
pulls the model and performs inference within one PowerShell step.

## Interface, recovery and packaging checks

**79 local offline checks pass** on Python 3.12. The native Windows run
[42028444818](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42028444818)
also passed all 79 checks, new input through the actual UI button/background worker
and real Ollama to the displayed report, and the complete embedded-runtime package
checks. Its publication step failed after a concurrent generated-evidence update.
[Recovery run 42030511585](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42030511585)
downloaded that same successful artifact, verified its application files against
the branch, and published it without rebuilding or making new AI calls.

The latest local suite covers original source quotations, malformed/missing or
duplicate evidence IDs, bounded fallback, partial coverage, the review-12 failure,
stream cancellation, duplicate jobs/tabs, session cache isolation, deterministic
counting, week labels, navigation, explicit saved report round-trips and import
validation. UI fixture tests are deliberately separate from real AI verification.
The native workflow reruns this suite against its own source commit.

Desktop/mobile Chromium checks passed with no external requests or JavaScript
errors. The actual recorded Windows AI report loaded and exported successfully;
input survived navigation. A separate, visibly labelled SDK fixture confirmed
live results before completion, 79 validated results retained after review 12
failed, all 80 original inputs included in partial export, stopping, duplicate-tab
blocking and automatic reenabling. This fixture does not establish model latency
or accuracy.

The browser checks load the actual recorded Windows AI result. They check the
redesigned desktop/mobile interface, report chart/export, saved-result labelling,
input preservation, browser exceptions and external requests. They do not run
new model inference or measure model latency.

The ready-to-run Windows build includes official Python 3.12.10 embedded x64,
whose executable publisher signature is checked before execution, plus the exact
hash-verified binary packages. Its build verifies native imports, renders the
bundled UI and its genuine recorded report, and starts the actual bundled launch
path for a loopback health request. [Build evidence](verification/windows-package.json)
records source commit, artifact SHA-256, size and measured runner startup time.
The published artifact is the successfully tested build from source commit
`32d6c326c6c24a2cc319e4f00d6674edf2a30c80`. Source identity is checked before
publication. Its checksum/size are in the package record; the original run
is linked above. CI execution is not proof
of a successful Windows File Explorer double-click or WinGet install on a laptop.

Earlier managed Linux setup installed the hash-locked dependencies and verified
native Ollama startup. Its registry download is still denied by cloud network
policy; a saved allowlist draft does not change that policy. Native Windows CI
supplies the independent real-model integration evidence. No access checks,
TLS or artifact verification were bypassed. No Docker is used.

## The reported laptop defect and correction

The user reports Windows, 8 GB RAM and an unspecified Intel processor. The older
package processed 11 of 80 reviews, rejected review 12 after two attempts, and
discarded the usable report view. Its quiet pip step also appeared unchanged for
more than 15 minutes. The rejected model response was not retained, so the exact
old validation failure cannot be reconstructed.

The current source groups short reviews into compact evidence-ID requests and
uses at most two CPU threads. The UI stays available through a background worker,
shows validated partial results, isolates an invalid review, lists every failed
or pending input, supports stopping, and blocks duplicate model jobs within one
app process. Repeats reuse validated session results with matching model identity.

Explicit Save report makes a genuine result available after restart or export
without another model run. Recorded output is clearly labelled and is never
claimed to be live inference. The ready-to-run edition removes Python/pip setup
from the professor's machine. Ollama/model preparation runs in the background;
saved reports are available during preparation or after an installation failure.
The source-only launcher still shows real pip progress and can reuse an older
completed matching environment without moving/deleting it or touching CSV files.

These resource settings reduce requested concurrency/context, but are not a
verified RAM or speed guarantee. New 80-review input may still take minutes.
Stop can wait for the next stream response or the 60-second read timeout.

## Another-laptop protocol — required before submission

Give another person only the packaged ZIP and README. Record all help provided.

1. Record tester/date, OS, RAM, CPU, free disk, existing Ollama, package hash and
   source commit. Follow the three README steps in a writable path with spaces.
   Record download/extraction time separately from model setup and app startup.
2. Open the recorded example, then analyse new permitted input. Inspect original
   evidence and complaint counts, download/export the report, save it and reopen
   it after restart. Measure cold and warm inference separately.
3. Analyse the actual weekly file of at least 80 reviews. Check every input is
   accounted for as validated, failed or pending. Do not count pending/failed
   reviews as successful. Record duration, CPU/RAM pressure and semantic errors.
4. After setup, disconnect internet and restart. Confirm saved reports and new
   real inference work without downloads. In a disposable account/model directory,
   test missing Ollama/model, stopped service and interrupted download. Do not
   remove the tester's own models or working installation.
5. Check Windows without a system Python, missing WinGet/manual Ollama fallback,
   corrupt/incomplete extraction and unavailable registry. Confirm error messages
   give a usable remedy. Ask speakers to assess all claimed languages.

| Evidence the team must supply | Status |
|---|---|
| Tester, date, machine and package commit | Pending |
| Setup steps, assistance and actual duration | Pending |
| 80-review first run, accuracy and resource use | Pending |
| Offline restart and failure recovery | Pending |
| Real permitted input and multilingual human assessment | Pending |
| Video, actual team attribution and submission links | Pending |

## Reproduce development checks

From the source root on Windows:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\manage.py doctor
.venv\Scripts\python.exe scripts\manage.py smoke --text "The coffee was cold and the service was slow."
```

Use `.venv/bin/python` on macOS/Linux. The professor does not run these commands.
The smoke command calls actual Ollama and fails for incomplete coverage. Human
assessment must evaluate category selection separately from Python counting.
