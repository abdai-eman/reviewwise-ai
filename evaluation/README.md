# M4 evaluation

> **Status: draft (23 Nov 2026), set up with Claude Code.** Before submitting, the team must check every
> gold label in `cases.csv`. Ask a native speaker to check the Luxembourgish reviews in particular.

## Task and what counts as correct

ReviewWise must find the complaint categories that each review contains. The categories are the 7 in
[`reviewwise/config.py`](../reviewwise/config.py). A review can have no complaint, one, or several.
Praise must never be counted as a complaint.

- A **case is correct** when the predicted set of categories equals the gold set exactly.
- At the **label level**, every (review, category) pair counts as a true positive, false positive or
  false negative. From these we report precision, recall and F1. **F1 is the headline metric.**
- **Complaint detection** asks whether the review was correctly flagged as containing a complaint or
  not, ignoring the category.
- **Count error** is the sum over categories of |predicted count − gold count|. It is the error the
  owner sees in the "What needs attention" chart.
- **Top issue** checks whether the most frequent predicted category is the true most frequent one.
- **Latency** is reported per review and per AI request (median and worst case), after one warm-up
  request so that model loading is excluded.

## Data: [`cases.csv`](cases.csv), 70 cases, all fictional

| Set | Cases | Content |
|---|---|---|
| `workbook` | 50 | The team's [`examples/Workbook1.csv`](../examples/Workbook1.csv): 13 EN, 13 FR, 12 DE, 12 LU. 16 reviews contain a complaint, each with exactly one category. 34 contain no complaint. |
| `hard` | 20 | Written for M4 (drafted by Claude) to cover what Workbook1 lacks: `incorrect_order` and `unfriendly_staff` (which never appear in Workbook1), 6 reviews with two complaints, negation ("expected it to be cold… but it was perfectly hot"), sarcasm, and a prompt-injection attempt. |

Gold labels are in the `gold_complaints` column, with categories separated by `;`. An empty value means
no complaint.

## Baseline

The naive alternative is a **keyword matcher**: a list of word prefixes per category in EN, FR, DE and
LU, with no AI (`KEYWORDS` in [`run_eval.py`](run_eval.py)). It cannot produce `other`.
**Caveat:** the list was written by someone who had already seen the cases, so the baseline is an
optimistic upper bound for keywords. Report it that way.

## How to run

Start Ollama first, then run these commands from the repository root:

```bash
.venv/bin/python evaluation/run_eval.py --system keyword --label baseline-keyword
.venv/bin/python evaluation/run_eval.py --system model --label m3-model
.venv/bin/python evaluation/run_eval.py --system model --group-size 1 --label exp-group-size-1
```

Each run writes `results/<label>.json` (the metrics) and `results/<label>_cases.csv` (each case with its
gold and predicted labels). The model runs at temperature 0. Repeating `m3-model` gave identical
predictions (`m3-model-repeat`).

## Results (23 Nov 2026, qwen2.5:3b via Ollama 0.40.17, Apple M5 Pro, 48 GB)

| Run | Set | Exact match | Precision | Recall | **F1** | Complaint detection | Count error | Top issue | s / review |
|---|---|---|---|---|---|---|---|---|---|
| Keyword baseline | all 70 | 86% | 94% | 79% | **0.86** | 86% | 10 | wrong | <0.001 |
| **M3 model** (before) | all 70 | 80% | 74% | 68% | **0.71** | 94% | 13 | wrong (cold coffee) | 0.31 |
| Experiment: 1 review per request | all 70 | 81% | 84% | 68% | **0.75** | 93% | 13 | wrong | 0.29 |
| M3 model | workbook 50 | 84% | 60% | 56% | 0.58 | 94% | 11 | wrong (cold coffee) | |
| Experiment: 1 review per request | workbook 50 | 88% | 77% | 62% | 0.69 | 94% | 9 | wrong (slow service) | |
| M3 model | hard 20 | 70% | 85% | 77% | 0.81 | 95% | 2 | correct | |

Exact match looks high because 38 of the 70 cases have no complaint, and saying "none" is easy.
Use F1 for comparisons.

Per-request latency: the M3 model has a median of 0.69 s and a worst case of 1.36 s, using 34 requests
(the app groups up to 4 reviews per request and retries invalid groups one review at a time). With one
review per request, the median is 0.27 s and the worst case 0.47 s, using 70 requests. Cost per
interaction is €0 in API fees because inference is local.

**What this shows so far.** The model is better at noticing *that* a review contains a complaint (94% vs
86% detection), because it catches problems a keyword list does not anticipate. It is worse at choosing
the *category*: it pushes "other" complaints into known categories, especially `cold_coffee`. That one
behaviour makes "Cold coffee" the top issue on Workbook1, when only 1 of the 50 reviews mentions it.
Sending one review per request removes cross-review leakage, raises precision from 74% to 84%, and is
not slower.

## Failure cases (M3 model, verbatim from `results/m3-model_cases.csv`)

| Case | Review | Gold | Predicted | Likely reason |
|---|---|---|---|---|
| W29 | Le service était un peu lent ce matin. | slow_service | high_prices | **Cross-review leakage.** W32 ("Les prix sont légèrement élevés") was in the same 4-review request. This case is fixed with 1 review per request. |
| W21 | Ech kommen ëmmer gär fir de Kaffi zréck. | (none) | cold_coffee | **Praise read as a complaint.** "Kaffi" plus Luxembourgish, which the model handles weakly. A neighbouring review (W23) was also wrongly tagged cold_coffee. |
| W25 | De waarme Schockela war mir ze séiss. | other | cold_coffee | **Known categories forced onto "other" complaints.** "Too sweet hot chocolate" is not cold coffee. W23 (too loud) and W47 (too little milk foam) fail the same way. |
| H01 | The barista was rude and my latte arrived cold. | cold_coffee; unfriendly_staff | unfriendly_staff | **Only one complaint per text unit.** `evidence_units()` splits on `but / mais / aber / mee` but not on `and / et / und / an`, so both complaints share one unit and the model labels it once. H08 and H20 fail the same way. |
| H12 | I expected the coffee to be cold after reading reviews, but it was perfectly hot. | (none) | cold_coffee | **Negation or expectation.** The unit "I expected the coffee to be cold…" is labelled as a complaint. The keyword baseline fails here too. |
| W20 | D'Präisser sinn e bëssen héich. | high_prices | (none) | **Luxembourgish vocabulary.** The prompt gives Luxembourgish hints only for "lues" and "kal". H18 "Ze deier fir e Kaffi" is labelled `other`. |

## Candidate issues for the M4 "five issues + commit" item

These are not yet fixed. Each should be one commit, followed by a re-run with a new `--label`:

1. Send 1 review per request instead of groups of 4 (`review_groups` in `reviewwise/evidence.py`). Evidence: W29.
2. Also split evidence units on `and / et / und / an`, or let the prompt tag one unit with several categories. Evidence: H01, H08, H20.
3. In the prompt, tell the model to use `other` when no category fits exactly, with examples (taste, noise, portion). Evidence: W23, W25, W47.
4. Add Luxembourgish and German hints to `COMPACT_PROMPT` (`deier`, `héich`, `Präisser`, `lauwarm`). Evidence: W20, H18.
5. Add a negation and expectation rule ("only actual problems the guest experienced"). Evidence: H12.
