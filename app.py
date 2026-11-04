"""Local ReviewWise interface. Start with start.bat or bash start.sh."""

import json
from pathlib import Path

import streamlit as st

from reviewwise.config import CATEGORIES, MAX_REVIEWS, MODEL
from reviewwise.pipeline import (
    ReviewWiseError, analyze_reviews, complaint_rows, reviews_from_csv, reviews_from_text,
)
from reviewwise.report import render_report, suggested_actions


st.set_page_config(page_title="ReviewWise", page_icon="☕", layout="centered")
st.title("ReviewWise")
st.write("Understand customer feedback and choose what to improve next.")
st.caption(
    f"Local AI: Ollama · {MODEL} · English, French, German and Luxembourgish · "
    f"Up to {MAX_REVIEWS} reviews per batch"
)
st.info("Remove names and personal details before analysis. Reviews are sent only to Ollama on this computer.")

mode = st.radio("Review input", ["Paste reviews", "Upload CSV"], horizontal=True)
if "review_text" not in st.session_state:
    st.session_state.review_text = ""

if mode == "Paste reviews":
    if st.button("Load fictional M2 example"):
        example = Path(__file__).parent / "experiments" / "reviews.json"
        st.session_state.review_text = "\n".join(json.loads(example.read_text(encoding="utf-8")))
        st.session_state.pop("result", None)
    text = st.text_area(
        "One review per line", key="review_text", height=200,
        placeholder="The coffee was excellent, but we waited too long.\nLe personnel était sympathique.",
        max_chars=25_000,
    )
    raw_input = (mode, text)
    try:
        reviews = reviews_from_text(text)
        input_error = None
    except ReviewWiseError as exc:
        reviews, input_error = [], str(exc)
else:
    upload = st.file_uploader("UTF-8 CSV with a 'review' column", type=["csv"], max_upload_size=1)
    data = upload.getvalue() if upload else b""
    raw_input = (mode, data)
    try:
        reviews = reviews_from_csv(data) if upload else []
        input_error = None if upload else "Choose a CSV to begin."
    except ReviewWiseError as exc:
        reviews, input_error = [], str(exc)

# Editing input invalidates old results, including after a failed analysis.
if st.session_state.get("result_input") != raw_input:
    st.session_state.pop("result", None)

if reviews:
    with st.expander(f"Preview {len(reviews)} review(s)", expanded=False):
        for review in reviews:
            st.text(f"{review.number}. {review.text}")
    if len({review.text for review in reviews}) < len(reviews):
        st.warning("Identical reviews are present. Each input row will count as a separate review.")
elif input_error:
    st.caption(input_error)

if st.button("Analyze reviews", type="primary", disabled=not reviews):
    st.session_state.pop("result", None)
    progress = st.progress(0, text="Checking Ollama and the model…")
    try:
        with st.spinner("Analyzing locally. CPU inference can take several minutes."):
            result = analyze_reviews(
                reviews,
                progress=lambda done, total: progress.progress(
                    done / total, text=f"Analyzed {done} of {total} reviews"
                ),
            )
        st.session_state.result = result
        st.session_state.result_input = raw_input
    except ReviewWiseError as exc:
        st.error(str(exc))
    finally:
        progress.empty()

if "result" in st.session_state:
    result = st.session_state.result
    st.subheader("Feedback report")
    st.caption(f"{len(result.analyses)} reviews analyzed in {result.elapsed_seconds:.1f} seconds")
    st.warning("AI can misinterpret reviews. Counts reflect its extracted labels; inspect the supporting evidence.")
    rows = complaint_rows(result.analyses)
    if rows:
        st.dataframe([{k: v for k, v in row.items() if k != "category"} for row in rows], hide_index=True)
    else:
        st.write("No complaints were extracted. Check the original reviews for missed feedback.")

    st.subheader("Practical actions")
    actions = suggested_actions(result.analyses)
    for number, action in enumerate(actions, 1):
        st.write(f"{number}. {action}")
    if len(actions) < 3:
        st.caption("Fewer than three actions are supported. We do not invent feedback to fill the list.")

    st.subheader("Positive feedback and complaint evidence")
    for analysis in result.analyses:
        with st.expander(f"Review {analysis.review.number}"):
            st.text(analysis.review.text)
            st.write("Positive feedback")
            if not analysis.extraction.positives:
                st.caption("None extracted.")
            for quote in analysis.extraction.positives:
                st.text(quote)
            st.write("Complaints")
            if not analysis.extraction.complaints:
                st.caption("None extracted.")
            for item in analysis.extraction.complaints:
                st.text(f"{CATEGORIES[item.category]}: {item.quote}")
    st.download_button(
        "Download report (.txt)", render_report(result),
        file_name="reviewwise-report.txt", mime="text/plain",
    )
    if st.button("Clear reviews and results"):
        st.session_state.clear()
        st.rerun()

st.caption("No database or automatic report files. Download reports only when you want to keep them.")
