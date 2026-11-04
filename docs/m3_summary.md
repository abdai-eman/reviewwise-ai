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
creates a downloadable template report with up to three supported actions.
No database, cloud AI, API key or Docker is required. See `docs/architecture.svg`.

**Installation.** Five README steps: install 64-bit Python 3.12; install/open
Ollama; download/extract the ZIP; run `setup.bat`; run `start.bat`. Setup creates
`.venv`, installs hash-checked pinned packages and downloads the model. Later
starts reuse them. Model size is approximately 1.9 GB (unverified estimate);
16 GB RAM is a planning recommendation, not a measured minimum.

**Evidence and status.** 24 offline logic/UI tests pass on Linux. Package install
and native Ollama 0.40.14 startup work. Cloud policy blocks the model registry,
so no real M3 inference or accuracy improvement is claimed. M2 evidence is
unchanged. Windows setup, a real-input run, another person's laptop test,
offline operation and the video remain pending.

**Known limitations.** AI may miss or misclassify multilingual feedback,
especially Luxembourgish; Python counts cannot correct incorrect extraction.
Six café categories are limited and “other” combines different topics. CPU
inference may be slow; batches are capped at ten reviews. Quotes establish
traceability, not semantic truth. M3 performance/user benefit remain unmeasured.

**Cost and privacy.** Up to 20 local extraction calls for ten reviews including
retries × €0 metered API fee = €0 metered API fees. Hardware/electricity remain
unmeasured. Reviews go only to local Ollama; no automatic report files are saved.
Remove unnecessary personal information and use permitted data.

**Who did what since M2.** Actual member contributions require team confirmation.
Codex assisted with M3 code, tests and documentation; that does not establish an
individual student's contribution or technical understanding.

**Before submission.** Complete the real-input and other-laptop tests, record an
unlisted three-minute video, replace pending links/contributions, review this
draft, export the final one-page PDF and tag the agreed M3 commit.
