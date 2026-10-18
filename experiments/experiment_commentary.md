# M2 — AI Experiment Commentary

**Project:** ReviewWise  
**Date:** 18 October 2026  
**Model:** Qwen2.5 (3B), running locally through Ollama  
**Dataset:** 10 fictional café reviews in English, French, German and Luxembourgish

## Objective

We tested whether a small local language model could turn multilingual customer reviews into a useful weekly report. We compared three prompting methods using the same 10 reviews and the same model.

The expected output was a summary of positive feedback, correctly grouped complaints with accurate frequencies, and three practical recommendations.

## Experiment 1 — Basic Prompt

**Method:** All 10 reviews were submitted in one prompt with basic instructions to summarize feedback and suggest improvements.

**Measured AI runtime:** 221.80 seconds.

**Findings:** The model identified slow service across reviews 1, 6 and 8 and produced a readable report. However, it associated unrelated reviews with order accuracy, cleanliness and pricing complaints. It also missed some negative feedback and mixed positive and negative observations.

**Conclusion:** A basic prompt is sufficient to generate a report, but it does not reliably classify customer complaints.

## Experiment 2 — Improved Prompt

**Method:** All 10 reviews were submitted in one prompt with explicit instructions covering four languages, complaint categories, supporting review numbers, frequency counts and exactly three improvements.

**Measured AI runtime:** 60.99 seconds.

**Findings:** The report followed a clearer structure but contained incorrect counts and references. It listed slow service in reviews 1 and 3 instead of 1, 6 and 8. It attributed dirty tables to reviews 4, 5 and 8 instead of only review 5. It also omitted cold coffee, incorrect orders and unfriendly staff.

**Conclusion:** More detailed instructions improved the report format but did not guarantee factual accuracy.

## Experiment 3 — Two-Stage Analysis

**Method:** Stage 1 analyzed each review individually. Stage 2 combined the individual analyses into a weekly report. This required 11 model calls: 10 individual analyses and one report-generation call.

**Measured runtime:**
- Stage 1: 126.76 seconds
- Stage 2: 114.81 seconds
- Total AI runtime: 241.57 seconds

**Findings:** The intermediate analyses made errors easier to inspect, but some translations were incorrect. Review 8's slow service was interpreted as bad service and bad coffee. Review 10's cold coffee was described as bad coffee. The final report also treated some complaints as positive feedback, omitted categories and failed to group repeated complaints correctly.

**Conclusion:** The two-stage method provides more visibility into individual analyses, but the current implementation is slower and still produces inaccurate reports.

## Comparison

| Criterion | Experiment 1 | Experiment 2 | Experiment 3 |
|---|---|---|---|
| Method | Basic prompt | Improved prompt | Two-stage |
| Reviews | 10 | 10 | 10 |
| Model | Qwen2.5:3b | Qwen2.5:3b | Qwen2.5:3b |
| AI runtime | 221.80 s | 60.99 s | 241.57 s |
| Model calls | 1 | 1 | 11 |
| Complaint accuracy | Unreliable | Unreliable | Unreliable |
| Main advantage | Simple | Clear structure | Inspectable intermediate results |
| Main weakness | Incorrect grouping | Incorrect counts | Translation and aggregation errors |

These runtimes are from individual recorded executions and should not be treated as stable performance benchmarks.

## Reference Answers

Manual inspection of the original reviews gives the following complaint categories:

| Complaint | Number of reviews | Review numbers |
|---|---|---|
| Slow service | 3 | 1, 6, 8 |
| Cold coffee | 2 | 4, 10 |
| High prices | 2 | 7, 10 |
| Dirty tables | 1 | 5 |
| Incorrect order | 1 | 3 |
| Unfriendly staff | 1 | 9 |

These reference answers allow future model outputs to be checked systematically.

## Chosen Approach

We selected **Qwen2.5 (3B) through Ollama** for further development because it runs locally, avoids per-request cloud API charges and allows us to test with multilingual reviews.

For the MVP, we plan to combine structured individual-review extraction with Python-based validation and complaint counting. This validation is **planned, not yet implemented or verified**.

## Limitations and Next Steps

1. The evaluation uses only 10 fictional reviews and may not represent real business feedback.
2. The model sometimes mistranslates Luxembourgish and misclassifies multilingual complaints.
3. The two-stage approach increases processing time and can propagate extraction errors into the final report.

Next, we will implement deterministic counting, verify supporting review numbers, test more reviews and compare accuracy and runtime. We may switch to a stronger local model or a cloud API if accuracy or latency remains unacceptable.

## Reproducibility

The repository contains the three Python experiments, shared `reviews.json`, generated reports, saved prompts and runtime measurements.

Run the experiments using:

```powershell
python experiments/m2_experiment_1.py
python experiments/m2_experiment_2.py
python experiments/m2_experiment_3.py
```

Ollama must be running with `qwen2.5:3b` installed, and the Python environment must include the `ollama` package.

## AI Tools Used

ChatGPT was used to assist with Python development, prompt refinement, debugging and documentation. Qwen2.5 (3B), running locally through Ollama, generated the experimental analyses and reports. The team reviewed the outputs and identified their inaccuracies.

**Evaluation status:** All three experiments execute and save their results, but reliable complaint classification and counting remain open problems.