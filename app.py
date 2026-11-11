"""ReviewWise presentation. Analysis, validation and counting live in reviewwise/."""

import html
import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import streamlit as st

from reviewwise.config import ACTIONS, CATEGORIES, MAX_REVIEW_LENGTH, MAX_REVIEWS, MODEL, OLLAMA_URL
from reviewwise.pipeline import (
    ReviewWiseError, complaint_rows, local_client, reviews_from_csv, reviews_from_text,
)
from reviewwise.jobs import is_busy, start_job
from reviewwise.report import render_report, reporting_week, suggested_actions
from reviewwise.storage import ReportStore, load_report, report_document, reports_directory
from scripts.manage import ai_setup_status, start_ai_preparation


ROOT = Path(__file__).parent
REPORTS = ReportStore(reports_directory(ROOT))
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



def render_result(result, week_label, reporting_day, recorded_at=None):
    rows = complaint_rows(result.analyses)
    actions = suggested_actions(result.analyses)
    st.divider()
    st.markdown('<div class="rw-section-label">From feedback to focus</div>', unsafe_allow_html=True)
    st.subheader("Your weekly feedback report" if result.complete else "Your weekly feedback report — partial")
    st.write(f"**{week_label}**")
    if recorded_at is not None:
        timestamp = recorded_at.astimezone(ZoneInfo('Europe/Luxembourg')).strftime('%d %b %Y · %H:%M %Z')
        st.markdown(f'<div class="rw-recorded">SAVED REPORT · {html.escape(timestamp)}</div>', unsafe_allow_html=True)
        st.caption("This is a saved analysis. Opening it does not run the model again.")
    st.caption("Reporting week selected by you. Review dates are not verified or filtered.")
    if not result.complete:
        st.warning(f"Partial coverage: {len(result.analyses)} of {result.total_reviews} reviews have validated results; {len(result.failures)} need attention and {len(result.pending)} are waiting. Counts below cover only validated reviews.")
    if result.stop_reason:
        st.info(result.stop_reason)
    st.caption(f"{review_count_label(len(result.analyses))} included · Report prepared in {result.elapsed_seconds:.1f} seconds")
    if recorded_at:
        st.caption(f"Original run: {len(result.analyses) - result.reused_reviews} newly analysed by AI · {result.reused_reviews} reused. Opening this report made no new model calls.")
    else:
        st.caption(f"{len(result.analyses) - result.reused_reviews} newly analysed by AI · {result.reused_reviews} reused from validated analyses in this session.")
    if not recorded_at and st.button("Save this report", icon=":material/bookmark_add:", disabled=result.running):
        try:
            REPORTS.save(report_document(result, reporting_day))
            st.success("Saved on this computer. Open Saved reports to present it again without waiting for AI.")
        except (ValueError, OSError) as error:
            st.error(f"Could not save this report: {error}")
    metrics = st.columns(3)
    for column, label, value in zip(metrics, ["Reviews analysed", "Complaint groups", "Suggested actions"], [len(result.analyses), len(rows), len(actions)]):
        column.metric(label, value, border=True)
    st.caption("AI interpretations can be mistaken. Check the original evidence before making a decision; counts reflect the extracted labels.")
    if rows:
        first = rows[0]
        label = "A most recurring issue" if len(rows) > 1 and rows[1]["Reviews"] == first["Reviews"] else "Most recurring issue"
        st.markdown(f'<div class="rw-priority"><div class="rw-section-label">{label}</div><h3>{html.escape(first["Complaint"])}</h3><p>Found in <strong>{first["Reviews"]} of {len(result.analyses)} analysed reviews</strong>. Inspect the evidence before deciding what to change.</p></div>', unsafe_allow_html=True)

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
        action_rows = [row for row in rows if row["category"] in ACTIONS][:3]
        if action_rows:
            for number, (column, row) in enumerate(zip(st.columns(len(action_rows)), action_rows), 1):
                with column:
                    with st.container(border=True):
                        st.markdown(f'<div class="rw-action-number">SUGGESTION {number:02d}</div>', unsafe_allow_html=True)
                        st.markdown(f'**{row["Complaint"]}**')
                        st.write(ACTIONS[row["category"]])
                        st.caption(f'Supported by {row["Reviews"]} analysed reviews.')
                        with st.expander("Supporting review references"):
                            st.write(row["Review numbers"])
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
        st.caption(f"Coverage: {len(result.analyses)} validated / {result.total_reviews} submitted. Model requests: {result.ai_requests}. Review dates, business identity and authenticity have not been verified.")


