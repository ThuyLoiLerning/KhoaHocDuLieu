"""
Streamlit scraper UI — crawl job data, view, and stats.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import re
from io import StringIO
from typing import Dict, Optional, List, Any

from src.data.collector import run_all_scrapers
from src.data.data_manager import JobDataManager

sns.set_theme(style="whitegrid")

st.set_page_config(page_title="Job Scraper UI", layout="wide")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "crawl_results" not in st.session_state:
    st.session_state.crawl_results = None
if "crawl_log" not in st.session_state:
    st.session_state.crawl_log = ""
if "crawl_complete" not in st.session_state:
    st.session_state.crawl_complete = False


# ---------------------------------------------------------------------------
# Cached helpers
# ---------------------------------------------------------------------------
@st.cache_data
def convert_results(results: Dict[str, Any]):
    """Convert raw results dict into three DataFrames."""
    jobs = pd.DataFrame(results["jobs"])
    skills = pd.DataFrame(results["skills"])
    companies = pd.DataFrame(results["companies"])
    if "skills_raw" in jobs.columns:
        jobs["skills_raw"] = jobs["skills_raw"].apply(
            lambda x: x if isinstance(x, list) else []
        )
    return jobs, skills, companies


def extract_salary(row: "pd.Series") -> Optional[float]:
    """Parse a numeric salary value from a job row.

    Fallback data provides 'salary_min'; real scraper data has 'salary_raw'
    as a human-readable string like "20-30 triệu".
    """
    val: Optional[float] = None
    if "salary_min" in row and pd.notna(row.get("salary_min")):
        val = float(row["salary_min"])
    elif row.get("salary_raw") and isinstance(row["salary_raw"], str) and row["salary_raw"].strip():
        nums = re.findall(r"(\d+[\.,]?\d*)", row["salary_raw"])
        if nums:
            val = float(nums[0].replace(",", "."))
    if val is not None and 5 < val < 200:
        return val
    return None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Configuration")
    keywords = st.multiselect(
        "Keywords",
        ["python", "java", "javascript", "react", "data", "devops"],
        default=["python", "java"],
    )
    max_pages = st.slider("Max pages per site", 1, 5, 1)
    min_jobs = st.slider("Min total jobs", 500, 5000, 1000, step=100)
    use_fallback = st.checkbox("Auto-generate fallback data", value=True,
                               help="If ON: generates synthetic data when real crawl is insufficient. "
                                    "If OFF: returns only real crawled data (may be 0).")

    st.divider()
    st.caption("**Quick debug — test single site**")
    col1, col2 = st.columns(2)
    with col1:
        test_kw = st.text_input("Keyword", value="python", key="test_kw")
    with col2:
        test_site = st.selectbox("Site", ["itviec", "vietnamworks", "topdev", "careerbuilder"], key="test_site")
    if st.button("Test single site", type="secondary", use_container_width=True):
        with st.spinner(f"Testing {test_site} with keyword '{test_kw}'..."):
            import importlib
            mod = __import__("src.data.collector", fromlist=["scrape_" + test_site])
            scraper_fn = getattr(mod, "scrape_" + test_site)
            try:
                test_jobs = scraper_fn(keyword=test_kw, max_pages=1)
                if test_jobs:
                    st.success(f"✅ {test_site}: {len(test_jobs)} jobs scraped!")
                    for j in test_jobs[:3]:
                        st.write(f"- {j.get('job_title','?')} @ {j.get('company_name','?')}")
                else:
                    st.warning(f"❌ {test_site}: 0 jobs returned")
            except Exception as e:
                st.error(f"❌ {test_site}: {e}")

    dm = JobDataManager()
    st.caption(f"Data directory: `{dm.raw_dir}`")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Crawl", "View Data", "Stats"])

# ========================== TAB 1: CRAWL ==========================
with tab1:
    st.header("Crawl")
    st.markdown("Run scrapers against Vietnamese job portals.")

    meta = st.columns(3)
    meta[0].metric("Keywords", len(keywords))
    meta[1].metric("Pages / site", max_pages)
    meta[2].metric("Target jobs", min_jobs)

    if st.button("Start Crawling", type="primary", use_container_width=True):
        # Capture logs into a string buffer
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        ))
        logging.getLogger().addHandler(handler)

        try:
            with st.status("Crawling ...", expanded=True) as status:
                st.write(
                    "Scraping live sites (itviec, vietnamworks, topdev, careerbuilder). "
                    "Fallback data is generated automatically when real data is insufficient."
                )
                results = run_all_scrapers(
                    keywords=keywords if keywords else None,
                    max_pages_per_site=max_pages,
                    min_total_jobs=min_jobs,
                    use_fallback=use_fallback,
                )

            n_jobs = len(results["jobs"])
            n_skills = len(results["skills"])
            n_companies = len(results["companies"])
            fallback_count = sum(
                1 for j in results["jobs"] if j.get("source_site") == "fallback"
            )

            st.session_state.crawl_results = results
            st.session_state.crawl_complete = True

            cols = st.columns(4)
            cols[0].metric("Jobs", f"{n_jobs:,}")
            cols[1].metric("Skills", f"{n_skills:,}")
            cols[2].metric("Companies", f"{n_companies:,}")
            real_count = n_jobs - fallback_count
            cols[3].metric("Real (live)", f"{real_count:,}")

            if fallback_count > 0:
                pct = 100.0 * fallback_count / n_jobs if n_jobs else 0
                st.warning(
                    f"**{fallback_count:,} / {n_jobs:,} jobs ({pct:.0f}%) are fallback "
                    "(simulated) data.** "
                    "Live scrapers were blocked or returned too few results."
                )
            else:
                st.success("All data collected from live sites.")

            # Source breakdown
            src_counts = pd.Series([j.get("source_site","?") for j in results["jobs"]]).value_counts()
            st.write("**Source breakdown:**")
            for src, cnt in src_counts.items():
                real_tag = " 🟢" if src != "fallback" else " 🔴 simulated"
                st.write(f"- {src}: **{cnt}** jobs{real_tag}")

        except Exception as exc:
            st.error(f"Crawl failed: {exc}")
        finally:
            handler.close()
            logging.getLogger().removeHandler(handler)
            st.session_state.crawl_log = log_stream.getvalue()

    if st.session_state.crawl_log:
        with st.expander("Crawl Log", expanded=False):
            st.code(st.session_state.crawl_log)

    if st.session_state.crawl_complete and st.session_state.crawl_results is None:
        st.info("No data loaded yet. Run a crawl above.")

# ========================== TAB 2: VIEW DATA ==========================
with tab2:
    st.header("View Data")

    if st.session_state.crawl_results is None:
        st.info("No data yet. Run a crawl first.")
    else:
        jobs_df, skills_df, companies_df = convert_results(
            st.session_state.crawl_results
        )

        # Filters
        cf1, cf2 = st.columns([1, 2])
        with cf1:
            src_col = "source_site" if "source_site" in jobs_df.columns else "site"
            if src_col not in jobs_df.columns:
                jobs_df[src_col] = "unknown"
            sources = ["All"] + sorted(jobs_df[src_col].unique().tolist())
            src_filter = st.selectbox("Source site", sources)
        with cf2:
            search_q = st.text_input("Search job title", placeholder="e.g. developer")

        df = jobs_df.copy()
        if src_filter != "All":
            df = df[df[src_col] == src_filter]
        if search_q:
            df = df[df["job_title"].str.contains(search_q, case=False, na=False)]

        # Display a clean subset of columns
        display_cols = [
            c
            for c in (
                "job_title",
                "company_name",
                "city",
                "salary_raw",
                src_col,
                "remote_option",
            )
            if c in df.columns
        ]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "Download CSV",
            csv_bytes,
            "jobs.csv",
            "text/csv",
            key="dl_csv",
        )

        # Expandable row details
        st.subheader("Row Details")
        if not df.empty:
            sel_title = st.selectbox("Select a job", df["job_title"].tolist())
            row = df[df["job_title"] == sel_title].iloc[0]
            with st.expander(f"{row['job_title']}", expanded=True):
                ca, cb = st.columns(2)
                with ca:
                    st.markdown(f"**Company:** {row['company_name']}")
                    st.markdown(f"**City:** {row.get('city', '—')}")
                    st.markdown(f"**Source:** {row.get(src_col, '—')}")
                    st.markdown(f"**URL:** {row.get('source_url', '—')}")
                with cb:
                    st.markdown(f"**Salary:** {row.get('salary_raw', '—')}")
                    st.markdown(f"**Remote:** {row.get('remote_option', '—')}")
                    st.markdown(f"**Posted:** {row.get('posted_date_raw', '—')}")
                skills_raw = row.get("skills_raw", [])
                if skills_raw and isinstance(skills_raw, list):
                    st.markdown("**Skills:** " + ", ".join(skills_raw))
                else:
                    st.markdown("**Skills:** _(none extracted)_")
        else:
            st.info("No matching records.")

# ========================== TAB 3: STATS ==========================
with tab3:
    st.header("Stats")

    if st.session_state.crawl_results is None:
        st.info("No data yet. Run a crawl first.")
    else:
        jobs_df, skills_df, companies_df = convert_results(
            st.session_state.crawl_results
        )

        # --- Top 20 skills ---
        st.subheader("Top 20 Skills")
        if not skills_df.empty:
            top20 = (
                skills_df.drop_duplicates(subset=["job_id", "skill_name"])
                .groupby("skill_name")
                .size()
                .sort_values(ascending=False)
                .head(20)
            )
            if not top20.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                top20.plot(kind="barh", ax=ax)
                ax.set_xlabel("Jobs")
                ax.set_title("Top 20 Skills")
                sns.despine()
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("No skills data to chart.")

        # --- City distribution ---
        st.subheader("City Distribution")
        city_col = "city" if "city" in jobs_df.columns else "location"
        if city_col not in jobs_df.columns:
            jobs_df[city_col] = "Unknown"
        city_counts = jobs_df[city_col].value_counts()
        if not city_counts.empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.pie(
                city_counts.values,
                labels=city_counts.index,
                autopct="%1.1f%%",
                startangle=90,
            )
            ax.set_title("Jobs by City")
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("No city data available.")

        # --- Source distribution ---
        st.subheader("Source Distribution")
        src_counts = jobs_df[src_col].value_counts()
        if not src_counts.empty:
            st.bar_chart(src_counts)
        else:
            st.info("No source data available.")

        # --- Salary distribution (histogram) ---
        st.subheader("Salary Distribution")
        salaries = []
        for _, row in jobs_df.iterrows():
            s = extract_salary(row)
            if s is not None:
                salaries.append(s)
        if salaries:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.hist(salaries, bins=20, edgecolor="white", color="steelblue")
            ax.set_xlabel("Salary (million VND / month)")
            ax.set_ylabel("Jobs")
            ax.set_title("Salary Distribution")
            sns.despine()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("No salary data available.")

    # end of stats tab
