import json
import time
from pathlib import Path
from ollama import chat

# ReviewWise - M2 Experiment 3
# Two-stage multilingual customer review analysis

MODEL = "qwen2.5:3b"
OUTPUT_DIR = Path(__file__).parent

# Same 10 fictional reviews used in Experiments 1 and 2
# 10 fictional cafe reviews in 4 languages

# Load the shared review dataset
reviews_path = OUTPUT_DIR / "reviews.json"

with open(reviews_path, "r", encoding="utf-8") as file:
    reviews = json.load(file)


# Track the total runtime of all AI calls
total_ai_runtime = 0.0


def ask_ai(prompt):
    global total_ai_runtime

    start_time = time.perf_counter()

    response = chat(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0}
    )

    end_time = time.perf_counter()
    runtime = end_time - start_time

    total_ai_runtime += runtime

    return response.message.content


print("ReviewWise - M2 Experiment 3")
print("----------------------------")
print("Method: Two-stage analysis")
print(f"Model: {MODEL}")
print(f"Number of reviews: {len(reviews)}")


# STAGE 1: Analyze each review separately

individual_results = []
stage1_prompts = []

print("\nSTAGE 1: Analyzing individual reviews...")

stage1_start = time.perf_counter()

for number, review in enumerate(reviews, start=1):

    review_prompt = f"""
You are ReviewWise, a multilingual customer feedback analyst.

Analyze ONE customer review written in English, French, German or Luxembourgish.

Review number: {number}
Review text: {review}

Extract:
1. Positive feedback mentioned in this review.
2. Negative feedback mentioned in this review.

Rules:
- Translate the meaning into clear English.
- Do not invent information.
- Do not confuse positive and negative feedback.
- If no positive or negative feedback exists, write "None".
- Keep your answer short.
- Do not analyze any other review.

Use exactly this format:

Review number: {number}
Positive feedback:
Negative feedback:
"""

    # Record the exact prompt sent for this review
    stage1_prompts.append(review_prompt)

    # Analyze the review
    result = ask_ai(review_prompt)
    individual_results.append(result)

    print(f"\nReview {number} analysis:")
    print(result)

stage1_end = time.perf_counter()
stage1_runtime = stage1_end - stage1_start

print(f"\nStage 1 runtime: {stage1_runtime:.2f} seconds")


# Save the individual analyses

individual_text = "\n\n".join(individual_results)

individual_path = OUTPUT_DIR / "experiment_3_individual_analysis.txt"

individual_path.write_text(
    individual_text,
    encoding="utf-8"
)


# STAGE 2: Generate the weekly report

print("\nSTAGE 2: Generating weekly report...")

report_prompt = """
You are ReviewWise, an AI assistant for small cafes
in Luxembourg.

Create a weekly customer feedback report using
the individual review analyses provided below.

IMPORTANT RULES:

1. Use only the provided analyses.
2. Do not invent complaints or positive feedback.
3. Group complaints with the same meaning.
4. Keep unrelated complaints separate.
5. Count each review only once per complaint category.
6. Provide the supporting review numbers.
7. Include complaints mentioned only once.
8. Write the report in clear English.
9. Suggest exactly three practical improvements.
10. Do not repeat customer feedback unnecessarily.

Use this structure:

WEEKLY FEEDBACK REPORT

1. OVERALL SUMMARY

2. MAIN POSITIVE FEEDBACK

3. CUSTOMER COMPLAINTS
For every complaint category include:
- Complaint name
- Number of reviews
- Supporting review numbers

4. THREE PRACTICAL IMPROVEMENTS

Individual review analyses:
"""

report_prompt += "\n\n" + individual_text

stage2_start = time.perf_counter()

report = ask_ai(report_prompt)

stage2_end = time.perf_counter()
stage2_runtime = stage2_end - stage2_start


# Display runtime results

print("\n===== RUNTIME RESULTS =====")
print(f"Stage 1 runtime: {stage1_runtime:.2f} seconds")
print(f"Stage 2 runtime: {stage2_runtime:.2f} seconds")
print(f"Total AI runtime: {total_ai_runtime:.2f} seconds")


# Display the final report

print("\n===== EXPERIMENT 3 WEEKLY REPORT =====\n")
print(report)


# Save the final report and runtime

report_path = OUTPUT_DIR / "experiment_output_3.txt"

report_path.write_text(
    report
    + f"\n\n===== RUNTIME RESULTS =====\n"
    + f"Stage 1 runtime: {stage1_runtime:.2f} seconds\n"
    + f"Stage 2 runtime: {stage2_runtime:.2f} seconds\n"
    + f"Total AI runtime: {total_ai_runtime:.2f} seconds\n",
    encoding="utf-8"
)


# Save ALL prompts used in this experiment

prompt_path = OUTPUT_DIR / "experiment_prompt_3.txt"

prompt_description = """
EXPERIMENT 3 - TWO-STAGE PROMPTING

Stage 1:
Each review is sent separately to Qwen2.5:3b.
The model extracts positive and negative feedback.

Stage 2:
The individual analyses are sent to the same model.
The model groups complaints, counts occurrences,
and generates the final weekly report.
"""

# Combine the exact prompts from both stages
all_prompts = (
    prompt_description
    + "\n\n===== STAGE 1 PROMPTS =====\n\n"
    + "\n\n".join(stage1_prompts)
    + "\n\n===== STAGE 2 PROMPT =====\n\n"
    + report_prompt
)

prompt_path.write_text(
    all_prompts,
    encoding="utf-8"
)


# Display completion messages

print("\nExperiment 3 completed!")
print(f"Individual analyses: {individual_path}")
print(f"Weekly report: {report_path}")
print(f"Prompt: {prompt_path}")
