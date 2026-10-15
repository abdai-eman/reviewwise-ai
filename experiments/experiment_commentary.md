# ReviewWise — M2 Experiment Commentary

## 1. Experiment Objective

We tested whether Qwen2.5 (3B), running locally through Ollama, could analyze multilingual café reviews and generate a useful weekly report.

We used 10 fictional reviews written in English, French and German. The same reviews were used in all three experiments so we could compare the outputs.

We checked whether the AI could identify positive feedback, group similar complaints, count complaints correctly and suggest three improvements.

## 2. Experiment 1 — Basic Prompt

**Method:** We sent all 10 reviews to the model in one prompt and asked it to generate a weekly report.

**Output:** `experiment_output_1.txt`

The AI generated a report, but we found several problems:

- It repeated the same feedback multiple times.
- It mixed unrelated complaints, including pricing and service issues.
- It missed some complaints, such as cold coffee, limited seating and incorrect orders.

For example, the report repeated feedback about helpful staff instead of correctly identifying all the different customer complaints.

**Our observation:** The model understood the general feedback but did not organize it accurately. We decided to test a more detailed prompt.

## 3. Experiment 2 — Improved Prompt

**Method:** We used the same reviews but added instructions to avoid repetition, group similar complaints, count them and provide supporting review numbers.

**Output:** `experiment_output_2.txt`

The report was better organized, but the complaint counts and review numbers were incorrect.

| Complaint | Correct result | AI result |
|---|---|---|
| Slow service | 3 reviews (1, 3, 8) | 4 reviews (1, 8, 9, 10) |
| Dirty tables | 1 review (5) | 2 reviews (4, 5) |
| High prices | 1 review (6) | 2 reviews (6, 7) |
| Cold coffee | 1 review (2) | Missing |
| Limited seating | 1 review (7) | Missing |
| Loud music | 1 review (9) | Missing |
| Incorrect order | 1 review (10) | Missing |

For example, review 9 complained about loud music, but the model classified it as slow service. Review 7 complained about insufficient seating, but the model classified it as high prices.

**Our observation:** Clearer instructions improved the report's structure but did not solve the accuracy problems.

## 4. Experiment 3 — Two-Stage Analysis

**Method:** We divided the analysis into two stages.

1. The model analyzed each review separately and extracted positive and negative feedback.
2. The model combined those individual analyses into a weekly report.

**Outputs:**
- `experiment_3_individual_analysis.txt` — Results from the first stage.
- `experiment_output_3.txt` — Final weekly report.

The first stage worked well. For example, the model correctly identified cold coffee in review 2, long waiting times in review 3 and an incorrect order in review 10.

However, the final report still had errors:

- Slow service and long waiting times were treated as separate complaints, even though they describe the same issue.
- Cold coffee was incorrectly attributed to review 3.
- Limited seating in review 7 was incorrectly grouped with waiting times.
- The incorrect order in review 10 was missing.

**Our observation:** The individual analyses were mostly correct, but errors appeared when the model combined the results. This method made it easier to identify where mistakes happened.

## 5. Comparison of the Three Outputs

| Experiment | Approach | Main result |
|---|---|---|
| 1 | Basic prompt | Repeated information and incorrect complaint grouping |
| 2 | Improved prompt | Better structure but incorrect counts and missing complaints |
| 3 | Two-stage analysis | Better individual analysis but errors in the final report |

All three experiments generated reports, but none produced completely accurate complaint counts and categories.

## 6. Conclusion and Next Step

We selected the **two-stage approach from Experiment 3** as the starting point for our MVP because it allows us to check the results for each review before generating the final report.

For the next version, we plan to use Python to validate complaint categories and counts instead of relying entirely on the AI.

Our tests were limited to 10 fictional reviews, so we still need to test with more data. We also need to measure processing time, especially because Experiment 3 makes more model calls.

## 7. Use of AI Tools

We used ChatGPT to help generate the Python scripts, prepare prompts and troubleshoot coding problems.

We used Ollama and Qwen2.5 (3B) to run the actual experiments.

We executed the scripts in VS Code and compared the generated reports with the original reviews.