"""ReviewWise presentation. Analysis, validation and counting live in reviewwise/."""

import html
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import streamlit as st

from reviewwise.config import CATEGORIES, MAX_REVIEW_LENGTH, MAX_REVIEWS, MODEL, OLLAMA_URL
from reviewwise.pipeline import (
    ReviewWiseError, complaint_rows, local_client, reviews_from_csv, reviews_from_text,
)
from reviewwise.jobs import is_busy, start_job
from reviewwise.report import render_report, reporting_week, suggested_actions


ROOT = Path(__file__).parent
HOST = urlsplit(OLLAMA_URL).hostname
IS_LOCAL = HOST in {"127.0.0.1", "localhost", "::1"}


def save_text():
    st.session_state.saved_review_text = st.session_state._review_text


def save_csv():
    upload = st.session_state.get("_csv_upload")
    st.session_state.saved_csv = upload.getvalue() if upload else b""
    st.session_state.saved_csv_name = upload.name if upload else ""


def load_sample():
    reviews = json.loads((ROOT / "experiments/reviews.json").read_text(encoding="utf-8"))
    st.session_state.saved_review_text = "\n".join(reviews)
    st.session_state._review_text = st.session_state.saved_review_text
    st.session_state.input_mode = "Paste reviews"
    st.session_state.pop("result", None)
    st.session_state.pop("last_result", None)


def clear_workspace():
    st.session_state.clear()


def show_review_text(text):
    # Guest text is escaped, never treated as markup or interactive HTML.
    st.markdown(f'<p class="rw-quote">{html.escape(text)}</p>', unsafe_allow_html=True)


def review_count_label(count):
    return f"{count} review{'s' if count != 1 else ''}"


def explain_error(error):
    message = str(error).lower()
    if "model is missing" in message:
        return "The analysis model isn’t ready yet.", "Reopen the ReviewWise launcher with internet access to finish setup, then try again."
    if "unavailable" in message:
        return "We couldn’t reach your local AI.", "Open Ollama on this computer, then try again. Your reviews are still here."
    if "could not analyze" in message or "could not analyse" in message:
        return "The local AI couldn’t analyse this review.", "Check that Ollama is open. Close applications that use a lot of memory, then try the review on its own."
    if "timed out" in message:
        return "This review took longer than expected.", "Try a smaller batch or a shorter review, and close applications that use a lot of memory."
    return "We couldn’t finish this batch.", "Your input is saved. Try the review mentioned in the details on its own, or use a smaller batch."


