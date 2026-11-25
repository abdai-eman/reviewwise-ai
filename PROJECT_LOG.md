# ReviewWise — Project Log

## M1 — Problem and Customer Validation

**Date:** 12 October 2026

### 1. Problem Statement

Small businesses in Luxembourg receive reviews in French, German, Luxembourgish, and English. Reading reviews manually can make it difficult to spot repeated problems and customer suggestions, especially when there are many reviews. This could take extra staff time, although we have not yet measured the cost for businesses with high review volumes.

ReviewWise aims to help businesses understand their reviews and identify what they could improve each week.

### 2. Users and Customers

**Users:** Owners and managers of small cafés, restaurants, and hotels in Luxembourg.

**Potential payers:** Business owners or managers. Pricing has not been decided.

**Market size:** Around 2,675 accommodation and food-service businesses in Luxembourg (2022). [1]

### 3. Existing Alternatives

- **Trustpilot Business:** Mainly focused on its own review platform.
- **Birdeye:** Offers a broader range of reputation-management features than our proposed tool.
- **Manual reading:** Finding repeated issues across many reviews takes time.

### 4. Value Proposition

For small-business owners in Luxembourg who want to understand multilingual customer feedback, ReviewWise is an AI-powered review analysis tool that suggests practical weekly improvements, unlike manually comparing reviews.

### 5. Why AI?

AI can recognize similar complaints written in different languages, group recurring feedback, and suggest improvements. Without AI, businesses would need to compare reviews manually or use language-specific rules.

### 6. Potential User Interviews

**Interview 1 — Hotel Bristol**

**Mr. Nea Marku, Receptionist | 10 October 2026 | 10–15 minutes**

- Mainly uses Booking.com and Airbnb.
- Reviews are handled manually, taking less than 30 minutes per week.
- Guest complaints are usually resolved directly by staff.
- Booking.com's translation feature helps with multilingual reviews.
- Fake reviews are a bigger problem than language differences.
- He felt AI review analysis might benefit larger hotels more than their 30-room hotel.
- Personal communication with guests remains important.

**Interview 2 — Bloom Specialty Coffee Shop**

**Café supervisor | 9 October 2026 | 12–15 minutes**

- Checks reviews once a week or every two weeks.
- Reviews are handled manually without AI tools.
- Negative reviews are uncommon.
- Customer suggestions are useful for improving the café.
- The supervisor reacted positively to ReviewWise, especially its improvement suggestions.
- The café does not currently pay for review-management software.
- No specific willingness-to-pay amount was established.

**Interview challenges:** We contacted several other businesses, but many were busy or preferred to reply later by email.

### Source

[1] STATEC, *Luxembourg in Figures 2025*, p. 48.

https://statistiques.public.lu/dam-assets/catalogue-publications/luxembourg-en-chiffres/2025/luxembourg-in-figures-2025.pdf

### Writing Improvement Tool Used

Grammarly was used to check grammar and improve wording.


## M2 – Technology Exploration and Project Proposal
**Date:** 19 October 2026

### 1. Technology Comparison
We compared two AI approaches for ReviewWise:
- **Qwen2.5 (3B) with Ollama:** Runs locally, has no API fees, and keeps customer reviews on the user's computer.
- **GPT-4.1 mini API:** Cloud-based alternative with usage-based pricing.

We selected Qwen2.5 with Ollama because it is free to use locally, offers better control over data, and has already been tested.

### 2. AI Experiment
We tested Qwen2.5 (3B) using 10 fictional multilingual customer reviews.

We conducted three experiments to analyze customer complaints and generate weekly improvement reports.

The results showed that the model could understand multilingual reviews and identify complaints, but sometimes made mistakes when grouping similar complaints and counting their frequency.

We decided to improve accuracy using Python validation.

The experiment scripts, saved outputs, and instructions are available in the repository.

### 3. Chosen Approach and Limitations
We chose Qwen2.5 (3B) with Ollama.

Current limitations:
- Incorrect complaint grouping and counts.
- Limited testing with only 10 fictional reviews; Luxembourgish remains untested.
- Multiple AI calls may increase processing time.

We may consider a larger local model or a cloud API if accuracy or performance remains insufficient.

### 4. Architecture
The planned system will accept multilingual customer reviews, analyze them locally using Python, Ollama, and Qwen2.5, and generate weekly reports containing recurring complaints and improvement suggestions.

### 5. Cost Estimate
Ollama runs the model locally without API fees.

For one weekly report containing 10 reviews:

11 AI calls × €0 = **€0 API cost per report**.

Electricity and hardware costs have not yet been measured.

### 6. MVP Development Plan
- **26 October:** Improve AI analysis and complaint counting — Abdourrahmane Makni.
- **5 November:** Build review input and weekly report interface — Benjamin Haft.
- **10 November:** Test multilingual reviews — Eman Abdai.
- **15 November:** Integrate components, fix bugs, and record demo — All members.

**MVP deadline:** 16 November 2026.

### 7. Repository
The project repository contains the AI experiments, saved results, and documentation.

## M3 — Minimum Viable Product

**Date:** 11 November 2026

### What changed since M2

We turned the M2 experiments into a working local application for café owners. Users can paste reviews or upload a CSV, select a reporting week, and generate a report with recurring complaints, positive feedback, original supporting passages, and suggested actions.

