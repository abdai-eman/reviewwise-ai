# ReviewWise — M2 Experiments

**Course:** Digital Transformation (BPINFOR-131)  
**Milestone:** M2 — Technology Exploration and Project Proposal  
**Date:** 19 October 2026

## Team Members

- MAKNI Abdourrahmane
- HAFT Benjamin
- ABDAI Eman

## 1. Purpose

ReviewWise is an AI-based customer feedback analysis project for small businesses in Luxembourg.

For M2, we tested whether Qwen2.5 (3B), running locally through Ollama, could analyze multilingual café reviews and generate a weekly feedback report.

We used the same 10 fictional customer reviews in English, French, German and Luxembourgish for all three experiments.

The objective was to compare report quality, complaint classification, counting accuracy and processing time.

## 2. Dataset

All three experiments load the same dataset:

`experiments/reviews.json`

The dataset contains 10 numbered fictional café reviews.

Using a shared dataset ensures that differences between the experiments are not caused by changes in the review inputs.

## 3. Experiment Approaches

### Experiment 1 — Basic Prompt

All 10 reviews are submitted to Qwen2.5 (3B) in a single request with basic instructions to summarize feedback, identify complaints and recommend improvements.

**Script:** `m2_experiment_1.py`

### Experiment 2 — Improved Prompt

All 10 reviews are submitted in a single request with detailed instructions to group complaints across languages, count occurrences, identify supporting review numbers and provide exactly three improvements.

**Script:** `m2_experiment_2.py`

### Experiment 3 — Two-Stage Analysis

Stage 1 analyzes each review separately. Stage 2 uses the individual analyses to generate the weekly report.

This requires 11 model calls: 10 individual analyses and one final report generation.

**Script:** `m2_experiment_3.py`

## 4. Requirements

- Python 3
- Ollama installed and running
- Qwen2.5 (3B) model
- Python `ollama` package

Install the model:

```powershell
ollama pull qwen2.5:3b
```

Install the Python package:

```powershell
python -m pip install ollama
```

Ensure Ollama is running before executing the experiments.

## 5. How to Run

Open a terminal in the main `reviewwise-ai` project folder.

Run Experiment 1:

```powershell
python experiments/m2_experiment_1.py
```

Run Experiment 2:

```powershell
python experiments/m2_experiment_2.py
```

Run Experiment 3:

```powershell
python experiments/m2_experiment_3.py
```

Each script automatically loads the shared dataset and saves its results in the `experiments/` directory.

The experiments can be run independently.

## 6. Generated Files

| File | Description |
|---|---|
| `reviews.json` | Shared dataset of 10 multilingual reviews |
| `experiment_output_1.txt` | Experiment 1 weekly report |
| `experiment_output_2.txt` | Experiment 2 weekly report |
| `experiment_output_3.txt` | Experiment 3 weekly report |
| `experiment_prompt_1.txt` | Experiment 1 prompt |
| `experiment_prompt_2.txt` | Experiment 2 prompt |
| `experiment_prompt_3.txt` | Experiment 3 stage 1 and stage 2 prompts |
| `experiment_3_individual_analysis.txt` | Individual review analyses |
| `experiment_commentary.md` | Evaluation and discussion of the results |

Running an experiment again may overwrite its previous output files.

## 7. Experimental Results

All three experiments completed successfully using Qwen2.5 (3B).

| Experiment | Method | AI runtime | Model calls |
|---|---|---:|---:|
| 1 | Basic prompt | 221.80 seconds | 1 |
| 2 | Improved prompt | 60.99 seconds | 1 |
| 3 | Two-stage analysis | 241.57 seconds | 11 |

Experiment 3 runtime breakdown:

- Stage 1: 126.76 seconds
- Stage 2: 114.81 seconds
- Total AI runtime: 241.57 seconds

Runtime was measured using Python's `time.perf_counter()`.

The values represent individual recorded runs rather than averages across repeated tests.

## 8. Evaluation

We manually compared the generated reports against the original reviews.

The correct complaint categories are:

| Complaint | Count | Review numbers |
|---|---:|---|
| Slow service | 3 | 1, 6, 8 |
| Cold coffee | 2 | 4, 10 |
| High prices | 2 | 7, 10 |
| Dirty tables | 1 | 5 |
| Incorrect order | 1 | 3 |
| Unfriendly staff | 1 | 9 |

### Experiment 1 — Findings

The basic prompt generated a readable weekly report and recognized several recurring complaints.

However, it incorrectly associated some reviews with complaint categories and did not consistently separate positive and negative feedback.

### Experiment 2 — Findings

The improved prompt produced a clearer report structure and was the fastest in the recorded runs.

However, it still generated incorrect complaint counts and supporting review numbers and omitted some categories.

### Experiment 3 — Findings

The two-stage approach made individual review analyses available for inspection.

However, the model mistranslated some Luxembourgish feedback, missed certain positive observations and introduced errors in the final report.

It also required more model calls and had the longest recorded AI runtime.

## 9. Overall Conclusion

All three experiments executed successfully, but none consistently produced accurate complaint classification and counting.

Experiment 2 provided the clearest output format and lowest recorded runtime.

Experiment 3 made intermediate extraction errors easier to identify, but did not eliminate inaccuracies.

These findings suggest that prompt engineering alone is insufficient for reliable complaint counting.

For the MVP, we plan to introduce structured review extraction, Python-based counting and validation of supporting review numbers.

These improvements are planned and have not yet been implemented or tested.

## 10. Limitations

1. The dataset contains only 10 fictional reviews.
2. The model sometimes misinterprets Luxembourgish feedback.
3. Complaint counts and supporting review numbers are unreliable.
4. Local inference can be slow, particularly with multiple model calls.
5. Results and runtime may vary between executions.

## 11. Use of AI Tools

ChatGPT (OpenAI) assisted with Python development, prompt refinement, debugging and documentation.

Qwen2.5 (3B), running locally through Ollama, generated the experimental analyses and reports.

We manually reviewed the results and documented their inaccuracies.

See `experiment_commentary.md` for detailed observations and failures.