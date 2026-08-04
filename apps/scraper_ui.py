"""Streamlit scraper UI — crawl job data, view, config & test."""
import sys, os, warnings, json, tempfile, threading, time, logging, re
from io import StringIO
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
warnings.filterwarnings("ignore")
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd

from src.data.collector import run_all_scrapers
from src.data.data_manager import JobDataManager
from src.data.auth_manager import AuthManager

st.set_page_config(page_title="Job Scraper", layout="wide")

# === Const: temp file paths ===
_TMP = tempfile.gettempdir()
_PROGRESS = os.path.join(_TMP, "scraper_progress.json")
_LOG = os.path.join(_TMP, "scraper_log.txt")
_RESULTS = os.path.join(_TMP, "scraper_results.json")
_PID = os.path.join(_TMP, "scraper_crawling.pid")

# === Session state ===
for k in ["crawl_results","crawl_log","crawl_complete","crawling","crawl_error"]:
    if k not in st.session_state:
        st.session_state[k] = None if k != "crawling" else False

# === Temp file helpers ===
def _write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except: pass

def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return default

def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except: return []

def _clear_file(path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
    except: pass

# === Data helpers ===
@st.cache_data
def convert_results(results):
    jobs = pd.DataFrame(results["jobs"])
    if "skills_raw" in jobs.columns:
        jobs["skills_raw"] = jobs["skills_raw"].apply(lambda x: x if isinstance(x, list) else [])
    return jobs, pd.DataFrame(results.get("skills", [])), pd.DataFrame(results.get("companies", []))

def _restore_from_parquet():
    try:
        proc_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
        files = [f for f in os.listdir(proc_dir) if f.endswith(".parquet")]
        if not files: return None
        latest = max(files, key=lambda f: os.path.getmtime(os.path.join(proc_dir, f)))
        _df = pd.read_parquet(os.path.join(proc_dir, latest))
        return {"jobs": _df.to_dict("records"), "skills": [], "companies": []}
    except: return None

def _format_salary(row):
    """Extract numeric salary from row."""
    if "salary_min" in row and pd.notna(row.get("salary_min")):
        return float(row["salary_min"])
    raw = row.get("salary_raw", "")
    if isinstance(raw, str) and raw.strip():
        nums = re.findall(r"(\d+[\.,]?\d*)", raw.replace(",", ""))
        if nums:
            val = float(nums[0].replace(",", ""))
            if 5 < val < 200: return val
    return None

# === Sidebar ===
with st.sidebar:
    if st.session_state.crawling:
        st.warning("Crawling in progress...")
        p = _read_json(_PROGRESS, {})
        if p: st.caption(f"{p.get('site','?')} | kw: {p.get('keyword','?')} | jobs: {p.get('total_jobs',0)}")

    st.title("Crawl Config")
    all_kw = ["python","java","javascript","typescript","react","angular","vue","nodejs",
              "frontend","backend","fullstack","mobile","android","ios","flutter","php","ruby",
              "golang","rust","swift","kotlin","data","data engineer","data analyst","data scientist",
              "machine learning","ai","deep learning","big data","sql","database","mongodb",
              "devops","cloud","aws","azure","gcp","docker","kubernetes","sre","security",
              "cybersecurity","network","tester","qa","test automation","game","unity","embedded","iot",
              "product manager","project manager","tech lead","software architect",
              "IT phan mem","CNTT Phan mem","lap trinh vien","ky su phan mem"]
    keywords = st.multiselect("Keywords", all_kw, default=all_kw, disabled=st.session_state.crawling)
    max_pages = st.slider("Max pages", 1, 10, 3, disabled=st.session_state.crawling)
    min_jobs = st.slider("Min total jobs", 100, 5000, 1000, step=100, disabled=st.session_state.crawling)
    use_fallback = st.checkbox("Auto fallback", value=False, disabled=st.session_state.crawling)

# === Tabs ===
tab1, tab2, tab3, tab4 = st.tabs(["Crawl", "View Data", "Config & Test", "Login"])

# ===================== TAB 1: CRAWL =====================
with tab1:
    st.header("Crawl")

    # Read crawling state from PID file
    _pid_state = _read_json(_PID, {})
    _is_crawling = _pid_state.get("crawling", False)
    if _is_crawling != st.session_state.crawling:
        st.session_state.crawling = _is_crawling

    st_autorefresh(interval=3000, key="refresh")

    # === URL list management ===
    st.subheader("Sites to crawl")
    from src.config.method_handlers import suggest_url_pattern

    if "crawl_urls" not in st.session_state:
        from src.config.scraper_config import SITE_CONFIGS
        st.session_state.crawl_urls = {s["name"]: {"url": s.get("search_url",""), "enabled": True}
                                        for s in SITE_CONFIGS if s.get("search_url")}

    for _uname in list(st.session_state.crawl_urls.keys()):
        _uinfo = st.session_state.crawl_urls[_uname]
        c1, c2, c3 = st.columns([2, 4, 1])
        with c1:
            st.checkbox(_uname, value=_uinfo.get("enabled",True), key=f"url_{_uname}",
                        on_change=lambda n=_uname: st.session_state.crawl_urls[n].update({"enabled": not st.session_state.crawl_urls[n].get("enabled",True)}),
                        disabled=_is_crawling)
        with c2:
            st.code(_uinfo["url"][:70], language="")
        with c3:
            if st.button("✕", key=f"rm_{_uname}", disabled=_is_crawling):
                del st.session_state.crawl_urls[_uname]
                st.rerun()

    with st.expander("+ Add URL", expanded=False):
        c1, c2 = st.columns([3,1])
        with c1:
            new_url = st.text_input("URL", key="nu", placeholder="https://example.com/viec-lam?q={keyword}&page={page}", disabled=_is_crawling)
        with c2:
            new_name = st.text_input("Name", key="nn", placeholder="my_site", disabled=_is_crawling)
        if new_url and "{keyword}" not in new_url and "{page}" not in new_url:
            suggested = suggest_url_pattern(new_url)
            if suggested != new_url:
                st.info(f"Gợi ý: `{suggested}`")
                if st.button("Use pattern", key="use_sug"):
                    st.session_state.crawl_urls[new_name or f"url_{len(st.session_state.crawl_urls)}"] = {"url": suggested, "enabled": True}
                    st.rerun()
        if st.button("Add", disabled=not new_url or _is_crawling):
            st.session_state.crawl_urls[new_name or f"url_{len(st.session_state.crawl_urls)}"] = {"url": new_url, "enabled": True}
            st.rerun()
    st.divider()

    if _is_crawling:
        st.info("Crawling in progress... auto-refresh every 3s.")
        for line in _read_file(_LOG)[-12:]:
            c = line.strip()
            if not c: continue
            if "❌" in c: st.error(c)
            elif "✅" in c: st.success(c)
            else: st.info(c)

    if st.session_state.crawl_error:
        st.error(f"Crawl failed: {st.session_state.crawl_error}")

    if _is_crawling:
        if st.button("Stop & Clear", type="secondary", use_container_width=True):
            _write_json(_PID, {"crawling": False})
            _clear_file(_LOG)
            _clear_file(os.path.join(_TMP, "scraper_data.pkl"))
            _write_json(_RESULTS, {})
            _write_json(_PROGRESS, {"site":"cancelled","keyword":"","total_jobs":0})
            st.session_state.crawling = False
            st.session_state.crawl_results = None
            st.session_state.crawl_log = ""
            st.rerun()

    meta = st.columns(3)
    meta[0].metric("Keywords", len(keywords))
    meta[1].metric("Pages", max_pages)
    meta[2].metric("Target", min_jobs)

    if st.button("Start Crawling", type="primary", use_container_width=True, disabled=st.session_state.crawling):
        st.session_state.crawling = True
        st.session_state.crawl_results = None
        st.session_state.crawl_complete = False
        st.session_state.crawl_error = None
        _clear_file(_LOG)
        _clear_file(os.path.join(_TMP, "scraper_data.pkl"))
        _write_json(_RESULTS, {})
        _write_json(_PID, {"crawling": True})
        _write_json(_PROGRESS, {"site":"preparing...","keyword":"","total_jobs":0})

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
        logging.getLogger().addHandler(handler)

        def _run():
            try:
                results = run_all_scrapers(
                    keywords=keywords if keywords else None,
                    max_pages_per_site=max_pages,
                    min_total_jobs=min_jobs,
                    use_fallback=use_fallback,
                    progress_file=_PROGRESS,
                )
                # Save summary
                summary = {"n_jobs": len(results.get("jobs",[])),"n_skills": len(results.get("skills",[])),"n_companies": len(results.get("companies",[])),"src_counts":{}}
                for j in results.get("jobs",[]):
                    s = j.get("source_site","?")
                    summary["src_counts"][s] = summary["src_counts"].get(s,0) + 1
                # Merge with existing: dedup by job_id + posted + expired
                import pickle, datetime as _dt
                try:
                    existing = _restore_from_parquet()
                    if existing and existing.get("jobs"):
                        seen = {}
                        for j in existing["jobs"]:
                            k = f"{j.get('job_id','')}|{j.get('posted_at','') or j.get('posted_date_raw','')}|{j.get('expired_at','') or j.get('resume_apply_expired','')}"
                            seen[k] = j
                        new_jobs = []
                        for j in results.get("jobs",[]):
                            k = f"{j.get('job_id','')}|{j.get('posted_at','') or j.get('posted_date_raw','')}|{j.get('expired_at','') or j.get('resume_apply_expired','')}"
                            if k not in seen:
                                new_jobs.append(j)
                                seen[k] = j
                        if new_jobs:
                            results["jobs"] = existing["jobs"] + new_jobs
                            summary["n_jobs"] = len(results["jobs"])
                            summary["n_new"] = len(new_jobs)
                except: pass
                # Save crawl history
                try:
                    hist_dir = os.path.join(os.path.dirname(__file__),"..","logs","crawl_history")
                    os.makedirs(hist_dir, exist_ok=True)
                    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(os.path.join(hist_dir,f"crawl_{ts}.json"),"w",encoding="utf-8") as f:
                        json.dump({"timestamp":ts,"n_jobs":summary.get("n_jobs",0),"n_new":summary.get("n_new",0),"src_counts":summary["src_counts"],"keywords":keywords},f,ensure_ascii=False)
                except: pass
                _write_json(_RESULTS, summary)
                _write_json(_PROGRESS, {"site":"done","keyword":"","total_jobs":len(results.get("jobs",[]))})
                with open(os.path.join(_TMP, "scraper_data.pkl"), "wb") as f:
                    pickle.dump(results, f)
                # Save merged data (includes old data) to parquet
                try:
                    from src.data.data_manager import JobDataManager as _DM
                    from src.domain.job_posting import JobPosting as _JP
                    from src.domain.skill import Skill as _SK
                    from src.domain.company import Company as _CO
                    import hashlib as _hl
                    _dm = _DM()
                    _jp = []
                    for j in results.get("jobs",[]):
                        if "company_id" not in j and "company_name" in j:
                            j["company_id"] = f"comp_{_hl.md5(j['company_name'].encode()).hexdigest()[:8]}"
                        try: _jp.append(_JP.from_dict(j))
                        except: pass
                    _jdf = pd.DataFrame([j.to_dict() if hasattr(j,'to_dict') else j for j in _jp])
                    if _jdf.empty: _jdf = pd.DataFrame(results.get("jobs",[]))
                    _sdf = pd.DataFrame([_SK(**s) for s in results.get("skills",[])])
                    _cdf = pd.DataFrame([_CO(**c) for c in results.get("companies",[])])
                    if "salary_raw" in _jdf.columns:
                        from src.data.salary_parser import SalaryParser as _SP
                        _jdf = _SP().parse_column(_jdf, "salary_raw")
                    if not _sdf.empty and "job_id" in _sdf.columns and "skill_name" in _sdf.columns:
                        _sk_agg = _sdf.groupby("job_id").agg({"skill_name":list,"skill_group":list,"required_level":list,"original_name":list}).reset_index()
                        _sk_agg.columns = ["job_id","skills","skill_groups","skill_levels","skill_originals"]
                        if "skills" in _jdf.columns: _jdf.drop(columns=["skills","skill_groups","skill_levels","skill_originals"],inplace=True,errors="ignore")
                        _jdf = _jdf.merge(_sk_agg, on="job_id", how="left")
                    if "experience_years" in _jdf.columns and "job_title" in _jdf.columns:
                        _jdf["experience_years_parsed"] = _jdf["experience_years"]
                        _mask = _jdf["experience_years_parsed"].isna()
                        if _mask.any():
                            _tl = _jdf.loc[_mask, "job_title"].str.lower().fillna("")
                            _lm = {"intern":0.5,"fresh":0.5,"junior":1.5,"jr":1.5,"associate":2.0,"middle":3.5,"mid":3.5,"senior":6.0,"sr":6.0,"expert":6.0,"lead":7.0,"principal":8.0,"manager":6.0,"head":8.0,"director":10.0,"architect":9.0,"cto":12.0}
                            for kw,yr in _lm.items():
                                _m2 = _tl.str.contains(kw,na=False,regex=False)
                                if _m2.any(): _jdf.loc[_mask & _m2,"experience_years_parsed"]=yr; _mask=_jdf["experience_years_parsed"].isna()
                    from src.cleaning.experience_normalizer import ExperienceNormalizer as _EX
                    _jdf["experience_bin"] = _jdf.get("experience_years_parsed",_jdf.get("experience_years")).apply(lambda x: _EX().bin_experience(x) if pd.notna(x) else "Not specified")
                    _c = _dm.merge_datasets(_jdf, _sdf, _cdf)
                    _dm.save_processed(_c, "combined")
                    _c.to_csv("data/processed/jobs_clean.csv",index=False,encoding="utf-8-sig")
                    _sdf.to_csv("data/processed/skills_clean.csv",index=False,encoding="utf-8-sig")
                    _cdf.to_csv("data/processed/companies_clean.csv",index=False,encoding="utf-8-sig")
                    _c.to_csv("data/processed/combined.csv",index=False,encoding="utf-8-sig")
                    _sdf.to_csv("data/processed/skills_clean.csv",index=False,encoding="utf-8-sig")
                    _cdf.to_csv("data/processed/companies_clean.csv",index=False,encoding="utf-8-sig")
                    _c.to_csv("data/processed/combined.csv",index=False,encoding="utf-8-sig")
                except Exception as _e: pass
            except Exception as exc:
                _write_json(_PROGRESS, {"site":"error","keyword":"","total_jobs":0})
                st.session_state.crawl_error = str(exc)
            finally:
                handler.close()
                logging.getLogger().removeHandler(handler)
                st.session_state.crawl_log = log_stream.getvalue()
                st.session_state.crawling = False
                # Write log to file for live display
                _clear_file(_LOG)
                with open(_LOG, "a", encoding="utf-8") as f:
                    f.write(st.session_state.crawl_log)
                _write_json(_PID, {"crawling": False})

        threading.Thread(target=_run, daemon=True).start()
        st.rerun()

    # Show results from summary file
    r_summary = _read_json(_RESULTS)
    if r_summary and not _is_crawling:
        n = r_summary.get("n_jobs",0)
        src = r_summary.get("src_counts",{})
        fb = src.get("fallback",0)
        cols = st.columns(4)
        cols[0].metric("Jobs", f"{n:,}")
        cols[1].metric("Skills", r_summary.get("n_skills",0))
        cols[2].metric("Companies", r_summary.get("n_companies",0))
        cols[3].metric("Real", f"{n-fb:,}")
        if fb:
            st.warning(f"{fb}/{n} jobs are fallback (simulated)")
        else:
            st.success("All data from live sources")
        for s, c in sorted(src.items()):
            tag = " LIVE" if s != "fallback" else " FALLBACK"
            st.write(f"- {s}: {c}{tag}")

    if st.session_state.crawl_log and not _is_crawling:
        with st.expander("Log"):
            st.code(st.session_state.crawl_log)

# ===================== TAB 2: VIEW DATA =====================
with tab2:
    st.header("View Data")

    # Restore from pickle if session state is empty
    if st.session_state.crawl_results is None:
        pkl = os.path.join(_TMP, "scraper_data.pkl")
        if os.path.exists(pkl):
            try:
                import pickle
                with open(pkl, "rb") as f:
                    st.session_state.crawl_results = pickle.load(f)
            except: pass

    if st.session_state.crawl_results is None:
        st.session_state.crawl_results = _restore_from_parquet()

    if st.session_state.crawl_results is None:
        st.info("Run a crawl first.")
    else:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("Clear All Data", type="secondary", use_container_width=True):
                import os as _os
                for d in ["data/processed","data/raw","logs"]:
                    for f in _os.listdir(d):
                        fp = _os.path.join(d, f)
                        try:
                            if _os.path.isfile(fp): _os.remove(fp)
                        except: pass
                st.session_state.crawl_results = None
                _clear_file(os.path.join(_TMP, "scraper_data.pkl"))
                _write_json(_RESULTS, {})
                st.rerun()

        jobs_df, _, _ = convert_results(st.session_state.crawl_results)
        src_col = "source_site" if "source_site" in jobs_df.columns else "site"
        if src_col not in jobs_df.columns:
            jobs_df[src_col] = "unknown"

        c1, c2 = st.columns([1,2])
        with c1:
            sources = ["All"] + sorted(jobs_df[src_col].unique().tolist())
            src_filter = st.selectbox("Source", sources, key="vd_src")
        with c2:
            search = st.text_input("Search title", placeholder="e.g. developer", key="vd_search")

        df = jobs_df.copy()
        if src_filter != "All":
            df = df[df[src_col] == src_filter]
        if search:
            df = df[df["job_title"].str.contains(re.escape(search), case=False, na=False)]

        cols = [c for c in ["job_title","company_name","city","salary_raw",src_col,"remote_option"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
        st.download_button("Download CSV", df.to_csv(index=False, encoding="utf-8-sig"), "jobs.csv", "text/csv")

        if not df.empty:
            st.subheader("Detail")
            # Use iloc-based selection to handle duplicates
            titles = df["job_title"].tolist()
            sel_idx = st.selectbox("Select job", range(len(titles)),
                                   format_func=lambda i: f"{titles[i]} @ {df.iloc[i].get('company_name','')}",
                                   key="vd_detail")
            row = df.iloc[sel_idx]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Company:** {row.get('company_name','')}")
                st.markdown(f"**City:** {row.get('city','')}")
                st.markdown(f"**Source:** {row.get(src_col,'')}")
            with c2:
                st.markdown(f"**Salary:** {row.get('salary_raw','')}")
                st.markdown(f"**Remote:** {row.get('remote_option','')}")
                url = row.get("source_url","")
                st.markdown(f"**URL:** [{url}]({url})" if url else "**URL:** —")
            skills = row.get("skills_raw",[])
            st.markdown(f"**Skills:** {', '.join(skills) if isinstance(skills,list) and skills else '_(none)_'}")

# ===================== TAB 3: CONFIG & TEST =====================
with tab3:
    st.header("Config & Test")
    from src.config.scraper_config import save_test_results
    from src.config.method_handlers import auto_detect, AUTO_METHODS

    MH = dict(AUTO_METHODS)
    SITE_MAP = {s["name"]: s for s in __import__("src.config.scraper_config", fromlist=["SITE_CONFIGS"]).SITE_CONFIGS}

    # === AUTO DETECT ===
    st.subheader("Auto Detect", divider="orange")
    st.markdown("Nhập URL → tự động dò method phù hợp để lấy data.")
    ad_url = st.text_input("URL pattern (dùng {keyword}, {page})",
        value="https://example.com/viec-lam?q={keyword}&page={page}", key="ad_url",
        help="URL có chứa {keyword} và {page} làm placeholder")
    ad_pages = st.number_input("Pages", 1, 3, 1, key="ad_pages")
    # Keyword dùng chung từ sidebar Crawl config
    ad_kw = keywords[0] if keywords else "python"

    if "ad_results" not in st.session_state:
        st.session_state.ad_results = None

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Auto Detect", type="primary", use_container_width=True):
            with st.spinner("Dang do methods..."):
                st.session_state.ad_results = auto_detect(ad_url, ad_kw, ad_pages)
    with col2:
        if st.session_state.ad_results and st.button("Clear", use_container_width=True):
            st.session_state.ad_results = None
            st.rerun()

    if st.session_state.ad_results:
        results = st.session_state.ad_results
        ok_count = sum(1 for r in results if r["status"] == "OK")
        st.markdown(f"**Co data:** {ok_count}/{len(results)} methods")

        first_ok = next((r for r in results if r["status"] == "OK"), None)
        if first_ok:
            st.success(f"✅ **{first_ok['method']}** — {first_ok['n_jobs']} jobs")

        # Summary table
        tbl = []
        for r in results:
            icon = {"OK": "✅", "no data": "⏭️", "error": "❌"}.get(r["status"], "❓")
            s = ""
            if r["jobs"]:
                j = r["jobs"][0]
                s = f"{str(j.get('job_title',''))[:40]} @ {str(j.get('company_name',''))[:20]}"
            tbl.append({"Method": r["method"], "Status": f"{icon} {r['status']}",
                       "Jobs": r["n_jobs"], "Sample": s, "Error": r["error"][:50]})
        st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)

        # Detail per method
        tabs = st.tabs([r["method"] for r in results])
        for ti, r in enumerate(results):
            with tabs[ti]:
                if r["jobs"]:
                    df = pd.DataFrame(r["jobs"])
                    cols = [c for c in ["job_title","company_name","city","salary_raw","source_url"] if c in df.columns]
                    st.dataframe(df[cols].head(10), use_container_width=True, hide_index=True)
                    st.download_button("Download", df.to_csv(index=False, encoding="utf-8-sig"),
                        f"auto_{r['method']}.csv", "text/csv", key=f"ad_dl_{ti}")
                else:
                    st.info(f"No data from {r['method']}")
                    if r["error"]:
                        st.caption(f"Error: {r['error']}")

# ===================== TAB 4: LOGIN =====================
with tab4:
    st.header("Đăng nhập & Session")
    st.caption("Đăng nhập thủ công để crawl data chi tiết (vd lương itviec ẩn sau login).")

    am = AuthManager()
    from src.config.scraper_config import SITE_CONFIGS
    site_names = [s["name"] for s in SITE_CONFIGS if s.get("enabled", True)]

    def _close_browser():
        pw_state = st.session_state.get("_pw")
        if pw_state:
            try:
                if pw_state.get("browser"):
                    pw_state["browser"].close()
                if pw_state.get("pw"):
                    pw_state["pw"].stop()
            except Exception:
                pass
            st.session_state["_pw"] = None

    # Trạng thái session hiện tại
    sessions = am.list_sessions()
    st.subheader("Session đã lưu")
    if sessions:
        for sname, sinfo in sessions.items():
            mt = time.strftime("%Y-%m-%d %H:%M", time.localtime(sinfo["mtime"]))
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{sname}** — lưu lúc {mt}")
            with c2:
                if st.button("Xóa", key=f"del_{sname}"):
                    am.delete_session(sname)
                    st.rerun()
    else:
        st.info("Chưa có session nào.")

    st.divider()
    st.subheader("Đăng nhập mới")
    sel_site = st.selectbox("Chọn site", site_names)
    login_url = st.text_input("URL đăng nhập", value="https://itviec.com/viec-lam-it" if sel_site == "itviec" else "")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mở browser đăng nhập", key="open_login"):
            _close_browser()
            pw = browser = None
            try:
                from src.data.playwright_crawler import PlaywrightCrawler
                pc = PlaywrightCrawler(auth_manager=am)
                # Reuse auth logic qua PlaywrightCrawler mở browser headless=False
                from playwright.sync_api import sync_playwright
                pw = sync_playwright().start()
                # Ưu tiên browser default (Edge/Chrome) — fallback chromium
                browser = None
                for channel in ["msedge", "chrome"]:
                    try:
                        browser = pw.chromium.launch(headless=False, channel=channel)
                        break
                    except Exception:
                        continue
                if browser is None:
                    browser = pw.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                page.goto(login_url or "https://itviec.com/viec-lam-it", timeout=60000)
                st.session_state["_pw"] = {"pw": pw, "browser": browser, "context": context, "page": page, "site": sel_site}
                st.success("Browser đã mở. Đăng nhập trong browser, rồi bấm 'Lưu session'.")
            except Exception as e:
                st.error(f"Lỗi mở browser: {e}")
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass
                if pw:
                    try:
                        pw.stop()
                    except Exception:
                        pass
    with col2:
        if st.button("Lưu session", key="save_session"):
            pw_state = st.session_state.get("_pw")
            if pw_state:
                try:
                    state = pw_state["context"].storage_state()
                    save_site = pw_state.get("site", sel_site)
                    am.save_storage_state(save_site, state)
                    _close_browser()
                    st.success(f"Đã lưu session {save_site}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi lưu: {e}")
                    _close_browser()
            else:
                st.warning("Chưa mở browser. Bấm 'Mở browser đăng nhập' trước.")