def show_saved_reports():
    st.markdown('<div class="rw-section-label">READY WHEN YOU ARE</div>', unsafe_allow_html=True)
    st.title("Your saved reports")
    st.write("Open a genuine analysis, inspect its evidence and present the findings without waiting for the model again.")
    entries = REPORTS.list()
    if entries:
        labels = {name: f'{doc.title} · {doc.recorded_at:%d %b %Y, %H:%M}' for name, doc in entries}
        selected = st.selectbox("Reports saved on this computer", list(labels), format_func=labels.get)
        open_column, delete_column = st.columns([3, 1])
        with open_column:
            if st.button("Open saved report", type="primary", icon=":material/folder_open:"):
                st.session_state.opened_document = dict(entries)[selected]
                st.session_state.opened_saved_name = selected
        with delete_column:
            with st.popover("Manage"):
                if st.button("Delete selected saved report"):
                    REPORTS.delete(selected)
                    if st.session_state.get('opened_saved_name') == selected:
                        st.session_state.pop('opened_document', None)
                    st.rerun()
    else:
        st.info("Your saved reports will appear here. After an analysis finishes or stops, select Save this report.")
    sample = ROOT / 'docs/verification/recorded-ai-report.json'
    evidence = ROOT / 'docs/verification/windows-ai.json'
    if sample.exists() and evidence.exists():
        try:
            ready = json.loads(evidence.read_text(encoding='utf-8-sig')).get('passed') is True
        except (ValueError, OSError):
            ready = False
        if ready and st.button("Explore a recorded AI example"):
            st.session_state.opened_document = load_report(sample.read_bytes())
            st.session_state.opened_saved_name = None
    with st.expander("Open a report from another computer"):
        upload = st.file_uploader("Choose a ReviewWise report file", type=['json'], max_upload_size=20, key='_report_import')
        if upload:
            data = upload.getvalue()
            digest = hashlib.sha256(data).hexdigest()
            if digest != st.session_state.get('report_import_digest'):
                try:
                    st.session_state.opened_document = load_report(data)
                    st.session_state.opened_saved_name = None
                    st.session_state.report_import_digest = digest
                except ValueError:
                    st.error("This file is not a valid ReviewWise report with traceable evidence. Export the report again from the original computer.")
    document = st.session_state.get('opened_document')
    if document:
        st.caption(document.provenance)
        start, end = reporting_week(document.reporting_day)
        render_result(document.result, f'{start:%d %b %Y} – {end:%d %b %Y}', document.reporting_day, document.recorded_at)
        st.download_button("Download report for another computer", document.model_dump_json(indent=2), f'reviewwise-{start.isoformat()}.json', 'application/json')
        if not st.session_state.get('opened_saved_name') and st.button("Keep this report on this computer"):
            st.session_state.opened_saved_name = REPORTS.save(document)
            st.success("Saved locally. You can reopen it from this page.")


