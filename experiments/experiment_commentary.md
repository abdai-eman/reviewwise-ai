# M2 – AI Experiment Commentary

**Project:** ReviewWise  
**Model:** Qwen2.5 (3B) via Ollama  
**Dataset:** 10 fictional café reviews in English, French, German and Luxembourgish.

## Objective

The objective was to compare three prompting approaches for generating a weekly customer feedback report. All three experiments used the same 10 reviews to make the comparison consistent.

## Experiment 1 – Basic Prompt

**Method:** The model received all 10 reviews in one prompt and was asked to summarize positive feedback, group complaints and suggest three improvements.

**Result:** The report was generated in **230.39 seconds**. It correctly identified slow service in reviews 1, 6 and 8 and recognized some Luxembourgish feedback.

**Problems:** It incorrectly grouped unrelated complaints, included wrong supporting reviews and mixed positive and negative feedback. Cold coffee and unfriendly staff were not listed as separate complaint categories.

**Conclusion:** The basic prompt generated a readable report but lacked reliable complaint grouping.

## Experiment 2 – Improved Prompt

**Method:** The model received the same 10 reviews with stricter instructions requiring complaint categories, frequencies, supporting review numbers and exactly three improvements.

**Result:** The report was generated in **153.44 seconds**. Its structure was clearer and it correctly identified the incorrect-order complaint in review 3.

**Problems:** Complaint counts remained inaccurate. Slow service appeared in three reviews (1, 6 and 8), but the model reported one. It referenced review 4 instead of review 5 for dirty tables, missed cold coffee and unfriendly staff, and undercounted high prices. The prompt explicitly mentioned English, French and German but omitted Luxembourgish.

**Conclusion:** The improved prompt produced better formatting but did not solve accuracy problems.

## Experiment 3 – Two-Stage Analysis

**Method:** The model first analyzed each of the 10 reviews individually, then generated a weekly report from those analyses.

**Result:** The experiment took **318.20 seconds**. Individual analysis correctly extracted most English, French and German feedback.

**Problems:** Luxembourgish understanding was inconsistent. Review 8's slow-service complaint was missed, review 9's positive food feedback was missed, and review 10's cold coffee and high prices were not understood. The final report incorrectly claimed seven slow-service complaints instead of three and three cleanliness complaints instead of one. It also omitted several complaint categories.

**Conclusion:** The two-stage method made individual extraction errors visible but did not improve final-report accuracy. It was also the slowest approach.

## Comparison

| Criterion | Experiment 1 | Experiment 2 | Experiment 3 |
|---|---|---|---|
| Method | Basic prompt | Improved prompt | Two-stage |
| Reviews | 10 | 10 | 10 |
| Languages | EN, FR, DE, LU | EN, FR, DE, LU | EN, FR, DE, LU |
| Runtime | 230.39 s | 153.44 s | 318.20 s |
| Report structure | Repetitive | Clear | Clear |
| Complaint accuracy | Unreliable | Unreliable | Unreliable |
| Luxembourgish handling | Partial | Weak | Weak |

## Final Decision and Next Steps

**Experiment 2 produced the clearest report and was fastest in these runs**, but none of the three approaches reliably counted or grouped complaints.

For the MVP, we propose using **Qwen2.5 (3B) through Ollama with structured individual review extraction and Python-based complaint counting**, followed by report generation. This extends Experiment 3; the Python validation step has not yet been implemented or tested.

The next steps are to improve Luxembourgish recognition, validate extracted complaints against original reviews, and calculate complaint frequencies in Python rather than relying on AI-generated counts.

If accuracy or processing speed remains insufficient, we will evaluate a stronger local model or a cloud API.

**Limitations of this evaluation:** The dataset contains only 10 fictional reviews, each method was run once, and the prompts did not all explicitly support Luxembourgish. Therefore, the results are preliminary rather than a definitive performance benchmark.

## Use of AI Tools

We used **ChatGPT (OpenAI)** to assist with writing and improving the Python experiment code, developing and refining prompts, organizing the testing process, and analyzing the experiment results.

All three experiments were executed locally using **Qwen2.5 (3B) through Ollama**. We reviewed the generated outputs, identified errors, and documented the findings ourselves.

ChatGPT was used as a development and learning assistant, not as the AI model generating the customer feedback reports.
