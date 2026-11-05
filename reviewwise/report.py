"""Reports use validated extractions, fixed action templates and Python counts."""

from datetime import timedelta

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


def reporting_week(day):
    """The user supplies the period; input review dates are not inferred."""
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def render_report(result, reporting_day=None):
    lines = [
        ("REVIEWWISE WEEKLY FEEDBACK REPORT" if reporting_day else "REVIEWWISE FEEDBACK REPORT") + (" — PARTIAL" if not result.complete else ""), "",
    ]
    if reporting_day:
        start, end = reporting_week(reporting_day)
        lines.extend([
            f"Reporting week: {start:%d %b %Y} - {end:%d %b %Y} (selected by you)",
            "Use only reviews from this week; input dates are not verified or filtered.", "",
        ])
    lines.extend([
        f"Reviews analyzed: {len(result.analyses)}",
        f"Reviews submitted: {result.total_reviews}",
        f"Reviews needing attention: {len(result.failures)}",
        f"Reviews pending: {len(result.pending)}",
        "Coverage: complete" if result.complete else "Coverage: PARTIAL — counts cover validated reviews only",
        f"Model: {result.model_name}", f"Model digest: {result.model_digest}",
        f"Report preparation time: {result.elapsed_seconds:.2f} seconds",
        f"New AI analyses: {len(result.analyses) - result.reused_reviews}",
        f"Validated analyses reused from this session: {result.reused_reviews}", "",
        f"AI requests attempted: {result.ai_requests}", "",
        "COMPLAINTS (counted by Python)",
    ])
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
    if result.failures:
        lines.extend(["", "REVIEWS NEEDING ATTENTION — NOT COUNTED"])
        for failure in result.failures:
            lines.extend([f"Review {failure.review.number}: {failure.review.text}", f"  {failure.reason}"])
    if result.pending:
        lines.extend(["", "PENDING REVIEWS — NOT COUNTED"])
        lines.extend(f"Review {review.number}: {review.text}" for review in result.pending)
    if result.stop_reason:
        lines.extend(["", f"Stopped: {result.stop_reason}"])
    lines.extend([
        "", "LIMITATIONS",
        "Counts are exact for validated AI labels, not guaranteed interpretations of the reviews.",
        "AI can miss feedback or misread languages, especially Luxembourgish. Check the evidence.",
        "The 'other' row combines unclassified complaints, which may concern different topics.",
        "This report concerns the supplied batch; review dates are not verified.",
    ])
    return "\n".join(lines) + "\n"
