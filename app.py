from __future__ import annotations

import json
import textwrap

import pandas as pd
import streamlit as st

from src.analyzer import ask_ai, summarize_workbook
from src.excel_loader import load_workbook
from src.requirement_generator import generate_requirement_candidates, refine_requirements_with_ai

st.set_page_config(page_title="HPE Serviceability & Supportability AI", page_icon="🟦", layout="wide")

st.markdown(
    textwrap.dedent(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

    :root {
        --ink: #1f2740;
        --teal: #00c2b8;
        --teal-deep: #0097d9;
        --blue: #2f6bff;
        --violet: #7b61ff;
        --coral: #ff8a5b;
        --gold: #ffcc4d;
        --surface: rgba(255,255,255,0.9);
        --panel: rgba(248, 251, 255, 0.92);
    }

    .stApp {
        font-family: 'Manrope', sans-serif;
        background:
            radial-gradient(circle at 12% 12%, rgba(47, 107, 255, 0.18), transparent 28%),
            radial-gradient(circle at 84% 6%, rgba(0, 194, 184, 0.22), transparent 26%),
            radial-gradient(circle at 88% 82%, rgba(255, 138, 91, 0.16), transparent 24%),
            linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
        color: var(--ink);
    }

    .top-ribbon {
        height: 12px;
        width: 100%;
        margin: -1rem 0 1.2rem 0;
        border-radius: 0 0 10px 10px;
        background: linear-gradient(90deg, var(--teal-deep), var(--teal), var(--blue), var(--violet));
    }

    .hero-card {
        background: var(--surface);
        border: 1px solid #e8eef7;
        border-radius: 18px;
        padding: 24px 26px;
        margin-bottom: 18px;
        box-shadow: 0 14px 35px rgba(27, 50, 89, 0.09);
        overflow: hidden;
        position: relative;
    }

    .hero-card:after {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(130deg, rgba(0, 194, 184, 0.08), rgba(47, 107, 255, 0.05), rgba(255, 138, 91, 0.06));
        pointer-events: none;
    }

    .hero-title {
        font-size: 3.35rem;
        line-height: 1.01;
        letter-spacing: 0.2px;
        font-weight: 800;
        margin: 0 0 10px 0;
    }

    .hero-sub {
        font-size: 1.08rem;
        color: #44506a;
        margin: 0;
    }

    .sub-badge {
        margin-top: 14px;
        display: inline-block;
        border: 1px solid #d7e5f7;
        border-radius: 999px;
        padding: 7px 14px;
        font-size: 0.87rem;
        color: #2f4468;
        background: linear-gradient(90deg, #f1fcff, #eef6ff);
    }

    .hero-grid {
        display: grid;
        grid-template-columns: 1.25fr 0.85fr;
        gap: 14px;
        margin-top: 18px;
    }

    .landing-grid {
        display: grid;
        grid-template-columns: 1.35fr 1fr;
        gap: 18px;
        margin: 10px 0 20px 0;
    }

    .landing-panel {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #e7eef8;
        border-radius: 20px;
        padding: 22px;
        box-shadow: 0 16px 40px rgba(27, 50, 89, 0.08);
        position: relative;
        overflow: hidden;
    }

    .landing-panel::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(0, 194, 184, 0.08), rgba(47, 107, 255, 0.06), rgba(255, 138, 91, 0.05));
        pointer-events: none;
    }

    .eyebrow {
        display: inline-block;
        font-size: 0.74rem;
        letter-spacing: 0.18em;
        font-weight: 800;
        color: #4370d9;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .landing-title {
        font-size: 3.15rem;
        line-height: 0.98;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0 0 12px 0;
    }

    .landing-sub {
        font-size: 1.03rem;
        color: #4c5871;
        max-width: 52rem;
        line-height: 1.5;
        margin: 0;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #fff;
        border: 1px solid #dbe7f7;
        border-radius: 999px;
        padding: 9px 14px;
        font-size: 0.85rem;
        color: #27415f;
    }

    .pill i {
        font-style: normal;
    }

    .icon-grid {
        display: grid;
        gap: 12px;
        grid-template-columns: 1fr;
    }

    .icon-card {
        border-radius: 18px;
        padding: 16px 16px 14px 16px;
        border: 1px solid rgba(255,255,255,0.85);
        box-shadow: 0 10px 20px rgba(27, 50, 89, 0.06);
        background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(246,251,255,0.98));
    }

    .icon-card .row {
        display: flex;
        gap: 12px;
        align-items: flex-start;
    }

    .icon-badge {
        width: 42px;
        height: 42px;
        border-radius: 14px;
        display: grid;
        place-items: center;
        font-size: 1.2rem;
        flex: 0 0 auto;
        color: #fff;
    }

    .icon-badge.blue { background: linear-gradient(135deg, var(--blue), #6a8cff); }
    .icon-badge.teal { background: linear-gradient(135deg, var(--teal), #64d7d0); }
    .icon-badge.coral { background: linear-gradient(135deg, var(--coral), #ffb27e); }

    .icon-card h4 {
        margin: 0 0 5px 0;
        font-size: 1rem;
        font-weight: 800;
    }

    .icon-card p {
        margin: 0;
        color: #54617c;
        line-height: 1.45;
        font-size: 0.93rem;
    }

    .metric-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 14px 0 18px 0;
    }

    .metric-tile {
        background: rgba(255,255,255,0.95);
        border: 1px solid #e3ebf7;
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: 0 10px 22px rgba(27, 50, 89, 0.05);
    }

    .metric-tile .label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #6a7690;
        margin-bottom: 6px;
        font-weight: 800;
    }

    .metric-tile .value {
        font-size: 1.2rem;
        font-weight: 800;
        color: #21304d;
    }

    .metric-tile.blue { border-top: 4px solid var(--blue); }
    .metric-tile.teal { border-top: 4px solid var(--teal); }
    .metric-tile.coral { border-top: 4px solid var(--coral); }

    .section-shell {
        background: rgba(255,255,255,0.82);
        border: 1px solid #e8eef7;
        border-radius: 18px;
        padding: 18px 18px 8px 18px;
        box-shadow: 0 10px 28px rgba(27, 50, 89, 0.06);
    }

    .section-header {
        font-size: 1.15rem;
        font-weight: 800;
        margin: 0 0 10px 0;
    }

    .summary-chip {
        display: inline-block;
        margin-top: 10px;
        margin-right: 8px;
        padding: 6px 12px;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(47,107,255,0.12), rgba(0,194,184,0.12));
        color: #244065;
        font-size: 0.84rem;
        border: 1px solid #dbe8fb;
    }

    .stButton > button {
        border-radius: 11px;
        border: 0;
        font-weight: 800;
        padding: 0.55rem 1rem;
        background: linear-gradient(120deg, var(--teal-deep), var(--teal), var(--blue));
        color: #ffffff;
        box-shadow: 0 10px 18px rgba(8, 198, 190, 0.22);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 20px rgba(8, 198, 190, 0.3);
    }

    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div,
    .stFileUploader section {
        border-radius: 12px !important;
        background: var(--panel) !important;
    }

    @media (max-width: 760px) {
        .landing-title { font-size: 2.05rem; }
        .landing-grid,
        .metric-strip { grid-template-columns: 1fr; }
    }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='top-ribbon'></div>",
    unsafe_allow_html=True,
)

st.caption("Build v2.1 - Requirement Studio enabled")

st.markdown(
    textwrap.dedent(
        """
        <div class="landing-grid">
            <div class="landing-panel">
                <div class="eyebrow">HPE INTERNAL ANALYSIS CONSOLE</div>
                <div class="landing-title">HPE Serviceability &amp; Supportability AI</div>
                <p class="landing-sub">HPE Services Standard serviceability and supportability analysis console for Excel, PDF, and PowerPoint.</p>
                <div class="pill-row">
                    <span class="pill"><i>✦</i> Designed for Delivery Readiness and cross-team decision support</span>
                    <span class="pill"><i>⚡</i> Fast file review</span>
                    <span class="pill"><i>🧠</i> AI-driven insights</span>
                </div>
            </div>
            <div class="icon-grid">
                <div class="icon-card">
                    <div class="row">
                        <div class="icon-badge blue">📄</div>
                        <div>
                            <h4>Upload</h4>
                            <p>Excel, PDF, PPTX, PPT, and CSV with a clean workflow.</p>
                        </div>
                    </div>
                </div>
                <div class="icon-card">
                    <div class="row">
                        <div class="icon-badge teal">🤖</div>
                        <div>
                            <h4>Analyze</h4>
                            <p>Ask natural-language questions and get findings, risks, and actions.</p>
                        </div>
                    </div>
                </div>
                <div class="icon-card">
                    <div class="row">
                        <div class="icon-badge coral">✅</div>
                        <div>
                            <h4>Share</h4>
                            <p>Leadership-ready summaries for review and decision support.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Upload Excel, CSV, PDF, or PowerPoint",
    accept_multiple_files=False,
)

allowed_ext = {"xlsx", "xlsm", "csv", "pdf", "pptx", "ppt"}

if not uploaded:
    st.info("Upload your workbook to start analysis.")
    st.markdown("### What appears after upload")
    guide_col1, guide_col2, guide_col3 = st.columns(3)
    with guide_col1:
        with st.container(border=True):
            st.markdown("#### Preview")
            st.write("Sheet-level preview plus workbook health checks.")
    with guide_col2:
        with st.container(border=True):
            st.markdown("#### Requirement Studio")
            st.write("Auto-generated S&S requirements with evidence, priority, and review status.")
    with guide_col3:
        with st.container(border=True):
            st.markdown("#### AI Analyst")
            st.write("Interactive Q&A and executive summary prompts over your uploaded content.")
    st.stop()

ext = uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
if ext not in allowed_ext:
    st.error("Unsupported file type. Please upload: xlsx, xlsm, csv, pdf, pptx, or ppt.")
    st.stop()

with st.spinner("Reading workbook..."):
    wb = load_workbook(uploaded.getvalue(), uploaded.name)

summary = summarize_workbook(wb.sheets)
requirements = refine_requirements_with_ai(generate_requirement_candidates(wb.sheets), summary)

sheet_names = list(wb.sheets.keys())

st.markdown(
    textwrap.dedent(
        """
        <div class="metric-strip">
            <div class="metric-tile blue"><div class="label">File</div><div class="value">Upload ready</div></div>
            <div class="metric-tile teal"><div class="label">Sheets</div><div class="value">Preview + health</div></div>
            <div class="metric-tile coral"><div class="label">Mode</div><div class="value">HPE review flow</div></div>
        </div>
        """
    ),
    unsafe_allow_html=True,
)

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
with metric_col1:
    st.metric("File", uploaded.name)
with metric_col2:
    st.metric("Sheets", len(sheet_names))
with metric_col3:
    st.metric("Type", uploaded.name.split(".")[-1].upper())
with metric_col4:
    st.metric("Draft Requirements", len(requirements))

preview_tab, requirements_tab, analyst_tab = st.tabs(["Preview", "Requirement Studio", "AI Analyst"])

with preview_tab:
    selected_sheet = st.selectbox("Select sheet preview", sheet_names)

    left, right = st.columns([1.2, 1.0])

    with left:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Sheet Preview</div>', unsafe_allow_html=True)
        st.dataframe(wb.sheets[selected_sheet], use_container_width=True, height=420)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Workbook Health</div>', unsafe_allow_html=True)
        st.json(summary, expanded=False)

        profile_blocks = [x for x in summary if isinstance(x, dict) and "workbook_profile" in x]
        if profile_blocks:
            st.success("Detected workbook profile: S&S Requirements Tool")
            profile = profile_blocks[0].get("profile", {})
            missing = profile.get("missing_sheets", [])
            if missing:
                st.warning(f"Missing expected sheets: {', '.join(missing)}")
            else:
                st.info("Expected sheets found: Summary, Lists, Product 1")
        st.markdown('</div>', unsafe_allow_html=True)

with requirements_tab:
    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Requirement Studio</div>', unsafe_allow_html=True)
    st.caption("Draft product-specific S&S requirements generated from workbook structure and evidence.")

    if requirements:
        requirements_df = pd.DataFrame(requirements)
        edited_df = st.data_editor(
            requirements_df,
            use_container_width=True,
            height=420,
            column_config={
                "review_status": st.column_config.SelectboxColumn(
                    "Review Status",
                    options=["Draft", "Needs Review", "Approved", "Rejected"],
                )
            },
            num_rows="fixed",
            key="requirements_editor",
        )

        export_col1, export_col2 = st.columns(2)
        with export_col1:
            st.download_button(
                label="Download Requirements CSV",
                data=edited_df.to_csv(index=False),
                file_name="ss_requirements_draft.csv",
                mime="text/csv",
            )
        with export_col2:
            st.download_button(
                label="Download Requirements JSON",
                data=edited_df.to_json(orient="records", indent=2),
                file_name="ss_requirements_draft.json",
                mime="application/json",
            )
    else:
        st.warning("No draft requirements could be generated from the current file.")

    st.markdown('</div>', unsafe_allow_html=True)

with analyst_tab:
    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">AI Analyst</div>', unsafe_allow_html=True)
    default_q = "Give me key findings, risks, and action items from this workbook."

    if "question" not in st.session_state:
        st.session_state.question = default_q

    quick_col1, quick_col2, quick_col3 = st.columns(3)
    with quick_col1:
        if st.button("Quick Analysis: Requirement Gaps"):
            st.session_state.question = (
                "Analyze Product 1 like an S&S requirements tracker. "
                "List likely requirement gaps, missing ownership/status, and immediate fixes."
            )
    with quick_col2:
        if st.button("Quick Analysis: Executive Summary"):
            st.session_state.question = (
                "Create an executive summary for leadership with top findings, risks, "
                "and next 5 actions."
            )
    with quick_col3:
        if st.button("Quick Analysis: Requirement Generator Review"):
            st.session_state.question = (
                "Review the generated S&S requirements, point out weak evidence, and suggest which items need human validation first."
            )

    question = st.text_area("Ask a question", value=st.session_state.question, height=110)
    st.session_state.question = question

    if st.button("Run AI Analysis", type="primary"):
        with st.spinner("Thinking..."):
            answer = ask_ai(question, summary)
        st.markdown("### Result")
        st.write(answer)

    st.markdown('<span class="summary-chip">Insight summary ready for sharing</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.download_button(
    label="Download summary JSON",
    data=json.dumps(summary, indent=2),
    file_name="workbook_summary.json",
    mime="application/json",
)
