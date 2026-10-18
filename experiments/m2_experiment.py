
# ReviewWise - M2 Experiment
# Multilingual customer reviews and weekly feedback

# Fictional customer reviews from one cafe in Luxembourg
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
print("ReviewWise - M2 Experiment")
print("--------------------------")
print(f"Number of reviews: {len(reviews)}")
print("\nPrompt prepared for AI analysis:\n")
print(prompt)

from ollama import chat

# Send the 10 reviews to the free AI model
print("\nAI is analyzing customer reviews...")

response = chat(
    model="qwen2.5:3b",
    messages=[
        {"role": "user", "content": prompt}
    ],
    options={"temperature": 0}
)

# Get the AI-generated report
report = response.message.content

# Display the result
print("\n===== REVIEWWISE WEEKLY REPORT =====\n")
print(report)

# Save the actual AI output
with open("experiments/experiment_output_original.txt", "w", encoding="utf-8") as file:
    file.write(report)

print("\nReport saved successfully!")
