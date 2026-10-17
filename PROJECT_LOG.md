# ReviewWise — Project Log

## M1 — Problem and Customer Validation

**Date:** 12 October 2026

### 1. Problem Statement

Small businesses in Luxembourg receive reviews in French, German, Luxembourgish, and English. Reading reviews manually can make it difficult to spot repeated problems and customer suggestions, especially when there are many reviews. This could take extra staff time, although we have not yet measured the cost for businesses with high review volumes.

ReviewWise aims to help businesses understand their reviews and identify what they could improve each week.

### 2. Users and Customers

**Users:** Owners and managers of small cafés, restaurants, and hotels in Luxembourg.

**Potential payers:** Business owners or managers. Pricing has not been decided.

**Market size:** Around 2,675 accommodation and food-service businesses in Luxembourg (2022). [1]

### 3. Existing Alternatives

- **Trustpilot Business:** Mainly focused on its own review platform.
- **Birdeye:** Offers a broader range of reputation-management features than our proposed tool.
- **Manual reading:** Finding repeated issues across many reviews takes time.

### 4. Value Proposition

For small-business owners in Luxembourg who want to understand multilingual customer feedback, ReviewWise is an AI-powered review analysis tool that suggests practical weekly improvements, unlike manually comparing reviews.

### 5. Why AI?

AI can recognize similar complaints written in different languages, group recurring feedback, and suggest improvements. Without AI, businesses would need to compare reviews manually or use language-specific rules.

### 6. Potential User Interviews

**Interview 1 — Hotel Bristol**

**Mr. Nea Marku, Receptionist | 10 October 2026 | 10–15 minutes**

- Mainly uses Booking.com and Airbnb.
- Reviews are handled manually, taking less than 30 minutes per week.
- Guest complaints are usually resolved directly by staff.
- Booking.com's translation feature helps with multilingual reviews.
- Fake reviews are a bigger problem than language differences.
- He felt AI review analysis might benefit larger hotels more than their 30-room hotel.
- Personal communication with guests remains important.

**Interview 2 — Bloom Specialty Coffee Shop**

**Café supervisor | 9 October 2026 | 12–15 minutes**

- Checks reviews once a week or every two weeks.
- Reviews are handled manually without AI tools.
- Negative reviews are uncommon.
- Customer suggestions are useful for improving the café.
- The supervisor reacted positively to ReviewWise, especially its improvement suggestions.
- The café does not currently pay for review-management software.
- No specific willingness-to-pay amount was established.

**Interview challenges:** We contacted several other businesses, but many were busy or preferred to reply later by email.

### Source

[1] STATEC, *Luxembourg in Figures 2025*, p. 48.

https://statistiques.public.lu/dam-assets/catalogue-publications/luxembourg-en-chiffres/2025/luxembourg-in-figures-2025.pdf

### Writing Improvement Tool Used

Grammarly was used to check grammar and improve wording.
______________________________________________________________________________________________---
## M2 – Technology Exploration and Project Proposal
**Date:** 19 October 2026

### 1. Technology Comparison
We compared two AI approaches for ReviewWise:
- **Qwen2.5 (3B) with Ollama:** Runs locally, has no API fees, and keeps customer reviews on the user's computer.
- **GPT-4.1 mini API:** Cloud-based alternative with usage-based pricing.

We selected Qwen2.5 with Ollama because it is free to use locally, offers better control over data, and has already been tested.

### 2. AI Experiment
We tested Qwen2.5 (3B) using 10 fictional multilingual customer reviews.

We conducted three experiments to analyze customer complaints and generate weekly improvement reports.

The results showed that the model could understand multilingual reviews and identify complaints, but sometimes made mistakes when grouping similar complaints and counting their frequency.

We decided to improve accuracy using Python validation.

The experiment scripts, saved outputs, and instructions are available in the repository.

### 3. Chosen Approach and Limitations
We chose Qwen2.5 (3B) with Ollama.

Current limitations:
- Incorrect complaint grouping and counts.
- Limited testing with only 10 fictional reviews; Luxembourgish remains untested.
- Multiple AI calls may increase processing time.

We may consider a larger local model or a cloud API if accuracy or performance remains insufficient.

### 4. Architecture
The planned system will accept multilingual customer reviews, analyze them locally using Python, Ollama, and Qwen2.5, and generate weekly reports containing recurring complaints and improvement suggestions.

### 5. Cost Estimate
Ollama runs the model locally without API fees.

For one weekly report containing 10 reviews:

11 AI calls × €0 = **€0 API cost per report**.

Electricity and hardware costs have not yet been measured.

### 6. MVP Development Plan
- **26 October:** Improve AI analysis and complaint counting — Abdourrahmane Makni.
- **5 November:** Build review input and weekly report interface — Benjamin Haft.
- **10 November:** Test multilingual reviews — Eman Abdai.
- **15 November:** Integrate components, fix bugs, and record demo — All members.

**MVP deadline:** 16 November 2026.

### 7. Repository
The project repository contains the AI experiments, saved results, and documentation.

