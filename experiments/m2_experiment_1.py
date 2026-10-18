import json
import time
from pathlib import Path
from ollama import chat

# ReviewWise - M2 Experiment 1
# Multilingual customer reviews and weekly feedback

# Fictional customer reviews from one cafe in Luxembourg
# 10 fictional cafe reviews in 4 languages

reviews_path = Path(__file__).parent / "reviews.json"

with open(reviews_path, "r", encoding="utf-8") as file:
    reviews = json.load(file)


# Instructions for the AI model
prompt = """
You are ReviewWise, an AI assistant for small businesses
in Luxembourg.

Analyze the following customer reviews from one cafe.

Create a weekly feedback report with:

1. Overall summary of customer feedback.
2. Main positive feedback.
3. Most common customer complaints.
4. Three practical improvements for next week.

Group similar complaints even when they are written
in different languages.

Do not invent complaints or information that is not
present in the reviews.

Write the report in clear English.

Customer reviews:
"""


# Add all reviews to the prompt
for i, review in enumerate(reviews, start=1):
    prompt += f"\n{i}. {review}"


# Display the experiment input
print("ReviewWise - M2 Experiment 1")
print("----------------------------")
print(f"Number of reviews: {len(reviews)}")
print("Model: qwen2.5:3b")
print("Prompt version: Basic")
print("\nPrompt prepared for AI analysis:\n")
print(prompt)


# Send the 10 reviews to the AI model
print("\nAI is analyzing customer reviews...")

start_time = time.perf_counter()

response = chat(
    model="qwen2.5:3b",
    messages=[
        {"role": "user", "content": prompt}
    ],
    options={"temperature": 0}
)

end_time = time.perf_counter()

runtime = end_time - start_time

print(f"\nAI runtime: {runtime:.2f} seconds")


# Get the AI-generated report
report = response.message.content


# Display the result
print("\n===== REVIEWWISE WEEKLY REPORT =====\n")
print(report)


# Set the output directory
OUTPUT_DIR = Path(__file__).parent


# Save the actual AI output and runtime
output_path = OUTPUT_DIR / "experiment_output_1.txt"

with open(output_path, "w", encoding="utf-8") as file:
    file.write(report)
    file.write(f"\n\nAI runtime: {runtime:.2f} seconds\n")


# Save the exact prompt used for Experiment 1
prompt_path = OUTPUT_DIR / "experiment_prompt_1.txt"

with open(prompt_path, "w", encoding="utf-8") as file:
    file.write(prompt)


# Display completion message
print("\nExperiment 1 completed!")
print(f"Report saved to: {output_path}")
print(f"Prompt saved to: {prompt_path}")