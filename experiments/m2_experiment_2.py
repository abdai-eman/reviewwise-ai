
# ReviewWise - M2 Experiment 2
# Improved prompt for multilingual customer review analysis

from pathlib import Path
from ollama import chat

# Fictional customer reviews from one cafe in Luxembourg
# Same 10 reviews as Experiment 1 for a fair comparison
reviews = [
    "The coffee was excellent, but the service was very slow.",
    "Le personnel était sympathique, mais mon café était froid.",
    "Der Kaffee war lecker, aber wir mussten lange warten.",
    "Great atmosphere and friendly staff!",
    "Le café était bon, mais les tables étaient sales.",
    "Das Personal war nett, aber die Preise waren zu hoch.",
    "The pastries were delicious, but there were not enough seats.",
    "Très bon cappuccino, mais le service était trop lent.",
    "Die Musik war zu laut und wir konnten uns kaum unterhalten.",
    "The staff were helpful, but my order was incorrect."
]

# Experiment 2: Improved instructions for the AI model
prompt = """
You are ReviewWise, an AI assistant for small businesses
in Luxembourg.

Analyze the following customer reviews from one cafe.

Create a weekly feedback report in clear English with:

1. Overall summary of customer feedback.
2. Main positive feedback, grouped by topic.
3. Customer complaints, grouped by topic.
4. Exactly three practical improvements for next week.

IMPORTANT RULES:

1. Analyze all 10 reviews exactly once.
2. Understand reviews written in English, French, and German.
3. Group complaints with the same meaning across languages.
4. Do not repeat, invent, or misrepresent customer feedback.
5. For each complaint category, provide:
   - The complaint name.
   - The number of reviews mentioning it.
   - The supporting review numbers.
6. Do not place unrelated complaints in the same category.
7. Include complaints mentioned only once.
8. Sort complaint categories by frequency, highest first.
9. Keep positive feedback separate from complaints.
10. Base all three improvements on the actual reviews.

Use this report structure:

WEEKLY FEEDBACK REPORT

1. OVERALL SUMMARY
Provide a short summary.

2. MAIN POSITIVE FEEDBACK
Group positive feedback by topic.

3. CUSTOMER COMPLAINTS
For each complaint, show:
- Complaint:
- Number of reviews:
- Review numbers:

4. THREE PRACTICAL IMPROVEMENTS
Give exactly three specific actions.

Do not add information that is not supported by the reviews.

Customer reviews:
"""

# Add all reviews to the prompt
for i, review in enumerate(reviews, start=1):
    prompt += f"\n{i}. {review}"

# Display experiment information
print("ReviewWise - M2 Experiment 2")
print("----------------------------")
print(f"Number of reviews: {len(reviews)}")
print("Model: qwen2.5:3b")
print("Prompt version: Improved")
print("\nPrompt prepared for AI analysis:\n")
print(prompt)

# Send the reviews to the local AI model
print("\nAI is analyzing customer reviews...")

response = chat(
    model="qwen2.5:3b",
    messages=[
        {"role": "user", "content": prompt}
    ],
    options={"temperature": 0}
)

# Get the actual AI-generated report
report = response.message.content

# Display the report
print("\n===== REVIEWWISE WEEKLY REPORT =====\n")
print(report)

# Save Experiment 2 output
output_path = Path(__file__).parent / "experiment_output_2.txt"

with open(output_path, "w", encoding="utf-8") as file:
    file.write(report)

# Save the exact prompt used for Experiment 2
prompt_path = Path(__file__).parent / "experiment_prompt_2.txt"

with open(prompt_path, "w", encoding="utf-8") as file:
    file.write(prompt)

print("\nExperiment 2 completed!")
print(f"Report saved to: {output_path}")
print(f"Prompt saved to: {prompt_path}")
