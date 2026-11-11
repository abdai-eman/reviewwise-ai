# ReviewWise AI

**AI-Powered Multilingual Customer Review Analysis for Small Businesses in Luxembourg**

## 1. What it does

ReviewWise helps small businesses in Luxembourg make better use of customer reviews in French, German, Luxembourgish, and English. Users paste reviews or upload a CSV. The app groups recurring complaints, shows positive feedback and original supporting passages, and suggests practical improvements.

**Our main question:** What should this business improve this week?

## 2. Users and value proposition

**Target users:** Owners and managers of small businesses in Luxembourg, particularly independent cafés, restaurants, and hotels. The M3 prototype focuses on cafés.

**Potential customers:** Small businesses that regularly review customer feedback.

**Value proposition:** ReviewWise helps owners understand multilingual feedback and identify practical improvements based on recurring complaints. Each business receives an analysis based on the reviews it supplies.

## 3. How to run it

### M3 — Windows setup

1. [Download the Windows package](https://github.com/abdai-eman/reviewwise-ai/raw/refs/heads/main/download/ReviewWise-M3-Windows.zip).
2. Right-click the ZIP, choose **Extract All**, and open the extracted folder.
3. Double-click **`START_REVIEWWISE.bat`** and keep its window open. ReviewWise opens in your browser.

The Windows package includes Python and the app dependencies. On first launch, internet access is needed if the launcher has to install Ollama or download the `qwen2.5:3b` model. Wait for local AI setup to finish before running an analysis. If WinGet is unavailable, [install Ollama for Windows](https://ollama.com/download/windows) first, then follow the three steps above.

### Try the test CSV

1. Open [Workbook1.csv](examples/Workbook1.csv) and click **Download raw file** on GitHub, or [download it directly](https://github.com/abdai-eman/reviewwise-ai/raw/refs/heads/main/examples/Workbook1.csv).
2. In ReviewWise, open **Analyse reviews**, select a reporting week, and upload the CSV.
3. Click **Find my next improvements** to analyse the 50 reviews.
4. Open **Review evidence** to see the original passages behind the findings.

You can also paste one review per line or upload your own UTF-8 CSV with a `review` column.

### M3 demo

The video was recorded from the running application. [Watch the ReviewWise demo on YouTube](https://www.youtube.com/watch?v=BEC7LJjvb2o).

## 4. Architecture

![ReviewWise M3 architecture](docs/architecture.svg)

The Streamlit interface passes reviews to a background worker, which calls Ollama on the same computer. Qwen returns complaint categories and references to passages containing complaints or praise. Python validates those references, counts distinct reviews per complaint category, and builds the report. A temporary session cache can reuse validated results. Users can save reports locally or export them. Review text stays on the computer during analysis. Initial setup contacts external services to download software and model files. Local inference requires no API key.

## 5. AI components

In M2, we tested local Qwen2.5 3B on fictional multilingual reviews. The scripts, prompts, and outputs are preserved in the [M2 experiments](experiments/README.md).

In M3, the app uses **Qwen2.5 3B (`qwen2.5:3b`)** through the local Ollama API. The repository contains the [extraction prompt](reviewwise/prompts.py), [model and category configuration](reviewwise/config.py), and [analysis pipeline](reviewwise/pipeline.py).

Fresh review analysis calls the actual model to identify complaints and positive feedback. Python checks the returned evidence references against the supplied reviews and counts each review once per complaint category. The report shows the counts alongside the original passages. Suggested actions use fixed templates tied to the extracted categories. A saved report can be reopened without another model call.

## 6. Evaluation

Team members tested ReviewWise on each other's laptops and encountered no issues during those tests.

**M3 real-input test:** ReviewWise analyses real customer reviews with the local model and displays the resulting report in the [demo video](https://www.youtube.com/watch?v=BEC7LJjvb2o).

Windows CI separately verified the full path from fresh fictional input through the actual local model to the report shown in the app. It also passed 79 automated tests and verified the Windows package and launcher. [View the Windows CI run](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42397705242).

## 7. Limitations, risks, privacy and ethics

1. The model can miss or misclassify complaints and praise. Users should check the original passages before acting on a finding.
2. Local analysis can be slow on laptops with limited memory.
3. The “Other” category can group unrelated complaints.
4. The reporting week is selected by the user. The app does not verify or filter review dates.

Reviews are processed locally. Saved reports contain original review text. Use reviews you have permission to process and remove unnecessary personal information before sharing a CSV or report.

## 8. Business case

Our early customer research focused on small hospitality businesses in Luxembourg. The café supervisor we interviewed was interested in practical improvement suggestions. The hotel receptionist reported spending less than 30 minutes per week handling reviews and saw more potential value for larger hotels.

Local inference has no metered API fee. Pricing and willingness to pay remain open, and hardware and electricity costs have not been measured. The M1 interviews and M2 cost estimate are in the [project log](PROJECT_LOG.md).

## 9. AI tools the team used

- **M1:** Grammarly helped with grammar and wording.
- **M2:** ChatGPT assisted with code and prompts, and Qwen2.5 3B was used in the experiments.
- **M3:** Codex assisted with implementation, automated tests, and documentation.

## 10. Who did what

### Contributions since M2

- **MAKNI Abdourrahmane:** Reviewed the full project, tested the application, and created the demo video.
- **HAFT Benjamin:** Contributed to application development and helped write the README.
- **ABDAI Eman:** Developed ReviewWise with Codex assistance and worked on the M3 summary PDF and project log.
