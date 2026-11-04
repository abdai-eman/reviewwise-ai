# ReviewWise AI — M3 MVP

**Status:** M3 implementation draft. Offline logic/UI tests pass on Linux;
real model inference is currently blocked by cloud registry access. Windows
installation, another person's laptop test and the demo video remain outstanding.
See [validation evidence](docs/m3_validation.md). M3 is not yet complete or submitted.

## 1. What it does

ReviewWise helps café owners understand customer reviews in English, French,
German and Luxembourgish. Paste reviews or upload a CSV, analyze them locally
with Ollama and `qwen2.5:3b`, inspect complaint counts and supporting evidence,
and download a report with practical actions. Python performs the counting;
AI interprets the reviews. Incorrect interpretations remain possible.

## 2. Users and value proposition

For small-business owners in Luxembourg who need to understand multilingual
feedback, ReviewWise turns supplied café reviews into traceable improvement
suggestions. The current prototype focuses on cafés; hotels and restaurants
are potential later users. Business owners/managers are the potential payers.
Each batch represents one business; review dates are not verified.

## 3. How to run it (five steps)

**No Docker, Git, Node.js, API key or code editing required.** Windows 11 x64 is
the primary target, but has not yet been tested on a Windows laptop. Use
**64-bit Python 3.12**; other Python versions are rejected until tested.