st.set_page_config(page_title="ReviewWise · Weekly guest intelligence", page_icon="☕", layout="wide", initial_sidebar_state="auto")
css = (ROOT / "assets/interface.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

for key, default in [("saved_review_text", ""), ("saved_csv", b""), ("saved_csv_name", ""), ("analysis_cache", {})]:
    st.session_state.setdefault(key, default)
job = st.session_state.get("analysis_job")
busy = job is not None and job.running
other_busy = is_busy() and not busy
ai_status = ai_setup_status()
preparing_ai = ai_status.get('state') in {'starting','downloading'}


@st.fragment(run_every=1 if preparing_ai else None)
def ai_preparation_panel():
    observed = ai_setup_status()
    if observed.get('state') != ai_status.get('state'):
        st.rerun()
    if observed.get('state') in {'starting','downloading'}:
        st.info(observed.get('message','Preparing local AI…'))
        st.caption("First-time preparation can take several minutes. You can explore saved reports while it runs.")
    elif observed.get('state') == 'ready':
        st.caption("● Local AI installed")
    elif observed.get('state') == 'error':
        st.warning("Local AI needs attention. Saved reports remain available.")
        with st.expander("Setup details"):
            st.text(observed.get('message',''))
    if observed.get('state') in {'unknown','error'}:
        if st.button("Prepare local AI", disabled=is_busy()):
            start_ai_preparation()
            st.rerun()

with st.sidebar:
    st.markdown('<div class="rw-sidebar-brand"><span class="rw-brand-symbol">RW</span><div>ReviewWise<small>GUEST FEEDBACK, CLEARER</small></div></div>', unsafe_allow_html=True)
    view = st.radio("Workspace", ["Analyse reviews", "Saved reports"], key="workspace_view", label_visibility="collapsed", disabled=busy)
    st.markdown('<div class="rw-sidebar-divider"></div>', unsafe_allow_html=True)
    st.caption("FOR CAFÉS, RESTAURANTS & HOTELS")
    st.write("A clearer view of what guests appreciate and what deserves your attention.")
    st.markdown('<div class="rw-sidebar-languages">EN · FR · DE · LU</div>', unsafe_allow_html=True)
    st.caption("Language accuracy varies, especially Luxembourgish. Check the original evidence.")
    ai_preparation_panel()
    with st.expander("Processing & privacy"):
        st.caption("Reviews are processed on this computer." if IS_LOCAL else f"Reviews are sent to {HOST}.")
        st.caption("AI selects feedback; Python validates evidence and counts reviews. Saved reports stay on this device until you export or delete them.")
        st.caption("A first analysis can take time. Previously saved reports open without another model run.")

status = "Local processing" if IS_LOCAL else "Configured model service"
st.markdown(f'<div class="rw-header"><div class="rw-workspace-label">WEEKLY GUEST INTELLIGENCE <span>/ {html.escape(view)}</span></div><span class="rw-status">{html.escape(status)}</span></div>', unsafe_allow_html=True)

if view == "Saved reports":
    show_saved_reports()
    st.stop()

st.markdown("""
<div class="rw-dashboard-hero">
 <div class="rw-hero-copy"><div class="rw-kicker">GOOD FEEDBACK. BETTER DECISIONS.</div>
 <h1>Your customers have insights.<br><span>Find your next improvement.</span></h1>
 <p>Bring your reviews together to see what guests love, what keeps coming up, and where to focus next.</p>
 <div class="rw-hero-caption">YOUR WEEKLY WORKSPACE · ORIGINAL EVIDENCE · PRACTICAL NEXT STEPS</div></div>
 <svg class="rw-venue" viewBox="0 0 300 200" aria-hidden="true">
  <circle cx="170" cy="102" r="83" fill="#315d4a"/>
  <path d="M52 169h225" stroke="#96af98" stroke-width="2"/>
  <rect x="92" y="72" width="153" height="96" rx="3" fill="#f1e7d4"/>
  <path d="m83 76 16-29h138l17 29" fill="#c27d57"/>
  <path d="M83 76h171v12c-11 11-22 11-34 0-11 11-22 11-34 0-11 11-22 11-34 0-11 11-22 11-34 0-11 11-22 11-35 0z" fill="#dfb99a"/>
  <rect x="111" y="107" width="50" height="38" rx="2" fill="#315d4a"/>
  <path d="M136 107v38m-25-19h50" stroke="#f1e7d4" stroke-width="2"/>
  <rect x="182" y="105" width="41" height="63" rx="2" fill="#315d4a"/>
  <circle cx="214" cy="138" r="2" fill="#dfb99a"/>
  <rect x="57" y="123" width="12" height="45" rx="3" fill="#9a6647"/>
  <circle cx="63" cy="109" r="20" fill="#789b77"/>
  <path d="m227 31 5-9 5 9m-5-9v19" fill="none" stroke="#dfb99a" stroke-width="2" stroke-linecap="round"/>
  <circle cx="108" cy="25" r="4" fill="#dfb99a"/>
 </svg>
</div>
""", unsafe_allow_html=True)

# Restore workspace controls after the Saved reports page removes their widgets.
st.session_state.setdefault("input_mode", st.session_state.get("saved_input_mode", "Paste reviews"))
st.session_state.setdefault("reporting_day", st.session_state.get("saved_reporting_day", date.today()))

workspace, companion = st.columns([2.05, 1], gap="large")
with workspace:
    with st.container(border=True, key="input_workspace"):
        st.subheader("What are your guests saying?")
        if IS_LOCAL:
            st.caption("Before you begin, remove names and personal details. Reviews are analysed on this computer.")
        else:
            st.caption(f"Before you begin, remove names and personal details. Reviews are sent to {HOST or 'an unconfirmed location'}; check the details before using personal information.")

        reporting_day = st.date_input(
            "Reporting week — choose any day", key="reporting_day", persist_state="session",
            format="DD/MM/YYYY", width=250, disabled=busy,
        )
        if reporting_day:
            week_start, week_end = reporting_week(reporting_day)
            week_label = f"{week_start:%d %b %Y} – {week_end:%d %b %Y}"
            st.caption(f"Monday–Sunday: {week_label}. Include only reviews from this week. The period is selected by you; review dates aren’t automatically checked or filtered.")
        else:
            st.warning("Choose a day in the reporting week to enable analysis.")

        mode = st.radio("Review input", ["Paste reviews", "Upload CSV"], key="input_mode", horizontal=True, label_visibility="collapsed", disabled=busy, persist_state="session")
        if mode == "Paste reviews":
            if "_review_text" not in st.session_state:
                st.session_state._review_text = st.session_state.saved_review_text
            text = st.text_area(
                "One review per line", key="_review_text", on_change=save_text, height=150,
                placeholder="The staff were friendly, but the coffee was cold.\nLe service était agréable, mais nous avons attendu longtemps.",
                max_chars=MAX_REVIEWS * (MAX_REVIEW_LENGTH + 1),
                disabled=busy, persist_state="session",
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
            start_analysis = st.button("Find my next improvements", type="primary", disabled=not reviews or not reporting_day or is_busy() or preparing_ai, width="stretch")
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
        st.markdown('<div class="rw-section-label">YOUR REPORT BRIEF</div>', unsafe_allow_html=True)
        st.markdown("### One week. A clearer focus.")
        if reporting_day:
            st.write(f"**{week_label}**")
        if reviews:
            st.markdown(f'<div class="rw-ready-count">{len(reviews)}<span>reviews selected</span></div>', unsafe_allow_html=True)
        else:
            st.caption("Your review count appears here once input is ready.")
        st.markdown('<div class="rw-mini-rule"></div>', unsafe_allow_html=True)
        st.write("**01 · Understand the feedback**")
        st.caption("Find praise and recurring problems in the original words of your guests.")
        st.write("**02 · Check what supports it**")
        st.caption("See complaint counts and the reviews behind each finding.")
        st.write("**03 · Keep your weekly report**")
        st.caption("Save a genuine analysis and reopen it for your presentation without rerunning AI.")
    if st.session_state.saved_review_text or st.session_state.saved_csv:
        st.button("Start over", on_click=clear_workspace, width="stretch", disabled=busy)
    with st.expander("Local AI controls"):
        st.caption("Up to four inference threads, scaled to this computer; short groups use a 2,048-token context. A local model still needs RAM and processing time.")
        if st.button("Release AI memory", disabled=is_busy(), width="stretch", help="Unload the model; new input will need to load it again."):
            try:
                with local_client() as client:
                    client.generate(model=MODEL, prompt="", keep_alive=0)
                st.success("Asked Ollama to unload the model. Your report is kept.")
            except Exception:
                st.warning("Could not release the model. Quit Ollama from the Windows system tray when finished.")

st.session_state.saved_input_mode = mode
st.session_state.saved_reporting_day = reporting_day


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
