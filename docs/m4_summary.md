# ReviewWise — M4 summary

**Team:** MAKNI Abdourrahmane · HAFT Benjamin · ABDAI Eman

**Repository:** https://github.com/abdai-eman/reviewwise-ai/tree/m4-evaluation

**Deadline:** 30 November 2026, 23:59. **Submission tag:** `M4-submission`. **Evaluation data:** `evaluation/`

**Task and evaluation.** For each review, ReviewWise must find the complaint categories it contains,
with no false complaints. We wrote complaint labels by hand for **70 fictional reviews**: our 50 Workbook1
reviews plus 20 harder cases. The harder cases cover wrong orders, rude staff, two complaints in one
review, negation, sarcasm and a prompt-injection attempt; the 70 split into 21 English, 17 French,
16 German and 16 Luxembourgish. The metric is **F1 over (review, category) pairs**. The baseline is a
keyword matcher with no AI. Model: `qwen2.5:3b` via local Ollama, temperature 0. The two recorded M3 runs produced identical predictions.

| Version | F1 | Precision | Recall | Complaint yes/no | Count error | Worst request |
|---|---|---|---|---|---|---|
| Keyword baseline (no AI) | 0.86 | 94% | 79% | 86% | 10 | — |
| **M3 model (before)** | **0.71** | 74% | 68% | 94% | 13 | 1.36 s |
| **After fixes 1–5** | **0.83** | 88% | 79% | 96% | 10 | 0.48 s |

"Complaint yes/no": reviews correctly classified as with or without a complaint (67 of 70 after the fixes);
29 of the 32 reviews with a real complaint (about 91%) were detected. F1 by language after the fixes, keyword
baseline in brackets: English 0.95 (0.70), French 1.00 (0.93), German 0.84 (0.95),
**Luxembourgish 0.50 (0.88)**.

**Five issues found and fixed** (each a separate commit; F1 after the fix):

1. Reviews in the same request influenced each other ("service lent" was tagged as high prices).
   We now send one review per request. F1 0.75; worst request time 1.36 s down to 0.47 s. Commit [aac8dbb](https://github.com/abdai-eman/reviewwise-ai/commit/aac8dbb17373e36a757a81c2bb9bd0039efb4297).
2. Two complaints joined by "and" gave only one label. Text is now also split on and/et/und/an. F1 0.78. Commit [bb3a679](https://github.com/abdai-eman/reviewwise-ai/commit/bb3a6792d83d3bee4f04287fdc82485fd0207ef0).
3. Complaints fitting no category were forced into a named one (noise tagged "unfriendly staff"). The prompt
   now says to use "other" unless a category matches exactly. F1 0.83. Commit [80251b3](https://github.com/abdai-eman/reviewwise-ai/commit/80251b36e56247f2b69c9778ab76bc1e244150f1).
4. Luxembourgish and German price words were missed. We added hint words in FR, DE and LU to the
   prompt. F1 0.83; count error 10 down to 7. Commit [16876a6](https://github.com/abdai-eman/reviewwise-ai/commit/16876a619fa7f63bc531d83ab31c50a9bd1cd1e2).
5. Expectations and instructions inside a review were labelled as complaints. The prompt now excludes
   them. F1 0.83; precision on the harder cases reached 100%. Commit [5c0a838](https://github.com/abdai-eman/reviewwise-ai/commit/5c0a838f888252ab55d15ec477424b115193447f).

**Failure cases** (actual input and output after the fixes):

- "Et war leider zimlech haart am Café." (too loud): output *cold coffee*, expected *other*.
- "De Service war gutt mee e bësse lues." (a bit slow): output *cold coffee*, expected *slow service*. This was correct before fix 4.
- "Ze deier fir e Kaffi." (too expensive): no complaint found, expected *high prices*.

All three are Luxembourgish. When the 3B model does not understand a review, it often falls back to
"cold coffee", which wrongly makes cold coffee the top issue on Workbook1.

**Cost.** The approach did not change, so there is still no API fee. Each review is now one local
request, taking about 0.3 s per review on an Apple M5 Pro. Hardware and electricity costs are not
measured yet.

**Caveats and next steps.** Fixes 3–5 were tuned on the same small set, so small differences need caution;
we will check them on about 15 new reviews. The keyword baseline was written after seeing the cases, so it is optimistic.
Next, we will improve Luxembourgish by combining keyword rules with the model or by testing a larger model.
