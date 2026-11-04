# ReviewWise — M3 summary draft

**Team:** MAKNI Abdourrahmane · HAFT Benjamin · ABDAI Eman

**Deadline:** 16 November 2026, 23:59.

**Repository:** https://github.com/abdai-eman/reviewwise-ai

**M3 tagged commit and unlisted video:** pending — not created or published.

**Problem and users.** Independent café owners in Luxembourg receive multilingual
feedback and need to decide what to improve. ReviewWise aims to turn supplied
reviews into inspectable complaints and practical actions.

**Product.** A local Streamlit page accepts pasted reviews or a UTF-8 CSV. Ollama
with `qwen2.5:3b` extracts feedback and original-language evidence. Python checks
JSON, categories and quotations, counts distinct review IDs per complaint, and
creates a downloadable weekly report with up to three supported actions.
Up to 1,000 reviews are accepted. The Monday–Sunday week is selected by the
user; input dates are not verified or filtered. All accepted reviews are counted.
No database, cloud AI, API key or Docker is required. See `docs/architecture.svg`.

**Installation.** On Windows 11 with App Installer/WinGet: download the M3 ZIP,
extract it, double-click `START_REVIEWWISE.bat`. First launch installs missing
Python/Ollama only when missing, reuses Python 3.11-3.15, creates `.venv`, installs hash-checked
packages, downloads the model and opens the app. Later starts use the same file.
It asks before installing another Python. Without WinGet, installing missing prerequisites adds up to two steps: five
steps total. The model is about 1.9 GB (unverified estimate); 16 GB RAM is a
planning recommendation, not a measured minimum.

**Evidence and status.** The weekly workflow is tested offline on Python 3.12,
including 80-review handling, session reuse, failure recovery and date labels.
Earlier launcher checks covered Python 3.11-3.15; the latest detailed results
are in `docs/m3_validation.md`. Package install
and native Ollama 0.40.14 startup work. Cloud policy blocks the model registry,
so no real M3 inference or accuracy improvement is claimed. M2 evidence is
unchanged. Windows setup, a real-input run, another person's laptop test,
offline operation and the video remain pending.

**Known limitations.** AI may miss or misclassify multilingual feedback,
especially Luxembourgish; Python counts cannot correct incorrect extraction.
Six café categories are limited and “other” combines different topics. CPU
inference may be slow for a new weekly file. Validated analyses are reused in
the current session; closing or restarting the app can lose them. Quotes establish
traceability, not semantic truth. M3 performance/user benefit remain unmeasured.

**Cost and privacy.** Up to 160 local extraction calls for 80 new reviews including
retries × €0 metered API fee = €0 metered API fees. Hardware/electricity remain
unmeasured. Reviews go only to local Ollama; no automatic report files are saved.
Remove unnecessary personal information and use permitted data.

**Who did what since M2.** Actual member contributions require team confirmation.
Codex assisted with M3 code, tests and documentation; that does not establish an
individual student's contribution or technical understanding.

**Before submission.** Complete the real-input and other-laptop tests, record an
unlisted three-minute video, replace pending links/contributions, review this
draft, export the final one-page PDF and tag the agreed M3 commit.
