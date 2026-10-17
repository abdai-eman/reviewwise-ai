
# ReviewWise - M2 Experiment 3
# Two-stage multilingual customer review analysis

from pathlib import Path
from ollama import chat

MODEL = "qwen2.5:3b"
OUTPUT_DIR = Path(__file__).parent

# Same 10 fictional reviews used in Experiments 1 and 2

# Fictional customer reviews from one cafe in Luxembourg
# 10 reviews including English, French, German and Luxembourgish


# 10 fictional cafe reviews in 4 languages
reviews = [
    # English
    "The coffee was excellent, but the service was very slow.",
    "Great atmosphere and friendly staff!",
    "The staff were helpful, but my order was incorrect.",

    # French
    "Le personnel était sympathique, mais mon café était froid.",
    "Le café était bon, mais les tables étaient sales.",

    # German
    "Der Kaffee war lecker, aber wir mussten lange warten.",
    "Das Personal war nett, aber die Preise waren zu hoch.",

    # Luxembourgish
    "De Service war ganz lues an ech hu laang op mäi Kaffi gewaart.",
    "D'Iesse war ganz gutt, mee d'Personal war net frëndlech.",
    "De Kaffi war kal an d'Präisser waren ze héich."
]


# Fictional customer reviews from one cafe in Luxembourg

def ask_ai(prompt):
    response = chat(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0}
    )
    return response.message.content


print("ReviewWise - M2 Experiment 3")
print("----------------------------")
print("Method: Two-stage analysis")
print(f"Model: {MODEL}")
print(f"Number of reviews: {len(reviews)}")

# STAGE 1: Analyze each review separately

individual_results = []

print("\nSTAGE 1: Analyzing individual reviews...")

for number, review in enumerate(reviews, start=1):

    review_prompt = f"""
You are ReviewWise, a multilingual customer feedback analyst.

Analyze ONE customer review written in English,
French, or German.

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

    result = ask_ai(review_prompt)
    individual_results.append(result)

    print(f"\nReview {number} analysis:")
    print(result)

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

report = ask_ai(report_prompt)

print("\n===== EXPERIMENT 3 WEEKLY REPORT =====\n")
print(report)

# Save the actual final report
report_path = OUTPUT_DIR / "experiment_output_3.txt"
report_path.write_text(report, encoding="utf-8")

# Save the prompts used in this experiment
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

STAGE 2 PROMPT:
"""

prompt_path.write_text(
    prompt_description + report_prompt,
    encoding="utf-8"
)

print("\nExperiment 3 completed!")
print(f"Individual analyses: {individual_path}")
print(f"Weekly report: {report_path}")
print(f"Prompt: {prompt_path}")
