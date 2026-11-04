"""Reports use validated extractions, fixed action templates and Python counts."""

from reviewwise.config import ACTIONS, CATEGORIES, MODEL
from reviewwise.pipeline import complaint_rows


def suggested_actions(analyses):
    actions = []
    for row in complaint_rows(analyses):
        if row["category"] in ACTIONS:
            actions.append(
                f"{ACTIONS[row['category']]} "
                f"Based on {row['Complaint'].lower()} in reviews {row['Review numbers']}."
            )
        if len(actions) == 3:
            break
    return actions


def render_report(result):
    lines = [
        "REVIEWWISE FEEDBACK REPORT", "",
        f"Reviews analyzed: {len(result.analyses)}",
        f"Model: {MODEL}", f"Model digest: {result.model_digest}",
        f"Analysis time: {result.elapsed_seconds:.2f} seconds", "",
        "COMPLAINTS (counted by Python)",
    ]
    rows = complaint_rows(result.analyses)
    for row in rows:
        lines.append(f"- {row['Complaint']}: {row['Reviews']} review(s); reviews {row['Review numbers']}")
    if not rows:
        lines.append("No complaints extracted. This does not prove that no complaints exist.")
    lines.extend(["", "PRACTICAL ACTIONS (templates based on extracted complaints)"])
    actions = suggested_actions(result.analyses)
    lines.extend(f"{i}. {action}" for i, action in enumerate(actions, 1))
    if len(actions) < 3:
        lines.append("Fewer than three actions are supported by the recognized complaint categories.")
    lines.extend(["", "REVIEW EVIDENCE"])
    for analysis in result.analyses:
        lines.extend(["", f"Review {analysis.review.number}: {analysis.review.text}"])
        for quote in analysis.extraction.positives:
            lines.append(f"  Positive feedback: {quote}")
        for item in analysis.extraction.complaints:
            lines.append(f"  {CATEGORIES[item.category]}: {item.quote}")
        if not analysis.extraction.positives and not analysis.extraction.complaints:
            lines.append("  No feedback extracted; inspect the original review.")
    lines.extend([
        "", "LIMITATIONS",
        "Counts are exact for validated AI labels, not guaranteed interpretations of the reviews.",
        "AI can miss feedback or misread languages, especially Luxembourgish. Check the evidence.",
        "The 'other' row combines unclassified complaints, which may concern different topics.",
        "This report concerns the supplied batch; review dates are not verified.",
    ])
    return "\n".join(lines) + "\n"
