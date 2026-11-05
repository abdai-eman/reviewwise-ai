# ReviewWise — M3 summary draft

**Team:** MAKNI Abdourrahmane · HAFT Benjamin · ABDAI Eman

**Repository:** https://github.com/abdai-eman/reviewwise-ai/tree/m3-mvp

**Deadline:** 16 November 2026, 23:59. **Video / submission tag:** pending.

**Problem and user.** Independent café owners in Luxembourg need to interpret
multilingual guest feedback and choose practical improvements. ReviewWise turns
supplied reviews into inspectable complaint groups, evidence and next steps.

**Product and AI.** Paste reviews or upload a UTF-8 CSV, select a week and run
local Ollama `qwen2.5:3b`. AI selects categories and numbered original passages;
Python validates the IDs/quotations and counts distinct reviews per category.
Up to 1,000 reviews are tracked, with explicit validated/failed/pending coverage,
live partial results, stopping and up to three deterministic suggestions. Save
and reopen a genuine report without rerunning AI; recorded reports are labelled.
Dates are supplied by the user, not automatically filtered. No cloud AI, API key,
database or Docker is required. Architecture: `docs/architecture.svg`.

**Installation.** Windows package: download, Extract All, double-click
`START_REVIEWWISE.bat`. The ready-to-run build includes Python 3.12.10 and pinned
packages; native packaging checks are recorded in `docs/verification/windows-package.json`
when successful. Ollama is reused or installed through WinGet; a missing model
is downloaded in the background while saved reports remain available. Without
WinGet, manually installing Ollama adds one step: four total. Internet is needed
for initial downloads, including about 1.9 GB for the model. Windows 11 x64 is
the classroom target; CI uses Windows Server 2022. Human laptop validation is
pending. 16 GB RAM is a planning recommendation, not a verified minimum.

**Measured evidence.** Native Windows CI executed real Ollama 0.40.14 and Qwen:
one two-complaint input took 9.97 s; the preserved fictional multilingual sample
produced 10 validated reviews in 41.25 s over seven requests; its matching repeat
took 0.21 s with no new model calls. This is not a customer-data accuracy study
or an 8 GB laptop speed claim. The run misses some positive feedback. Offline
logic/UI tests use explicit fixtures and are reported separately in
`docs/m3_validation.md`. M2 experiments, CSV files and evidence are unchanged.

**Known limitations.** AI can miss or misclassify feedback, especially in
Luxembourgish. CPU inference and memory pressure can make new weekly files slow.
Six café categories plus “other” are limited. Review dates/authenticity are not
verified. The extraction cache is session-only; saved report files persist only
when explicitly saved. Quotes support traceability, not semantic truth.

**Cost/privacy.** Local inference has no metered API fee; hardware, electricity
and actual user benefit are unmeasured. Remove personal details and use permitted
input. Saved reports contain original reviews and remain locally until exported
or deleted. Imported provenance is not independently authenticated.

**Who did what since M2.** Actual member contributions require team confirmation.
Codex assisted with M3 code, tests and documentation; this establishes no
individual student's contribution or technical understanding.

**Before submission.** Test the packaged setup on another person's laptop,
measure the full 80-review workflow and assess new permitted input/languages.
Record the three-minute unlisted video, fill actual contributions and links,
review/export this one-page draft, and tag the agreed M3 commit. No video,
human laptop test or Moodle submission is claimed.