1. Install [Python 3.12 for Windows](https://www.python.org/downloads/windows/).
   Include **pip** and the **Python launcher**, and enable **Add python.exe to PATH**.
2. Install [Ollama for Windows](https://ollama.com/download/windows) and open it.
   The native Linux runtime checked during development was **0.40.14**;
   [that release](https://github.com/ollama/ollama/releases/tag/v0.40.14) also
   provides `OllamaSetup.exe`. Windows compatibility still needs testing.
3. Open the [M3 draft branch](https://github.com/abdai-eman/reviewwise-ai/tree/m3-mvp),
   use **Code → Download ZIP**, extract it into a writable folder, and open that
   extracted folder. For assessment, use the team's final M3 tagged version once it exists.
4. Double-click **`setup.bat`**. It creates `.venv`, installs checksum-verified
   pinned packages, checks/starts local Ollama and downloads `qwen2.5:3b` if missing.
   Wait for **Setup complete**; keep internet access available during this step.
5. Double-click **`start.bat`**. Keep its terminal open. In the browser, paste one
   review per line or upload a UTF-8 CSV with a `review` column, then click
   **Analyze reviews**. Check the evidence and download the report if useful.

**Next time:** only run `start.bat`. It reuses the environment/model and starts
Ollama if needed; no manual virtual-environment activation or `ollama run` is
required. Close ReviewWise with Ctrl+C in its terminal. Ollama may remain running;
quit its application separately if you want to release its resources.

**Downloads and hardware:** internet is required for the installers, ZIP, Python
packages and initial model download. The model is approximately **1.9 GB**
(estimate, not verified against the registry in this environment). Allow roughly
**10 GB free disk** and preferably **16 GB RAM**; these are planning recommendations,
not measured minimums. CPU inference is supported by Ollama but may be slow;
no dedicated GPU is required by our code. Hardware performance and offline
operation after setup still need laptop validation. See
[Ollama's hardware guidance](https://docs.ollama.com/gpu).

**macOS/Linux:** the same five steps apply with the appropriate Python/Ollama
installers; use `bash setup.sh` and `bash start.sh` in steps 4 and 5. Python must
include `pip` and `venv`. Linux Python 3.12.14 was used for the recorded checks;
macOS and other distributions are not yet verified support targets.

| Message or symptom | Action |
|---|---|
| Python 3.12 not found / wrong version | Install 64-bit Python 3.12 with pip/launcher; reopen the terminal and rerun setup. |
| Ollama not found | Install/open Ollama; reopen the terminal and rerun setup. No Docker needed. |
| Service cannot start | Open Ollama manually. Inspect `.reviewwise/ollama.log`; another program may occupy port 11434. |
| Model missing / download failed | Rerun setup with internet and enough disk space. School/company proxies may block the registry. |
| Package installation failed | Read the pip error; check connection, disk space and Python version. Never disable TLS or checksum checks. |
| Browser does not open | Use the local address printed by Streamlit in the terminal. |
| Application port already in use | Close the previous ReviewWise window/process and restart. |
| Analysis times out / model cannot load | Close memory-heavy applications and try one shorter review. CPU inference can take minutes. |
| Extraction cannot be validated | Try that review separately. No completed report is produced from a failed batch. |

Developer checks from the repository root (not additional professor setup steps):

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts\manage.py doctor
.venv\Scripts\python.exe scripts\manage.py smoke --text "The coffee was cold and we waited too long."
```

On macOS/Linux replace `.venv\Scripts\python.exe` with `.venv/bin/python`.
The smoke command calls the real model; unit/UI fixtures are not proof of AI quality.

## 4. Architecture

![ReviewWise M3 architecture](docs/architecture.svg)

The browser talks to a local Streamlit process. Python validates input and sends
one review at a time to local Ollama with a JSON schema. It validates the returned
types, categories and verbatim evidence quotes, then counts distinct review IDs
per complaint. A template report presents counts, positive evidence and up to
three supported actions. Unknown complaints remain visible as “other.” No second
model call rewrites counts. Reviews and results stay in the browser/server
session; only an explicit download creates a report. No database or API secrets
are required. Package/model downloads contact external services during setup;
analysis uses a fixed loopback address. [Diagram source](docs/architecture.dot).

## 5. AI components

- **Model:** local Ollama `qwen2.5:3b`. The tag is not immutable; `doctor` prints
  its installed digest and size. The report also records the digest.
- **Runtime:** Ollama; the launcher rejects releases older than 0.5.7.
  Native runtime 0.40.14 starts here; inference compatibility is not yet verified.
- **Python packages:** Streamlit **1.66.1**, `ollama` **0.6.3**, Pydantic **2.14.2**.
  All resolved dependencies and artifact hashes are in `requirements.txt`.
- **Prompt:** [reviewwise/prompts.py](reviewwise/prompts.py).
  Category/action definitions and model limits are in
  [reviewwise/config.py](reviewwise/config.py); the schema and extraction call
  are in [reviewwise/pipeline.py](reviewwise/pipeline.py).
- **Processing:** structured extraction at temperature zero; at most two attempts
  per review. Python validates evidence and counts. Actions use category templates.
- **Data:** user-supplied reviews or the labelled fictional M2 example in
  `experiments/reviews.json`. No scraping, cloud fallback or mocked app responses.

## 6. Evaluation

The [preserved M2 experiments](experiments/README.md) recorded AI runtimes of
221.80, 60.99 and 241.57 seconds. These were individual historical runs, not M3
benchmarks. Their inaccurate counts and translations motivated the M3 design.

The M3 offline suite checks input handling, multilingual quote validation,
retries, failure messages, distinct-review counting, reporting and UI state.
Its known-label counting test matches the M2 reference answers; it does **not**
establish that the real model extracts those labels correctly.

Real inference, manual comparison on new input, performance measurements,
offline operation and another person's laptop test remain required. Current
outcomes and the test protocol are in [docs/m3_validation.md](docs/m3_validation.md).

## 7. Limitations, risks, privacy and ethics

1. AI can misclassify or omit feedback, especially Luxembourgish. Quote validation
   checks traceability, not the correctness of interpretation.
2. Counts are exact for extracted labels, not guaranteed true complaint counts.
3. Six café categories are limited. “Other” may combine unrelated complaints;
   inspect them individually. Actions cover only recognized categories.
4. Batches are limited to ten reviews of at most 2,000 characters each. CPU
   analysis can be slow. A failed review stops the batch without a complete report.
5. Duplicate rows count separately. Dates, business identity and authenticity
   are not verified. A batch is not automatically a calendar week.
6. Windows installation and real M3 inference are not yet verified here.

Remove unnecessary personal details before use. Review text goes only to
`127.0.0.1:11434`; the model client ignores proxy/environment routing. There is
no database or automatic customer-report file; clear the session when finished.
Explicit downloads remain on the user's computer until deleted. Ollama/system
logs have their own retention; do not enable debug logging with personal reviews.
Setup contacts package/model providers. The launcher disables Streamlit usage
telemetry. Use permitted input, avoid publishing customer data without appropriate
rights, and keep a human responsible for decisions. Language bias needs evaluation.
Formal legal/regulatory assessment has not been completed.

## 8. Business case

Initial customers would be independent café owners/managers in Luxembourg.
M1 cited approximately 2,675 accommodation/food-service businesses in 2022
([STATEC, Luxembourg in Figures 2025, p. 48](https://statistiques.public.lu/dam-assets/catalogue-publications/luxembourg-en-chiffres/2025/luxembourg-in-figures-2025.pdf));
this is a broad sector total, not a verified café market size. The interviews
in `PROJECT_LOG.md` did not establish a willingness-to-pay amount.

A ten-review batch needs 10 extraction calls × €0 metered local API fee = **€0
metered API fees**; one retry per review permits up to 20 calls. Electricity,
hardware and support costs remain unmeasured. Pricing and margins need customer
evidence. Alternatives include Trustpilot Business, Birdeye and manual reading;
the proposed advantage is local multilingual analysis with inspectable evidence.

## 9. AI tools the team used

M2 used ChatGPT for coding/prompt assistance and local Qwen2.5 for the recorded
experiments. OpenAI Codex assisted with M3 code, tests and documentation in this
workspace. The team must review, test and understand it before submission;
AI assistance does not establish an individual student's contribution.

## 10. Who did what

Team: MAKNI Abdourrahmane, HAFT Benjamin, ABDAI Eman.
The M2 plan assigned analysis/counting to Abdourrahmane, interface work to
Benjamin and multilingual testing to Eman, with shared integration/demo work.
**Actual contributions since M2 have not yet been confirmed.** Replace this
with two factual lines backed by each member's work before submission.

M3 preparation: [summary draft](docs/m3_summary.md) and [demo/submission checklist](docs/m3_submission.md).
No M3 tag, video link or claim of another-laptop validation has been created.