st.set_page_config(page_title="ReviewWise · Guest feedback, clearer", page_icon="☕", layout="wide")
css = (ROOT / "assets/interface.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

status = "Local processing" if IS_LOCAL else "Configured model service"
st.markdown(f"""
<div class="rw-header">
  <div class="rw-brand">
    <svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true">
      <rect width="36" height="36" rx="11" fill="#245747"/>
      <path d="M10 11h16v11H16l-5 4v-4h-1z" fill="none" stroke="#f7f5ef" stroke-width="1.6" stroke-linejoin="round"/>
      <path d="m14 16 3 3 5-5" fill="none" stroke="#e3c5ac" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span class="rw-brand-name">ReviewWise</span>
  </div>
  <span class="rw-status">{html.escape(status)}</span>
</div>
<div class="rw-intro">
  <div class="rw-kicker">A clearer view of your guest feedback</div>
  <h1>Your customers have insights. Find your next improvement.</h1>
  <p>Bring your reviews together to see what guests love, what keeps coming up, and where to focus next.</p>
</div>
<div class="rw-languages"><span>English</span><span>French</span><span>German</span><span>Luxembourgish</span></div>
""", unsafe_allow_html=True)
st.caption("Interpretations can vary by language, especially Luxembourgish. The original reviews stay available to check.")

for key, default in [("saved_review_text", ""), ("saved_csv", b""), ("saved_csv_name", ""), ("analysis_cache", {})]:
    st.session_state.setdefault(key, default)
job = st.session_state.get("analysis_job")
busy = job is not None and job.running
other_busy = is_busy() and not busy

workspace, companion = st.columns([2.05, 1], gap="large")
with workspace:
    with st.container(border=True, key="input_workspace"):
        st.subheader("What are your guests saying?")
        if IS_LOCAL:
            st.caption("Before you begin, remove names and personal details. Reviews are analysed on this computer.")
        else:
            st.caption(f"Before you begin, remove names and personal details. Reviews are sent to {HOST or 'an unconfirmed location'}; check the details before using personal information.")

        reporting_day = st.date_input(
            "Reporting week — choose any day", value=date.today(), key="reporting_day",
            format="DD/MM/YYYY", width=250, disabled=busy,
        )
        if reporting_day:
            week_start, week_end = reporting_week(reporting_day)
            week_label = f"{week_start:%d %b %Y} – {week_end:%d %b %Y}"
            st.caption(f"Monday–Sunday: {week_label}. Include only reviews from this week. The period is selected by you; review dates aren’t automatically checked or filtered.")
        else:
            st.warning("Choose a day in the reporting week to enable analysis.")

        mode = st.radio("Review input", ["Paste reviews", "Upload CSV"], key="input_mode", horizontal=True, label_visibility="collapsed", disabled=busy)
        if mode == "Paste reviews":
            if "_review_text" not in st.session_state:
                st.session_state._review_text = st.session_state.saved_review_text
            text = st.text_area(
                "One review per line", key="_review_text", on_change=save_text, height=150,
                placeholder="The staff were friendly, but the coffee was cold.\nLe service était agréable, mais nous avons attendu longtemps.",
                max_chars=MAX_REVIEWS * (MAX_REVIEW_LENGTH + 1),
                disabled=busy,
            )
            st.caption(f"Up to {MAX_REVIEWS:,} reviews per report · {MAX_REVIEW_LENGTH:,} characters per review.")
            raw_input = (mode, text)
            try:
                reviews, input_error = reviews_from_text(text), None
            except ReviewWiseError as exc:
                reviews, input_error = [], str(exc)
        else:
            st.file_uploader(
                "Choose a CSV file", type=["csv"], key="_csv_upload", on_change=save_csv,
                max_upload_size=1, help="Use UTF-8 and a column named review. Other columns are not sent for analysis.",
                disabled=busy,
            )
            st.caption(f"A column named ‘review’ is required · UTF-8 · Under 1 MB · Up to {MAX_REVIEWS:,} reviews per report.")
            if st.session_state.saved_csv_name:
                st.caption(f"Loaded: {st.session_state.saved_csv_name}")
            data = st.session_state.saved_csv
            raw_input = (mode, data)
            try:
                reviews = reviews_from_csv(data) if data else []
                input_error = None if data else "Choose a CSV file to begin."
            except ReviewWiseError as exc:
                reviews, input_error = [], str(exc)

        # Keep drafts across input-mode changes; show a report only for its matching input.
        if reporting_day and st.session_state.get("result_input") == raw_input and "last_result" in st.session_state:
            st.session_state.result = st.session_state.last_result
        else:
            st.session_state.pop("result", None)

        if reviews:
            st.caption(f"{review_count_label(len(reviews))} ready to analyse.")
            st.caption("Every accepted review is tracked. AI checks small groups; validated results appear below as they arrive. A review that needs attention is listed separately. A full first run can still take time on a laptop.")
            if len({review.text for review in reviews}) < len(reviews):
                st.warning("Some reviews are identical. Each input row will count as a separate review.")
        elif (mode == "Paste reviews" and text.strip()) or (mode == "Upload CSV" and data):
            st.error(input_error)
        else:
            st.caption("Add a review or try the fictional sample to enable analysis." if mode == "Paste reviews" else "Upload a CSV or try the fictional sample to enable analysis.")

        with st.container(key="primary_action"):
            start_analysis = st.button("Find my next improvements", type="primary", disabled=not reviews or not reporting_day or is_busy(), width="stretch")
        if is_busy() and not busy:
            st.warning("ReviewWise is already analysing a report in another tab. Finish or stop that analysis there before starting a new one.")

        if reviews:
            with st.expander(f"Preview {review_count_label(len(reviews))}"):
                if len(reviews) > 20:
                    st.caption(f"Showing the first 20 of {len(reviews)} reviews. All {len(reviews)} are selected for analysis.")
                for review in reviews[:20]:
                    show_review_text(f"{review.number}. {review.text}")

        st.button("Try sample reviews", on_click=load_sample, disabled=busy)
        st.caption("Ten fictional café reviews, provided for demonstration.")

        if start_analysis:
            try:
                st.session_state.analysis_job = start_job(reviews, st.session_state.analysis_cache)
                st.session_state.job_input = raw_input
                st.session_state.job_finalized = False
                st.session_state.pop("result", None)
                st.session_state.pop("last_result", None)
                st.rerun()
            except ReviewWiseError as exc:
                st.error(str(exc))

with companion:
    with st.container(border=True, key="companion"):
        st.markdown('<div class="rw-section-label">A useful next step, in three parts</div>', unsafe_allow_html=True)
        st.markdown("""
<div class="rw-guide"><div class="rw-guide-number">01</div><h3>See what guests appreciate.</h3><p>Keep the positive feedback in view, alongside the things that need attention.</p></div>
<div class="rw-guide"><div class="rw-guide-number">02</div><h3>Spot recurring complaints.</h3><p>See how often an issue appears and which reviews support it.</p></div>
<div class="rw-guide"><div class="rw-guide-number">03</div><h3>Choose practical next steps.</h3><p>Turn supported findings into a few concrete actions for your business.</p></div>
""", unsafe_allow_html=True)
    with st.expander("Processing details"):
        st.write(f"Model: {MODEL}")
        st.write(f"Model host: {HOST or 'not confirmed'}")
        st.caption("AI returns category and evidence-unit IDs for up to four short reviews per call. Python validates IDs, copies exact original passages and counts reviews. Suggestions use category-based templates.")
        st.caption("CPU use is limited to at most two inference threads. Short groups use a 2,048-token context; long reviews use 4,096. The model can still use several GB of RAM. Speed and accuracy need a real laptop test.")
        st.caption("No database or automatic report files. Your inputs stay in this session; download a report only if you want to keep it.")
        st.caption(f"Up to {MAX_REVIEWS:,} validated analyses are retained in this session to speed up retries and repeat reports. Start over clears them; closing or restarting the app can lose them. Changed model weights, prompts or settings require fresh analysis.")
    if st.session_state.saved_review_text or st.session_state.saved_csv:
        st.button("Start over", on_click=clear_workspace, width="stretch", disabled=busy)
    if st.button("Release AI memory", disabled=is_busy(), width="stretch", help="Unload the local model. New reviews will need to load it again."):
        try:
            with local_client() as client:
                client.generate(model=MODEL, prompt="", keep_alive=0)
            st.success("Asked Ollama to unload the analysis model. Your results are kept in this session.")
        except Exception:
            st.warning("Could not release the model. Quit Ollama from the Windows system tray when you have finished analysing.")

def render_result(result, week_label, reporting_day):
    rows = complaint_rows(result.analyses)
    actions = suggested_actions(result.analyses)
    st.divider()
    st.markdown('<div class="rw-section-label">From feedback to focus</div>', unsafe_allow_html=True)
    st.subheader("Your weekly feedback report" if result.complete else "Your weekly feedback report — partial")
    st.write(f"**{week_label}**")
    st.caption("Reporting week selected by you. Review dates are not verified or filtered.")
    if not result.complete:
        st.warning(f"Partial coverage: {len(result.analyses)} of {result.total_reviews} reviews have validated results; {len(result.failures)} need attention and {len(result.pending)} are waiting. Counts below cover only validated reviews.")
    if result.stop_reason:
        st.info(result.stop_reason)
    st.caption(f"{review_count_label(len(result.analyses))} included · Report prepared in {result.elapsed_seconds:.1f} seconds")
    st.caption(f"{len(result.analyses) - result.reused_reviews} newly analysed by AI · {result.reused_reviews} reused from validated analyses in this session.")
    metrics = st.columns(3)
    for column, label, value in zip(metrics, ["Reviews analysed", "Complaint groups", "Suggested actions"], [len(result.analyses), len(rows), len(actions)]):
        column.metric(label, value, border=True)
    st.caption("AI interpretations can be mistaken. Check the original evidence before making a decision; counts reflect the extracted labels.")

    overview, evidence = st.tabs(["Overview", "Review evidence"])
    with overview:
        issues, praise = st.columns([1.35, 1], gap="large")
        with issues:
            st.markdown("### What needs attention")
            if rows:
                st.vega_lite_chart(
                    spec={
                        "data": {"values": [{"Complaint": row["Complaint"], "Reviews": row["Reviews"]} for row in rows]},
                        "encoding": {
                            "y": {"field": "Complaint", "type": "nominal", "sort": None,
                                  "axis": {"title": None, "labelLimit": 130}},
                            "x": {"field": "Reviews", "type": "quantitative",
                                  "axis": {"title": "Number of reviews", "tickMinStep": 1}},
                        },
                        "layer": [
                            {"mark": {"type": "bar", "color": "#245747", "cornerRadiusEnd": 3}},
                            {"mark": {"type": "text", "align": "left", "dx": 7, "color": "#26352d", "fontSize": 13},
                             "encoding": {"text": {"field": "Reviews", "type": "quantitative"}}},
                        ],
                        "padding": {"right": 24},
                        "config": {
                            "background": "#f7f5ef", "view": {"stroke": None},
                            "axis": {"labelColor": "#4b5c4d", "titleColor": "#4b5c4d",
                                     "labelFontSize": 13, "titleFontSize": 13, "titleFontWeight": "normal",
                                     "gridColor": "#e2dfd4", "domain": False, "ticks": False,
                                     "labelPadding": 10, "titlePadding": 15},
                        },
                    },
                    theme=None, height=max(180, len(rows) * 42), width="stretch",
                    alt="Number of reviews in each extracted complaint group",
                )
                with st.expander("View exact counts and supporting reviews"):
                    st.dataframe([{k: v for k, v in row.items() if k != "category"} for row in rows], hide_index=True)
                if any(row["category"] == "other" for row in rows):
                    st.caption("‘Other complaints’ may concern unrelated topics. Inspect those reviews individually.")
            else:
                st.info("No complaints were identified in the validated reviews so far. Pending or failed reviews are not included. Check the original evidence.")
        with praise:
            st.markdown("### What guests appreciate")
            positives = [(analysis.review.number, quote) for analysis in result.analyses for quote in analysis.extraction.positives]
            if positives:
                for number, quote in positives[:3]:
                    with st.container(border=True):
                        st.caption(f"From review {number}")
                        show_review_text(quote)
                if len(positives) > 3:
                    st.caption("More positive feedback is available in Review evidence.")
            else:
                st.caption("No positive feedback was extracted. The original reviews are available to check.")

        st.markdown("### Practical next steps")
        st.caption("These are recommendations based on the findings, not statements made by customers.")
        if actions:
            for number, (column, action) in enumerate(zip(st.columns(len(actions)), actions), 1):
                with column:
                    with st.container(border=True):
                        st.markdown(f'<div class="rw-action-number">SUGGESTION {number:02d}</div>', unsafe_allow_html=True)
                        st.write(action)
        if not actions:
            st.caption("No category-specific suggestion is available for this batch. Check the review evidence to decide on your next step.")
        elif len(actions) < 3:
            st.caption("These are the specific suggestions supported by the recognised complaint groups.")

    with evidence:
        st.caption("Original reviews and the exact quotations behind the findings.")
        if result.running and len(result.analyses) > 5:
            st.caption("Showing the latest five validated reviews while analysis runs. The download includes every validated review; the full evidence list appears when analysis stops or finishes.")
        for analysis in (result.analyses[-5:] if result.running else result.analyses):
            with st.expander(f"Review {analysis.review.number}"):
                st.write("**Original review**")
                show_review_text(analysis.review.text)
                st.write("**Positive feedback**")
                for quote in analysis.extraction.positives:
                    show_review_text(quote)
                if not analysis.extraction.positives:
                    st.caption("None extracted.")
                st.write("**Complaints**")
                for item in analysis.extraction.complaints:
                    show_review_text(f"{CATEGORIES[item.category]}: {item.quote}")
                if not analysis.extraction.complaints:
                    st.caption("None extracted.")
        for failure in result.failures:
            with st.expander(f"Review {failure.review.number} — needs attention"):
                show_review_text(failure.review.text)
                st.caption("Not included in complaint counts or suggestions.")
                st.text(failure.reason)
    start, _ = reporting_week(reporting_day)
    st.download_button("Download my feedback report" if result.complete else "Download partial feedback report", render_report(result, reporting_day=reporting_day), f"reviewwise-week-{start.isoformat()}{'' if result.complete else '-partial'}.txt", "text/plain", type="primary")
    with st.expander("Report details"):
        st.text(f"Model: {MODEL}\nModel digest: {result.model_digest}")
        st.caption(f"Coverage: {len(result.analyses)} validated / {result.total_reviews} submitted. Model requests: {result.ai_requests}. Review dates, business identity and authenticity have not been verified.")


@st.fragment(run_every=1 if busy or other_busy else None)
def analysis_panel():
    if other_busy and not is_busy():
        st.rerun()
    if not reporting_day:
        return
    active_job = st.session_state.get("analysis_job")
    if active_job and st.session_state.get("job_input") == raw_input:
        result, error, cache, running, stopping = active_job.snapshot()
        st.session_state.analysis_cache = cache
        if not running and not st.session_state.get("job_finalized"):
            st.session_state.job_finalized = True
            if result:
                st.session_state.result = result
                st.session_state.last_result = result
                st.session_state.result_input = raw_input
            st.rerun()
        if running:
            checked = len(result.analyses) + len(result.failures) if result else 0
            total = len(active_job.reviews)
            st.progress(checked / total, text=f"{checked} of {total} reviews checked")
            st.write("Stopping the active model request…" if stopping else "Looking for patterns in your reviews…")
            if st.button("Stop analysis", disabled=stopping):
                active_job.cancel()
                st.rerun()
            st.caption("Validated results appear below while analysis continues. Stopping closes the streamed request when the next response arrives; a stalled request can take up to the read timeout.")
        if error:
            title, guidance = explain_error(error)
            st.error(title)
            st.write(guidance)
            with st.expander("Technical details"):
                st.text(str(error))
        if result:
            render_result(result, week_label, reporting_day)
        elif running:
            st.info("Waiting for the first validated group. The browser remains available and you can stop the analysis above.")
    elif "result" in st.session_state:
        render_result(st.session_state.result, week_label, reporting_day)


analysis_panel()

st.markdown('<div class="rw-footer">ReviewWise · A clearer view of customer feedback for hospitality businesses in Luxembourg.</div>', unsafe_allow_html=True)
