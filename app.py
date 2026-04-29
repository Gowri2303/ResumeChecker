"""
Resume Checker - Streamlit Application
"""

import streamlit as st
from utils import extract_text_from_pdf
from model import analyze_resume
from job_description import JOB_TITLE, JOB_DESCRIPTION

MAX_FILES = 5

st.set_page_config(page_title="Resume Checker", layout="centered")

# ─── Styling ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
        background: #f8f9fb;
    }
    .block-container { max-width: 680px; padding-top: 2.5rem; }

    .app-title { font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 0.1rem; }
    .app-sub { font-size: 0.88rem; color: #64748b; margin-bottom: 1.5rem; }

    .result-box {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.8rem;
    }
    .result-name { font-size: 0.95rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem; }

    .tag-yes {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        background: #ecfdf5; color: #059669;
        border: 1px solid #a7f3d0;
        border-radius: 5px;
        font-weight: 600; font-size: 0.8rem;
        margin-bottom: 0.6rem;
    }
    .tag-no {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        background: #fef2f2; color: #dc2626;
        border: 1px solid #fecaca;
        border-radius: 5px;
        font-weight: 600; font-size: 0.8rem;
        margin-bottom: 0.6rem;
    }

    .reasons { margin: 0; padding-left: 1.1rem; color: #475569; font-size: 0.85rem; line-height: 1.65; }
    .reasons li { margin-bottom: 0.15rem; }

    /* hide file sizes in uploader */
    div[data-testid="stFileUploader"] small { display: none !important; }

    .stButton > button {
        background: #1e293b; color: #fff; border: none;
        border-radius: 7px; padding: 0.5rem 1.8rem;
        font-weight: 600; font-size: 0.88rem;
    }
    .stButton > button:hover { background: #334155; color: #fff; }

    .limit-msg { color: #64748b; font-size: 0.82rem; margin-top: 0.4rem; }

    hr { border-color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)


# ─── Header ───
st.markdown(f'<div class="app-title">Resume Checker</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-sub">Checking against the {JOB_TITLE} role</div>', unsafe_allow_html=True)

with st.expander("View Job Description"):
    st.write(JOB_DESCRIPTION)

st.divider()

# ─── Session state for collected files ───
if "collected_files" not in st.session_state:
    st.session_state.collected_files = []

# Show uploader only if under limit
file_count = len(st.session_state.collected_files)

if file_count < MAX_FILES:
    new_files = st.file_uploader(
        f"Upload resumes (PDF) — {file_count}/{MAX_FILES} added",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"uploader_{file_count}",
    )
    if new_files:
        remaining = MAX_FILES - file_count
        to_add = new_files[:remaining]
        st.session_state.collected_files.extend(to_add)
        st.rerun()
else:
    st.markdown(f'<div class="limit-msg">5 resumes added (limit reached)</div>', unsafe_allow_html=True)

# Show current files
if st.session_state.collected_files:
    names = [f.name for f in st.session_state.collected_files]
    for i, name in enumerate(names):
        st.text(f"  {i+1}. {name}")

    col1, col2 = st.columns([1, 1])
    with col1:
        analyze = st.button("Analyze Resumes")
    with col2:
        clear = st.button("Clear All")

    if clear:
        st.session_state.collected_files = []
        st.rerun()

    if analyze:
        st.divider()

        all_results = []
        with st.spinner("Analyzing..."):
            for f in st.session_state.collected_files:
                try:
                    text = extract_text_from_pdf(f)
                    if not text or len(text.strip()) < 50:
                        all_results.append({"name": f.name, "error": "Could not read this PDF."})
                    else:
                        result = analyze_resume(text)
                        all_results.append({"name": f.name, "error": None, "result": result})
                except Exception as e:
                    all_results.append({"name": f.name, "error": str(e)})

        for item in all_results:
            if item.get("error"):
                reasons_html = f'<li>{item["error"]}</li>'
                st.markdown(f'<div class="result-box"><div class="result-name">{item["name"]}</div><div class="tag-no">Error</div><ul class="reasons">{reasons_html}</ul></div>', unsafe_allow_html=True)
                continue

            r = item["result"]
            tag = "tag-yes" if r["is_shortlisted"] else "tag-no"
            label = "Shortlisted" if r["is_shortlisted"] else "Not Shortlisted"
            reasons_html = "".join(f"<li>{reason}</li>" for reason in r["reasons"])

            st.markdown(f'<div class="result-box"><div class="result-name">{item["name"]}</div><div class="{tag}">{label}</div><ul class="reasons">{reasons_html}</ul></div>', unsafe_allow_html=True)