Qwen2.5 3B runs locally through Ollama and identifies complaints and praise in the supplied reviews. Python validates the evidence references and counts each review once per complaint category. This addresses the counting errors we saw in M2. Suggested actions use templates tied to the extracted categories. Fresh analysis calls the actual model without mocked responses.

### Setup and testing

Team members tested ReviewWise on each other’s laptops and encountered no issues. The [README](README.md) documents the three Windows setup steps.

**Real-input test:** The [demo video](https://www.youtube.com/watch?v=BEC7LJjvb2o) shows ReviewWise analysing real customer reviews with the local model and displaying the resulting report.

Windows CI passed 79 automated tests and verified the Windows package, launcher, and workflow from fictional input through the local model to the displayed report. [View the Windows CI run](https://github.com/abdai-eman/reviewwise-ai/actions/runs/42397705242).

### Architecture

Reviews flow from the Streamlit interface through a background worker to the local Ollama model. Python validates the evidence, counts complaints, and builds the report. Review analysis runs on the user’s computer and requires no API key. See the [M3 architecture diagram](docs/architecture.svg).

### Known limitations

- The model can miss or misclassify feedback. Users should check the original passages behind the findings.
- Local analysis can be slow on laptops with limited memory.
- The “Other” category can group unrelated complaints.
- The reporting week is selected by the user. The app does not verify review dates or filter reviews by week.

### Demo video

The demo was recorded from the running application. [Watch the ReviewWise demo on YouTube](https://www.youtube.com/watch?v=BEC7LJjvb2o).

### Contributions since M2

- **MAKNI Abdourrahmane:** Reviewed the full project, tested the application, and created the demo video.
- **HAFT Benjamin:** Contributed to application development and helped write the README.
- **ABDAI Eman:** Developed ReviewWise with Codex assistance and worked on the M3 summary PDF and project log.

## M4 — Testing and Iteration

**Date:** 30 November 2026

### Evaluation

We tested whether ReviewWise finds the right complaint categories in each review. A review is correct when the predicted set of categories matches our hand-written labels exactly. Our main metric is F1 over (review, category) pairs. We also report how often the app correctly says whether a review contains a complaint at all (complaint yes/no accuracy), the error in the complaint counts shown to the owner, and latency.

We used 70 fictional reviews: the 50 reviews in [Workbook1.csv](examples/Workbook1.csv) and 20 harder reviews. The harder ones cover wrong orders, unfriendly staff, reviews with two complaints, negation, sarcasm and an attempted prompt injection. Our baseline is a simple keyword matcher with no AI. The data, script and every result are in [evaluation/](evaluation/README.md).

### Results before and after

| Version | F1 | Precision | Recall | Complaint yes/no accuracy | Count error | Worst request |
|---|---|---|---|---|---|---|
| Keyword baseline (no AI) | 0.86 | 94% | 79% | 86% | 10 | — |
| M3 model (before) | 0.71 | 74% | 68% | 94% | 13 | 1.36 s |
| After fixes 1–5 | 0.83 | 88% | 79% | 96% | 10 | 0.48 s |

After the fixes, F1 by language is: English 0.95, French 1.00, German 0.84 and Luxembourgish 0.50. The keyword baseline scores 0.70, 0.93, 0.95 and 0.88. The model is now better than keywords in English and French but clearly worse in Luxembourgish.

The 96% means the model correctly classified 67 of 70 reviews as containing or not containing a complaint. Of the 32 reviews that actually contain a complaint, it detected one in 29 (about 91%).

### Issues found and changes made

1. Reviews sent to the model in the same request influenced each other, so a slow-service review was tagged as high prices. We now send one review per request. F1 rose from 0.71 to 0.75, and the worst request time fell from 1.36 s to 0.47 s.
2. When two complaints were joined by "and", only one was found. Review text is now also split on "and / et / und / an". F1 rose to 0.78.
3. Complaints that fit no category were forced into a named one: two noise complaints ("La salle était trop bruyante à midi." and "The music was far too loud…") were labelled unfriendly staff. The prompt now says to use "other" unless a category matches exactly, and both are now "other". F1 rose to 0.83.
4. Luxembourgish and German price words were missed. We added hint words in French, German and Luxembourgish to the prompt. F1 stayed at 0.83, and the count error fell from 10 to 7.
5. Expectations ("expected it to be cold but it was hot") and instructions inside a review were labelled as complaints. The prompt now excludes them. Precision on the hard reviews reached 100%.

Each change is supplied as a separate patch and will be committed separately.

### Failure cases

- **"Et war leider zimlech haart am Café."** (too loud) → labelled *cold coffee*, expected *other*.
- **"De Service war gutt mee e bësse lues."** (a bit slow) → labelled *cold coffee*, expected *slow service*. This was correct before fix 4.
- **"Ze deier fir e Kaffi."** (too expensive) → no complaint found, expected *high prices*.

All three are Luxembourgish. The 3B model often falls back to "cold coffee" when it does not understand a review. On Workbook1 this makes "cold coffee" the top issue, although only one review mentions cold coffee.

### Cost

The approach did not change, so there is still no API fee. Each review is now one model request, at about 0.3 s per review on an Apple M5 Pro laptop. Hardware and electricity costs are still not measured.

### Next steps

- Improve Luxembourgish, for example by combining keyword rules with the model or by testing a larger model.
- Write about 15 new reviews that we did not use while making the fixes, to check that the fixes were not tuned to this test set.
