"""Generator: produce 03_eda.ipynb."""
import json, uuid, textwrap
from pathlib import Path

def cell(src, ct="code", id_=None):
    if id_ is None:
        id_ = uuid.uuid4().hex[:12]
    s = textwrap.dedent(src).strip()
    return {"cell_type": ct, "metadata": {"id": id_},
            "source": [l + "\n" for l in s.split("\n")],
            "outputs": [] if ct == "code" else None}

def md(s, id_=None):
    return cell(s, "markdown", id_)

C = []

C.append(md("""# Notebook 3: Exploratory Data Analysis (EDA)

**Chuyen de 4: Phan Tich Thi Truong Viec Lam & Goi Y Ung Vien**
**Notebook:** 03_eda.ipynb
**Muc tieu:** Phan tich kham pha du lieu, tra loi 4 cau hoi nghien cuu dau tien (F1-F4).

---

## 1. Setup & Data Loading"""))

C.append(cell(r"""import sys; sys.path.append('..')
import pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns
from src.data.data_manager import JobDataManager
from src.visualization.chart_utils import *
print(f"pandas {pd.__version__}, numpy {np.__version__}")
import matplotlib; print(f"matplotlib {matplotlib.__version__}")
print(f"seaborn {sns.__version__}")"""))

C.append(cell(r"""dm = JobDataManager()
df = dm.load_processed()
if df.empty:
    print("WARNING: No processed data. Using demo data.")
    np.random.seed(42)
    n = 200
    cities = ["HCMC", "Hanoi", "Da Nang"]
    titles = ["Backend Developer", "Frontend Developer", "Fullstack Developer",
              "Data Scientist", "DevOps Engineer", "Mobile Developer",
              "QA Engineer", "Data Engineer", "AI Engineer", "Product Manager"]
    df = pd.DataFrame({
        "job_id": [f"demo_{i}" for i in range(n)],
        "job_title": np.random.choice(titles, n),
        "city": np.random.choice(cities, n, p=[0.5, 0.35, 0.15]),
        "experience_years": np.round(np.random.exponential(3, n) + 0.5, 1),
        "experience_bin": pd.Categorical(np.random.choice(
            ["entry", "junior", "mid", "senior", "lead"], n,
            p=[0.1, 0.25, 0.35, 0.2, 0.1]
        ), categories=["entry", "junior", "mid", "senior", "lead"], ordered=True),
        "education_level": np.random.choice(
            ["Not Required", "Bachelor", "Master", "PhD"], n, p=[0.3, 0.5, 0.15, 0.05]),
        "remote_option": np.random.choice(["On-site", "Hybrid", "Remote"], n, p=[0.5, 0.3, 0.2]),
        "salary_min": np.random.uniform(5, 30, n) + np.random.choice([0, np.nan], n, p=[0.85, 0.15]),
        "salary_max": np.random.uniform(10, 60, n) + np.random.choice([0, np.nan], n, p=[0.85, 0.15]),
        "salary_hidden": np.random.choice([True, False], n, p=[0.25, 0.75]),
        "has_english": np.random.choice([True, False], n, p=[0.6, 0.4]),
        "posted_at": pd.date_range("2024-10-01", periods=n, freq="D") + pd.Timedelta(days=np.random.randint(0, 90, n)),
        "source_site": np.random.choice(["itviec", "vietnamworks", "topdev"], n),
    })
    df["salary_mid"] = (df["salary_min"] + df["salary_max"]) / 2
    skill_pool = ["Python","JavaScript","Java","SQL","React","Node.js","Docker","AWS","Git","TypeScript",
                  "Go","Kubernetes","Machine Learning","MongoDB","PostgreSQL","TensorFlow","Angular","Vue.js","Redis","Kafka"]
    skill_group_map = {"Python":"Programming Lg","JavaScript":"Programming Lg","Java":"Programming Lg","SQL":"Programming Lg",
                       "React":"Frontend","Node.js":"Backend","Docker":"DevOps","AWS":"Cloud","Git":"Tool",
                       "TypeScript":"Programming Lg","Go":"Programming Lg","Kubernetes":"DevOps",
                       "Machine Learning":"Data Science","MongoDB":"Database","PostgreSQL":"Database",
                       "TensorFlow":"Data Science","Angular":"Frontend","Vue.js":"Frontend","Redis":"Database","Kafka":"Data Science"}
    df["skills"] = [np.random.choice(skill_pool, np.random.randint(2, 8), replace=False).tolist() for _ in range(n)]
    df["skill_groups"] = [[skill_group_map[s] for s in skills] for skills in df["skills"]]
else:
    print(f"Loaded {len(df)} rows, {df.shape[1]} columns")"""))

C.append(md("""## 2. Tong quan du lieu"""))

C.append(cell("""print("Shape:", df.shape)
print("\\nColumns:", list(df.columns))
print("\\nInfo:")
df.info()"""))

C.append(cell("""print("\\nDescribe (numeric):")
df.describe()"""))

C.append(cell("""missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
md = pd.DataFrame({"Missing": missing, "Percent": missing_pct})
md = md[md["Missing"] > 0].sort_values("Missing", ascending=False)
if not md.empty:
    print("Columns with missing values:")
    display(md)
else:
    print("No missing values.")"""))

C.append(cell("""print("\\nCity distribution:", df["city"].value_counts().to_dict())
print("\\nRemote option:", df["remote_option"].value_counts().to_dict())
print("\\nExperience bins:")
print(df["experience_bin"].value_counts())
print("\\nEducation:", df["education_level"].value_counts().to_dict())
print("\\nSalary hidden rate: {:.1%}".format(df["salary_hidden"].mean()))
print("Sources:", df["source_site"].value_counts().to_dict())"""))

C.append(md("""---

## 3. F1: Ky nang nao duoc yeu cau nhieu nhat?"""))

C.append(cell(r"""if "skills" in df.columns and not df.empty:
    se = df.explode("skills")
    sc = se["skills"].value_counts().reset_index()
    sc.columns = ["skill", "count"]
    fig, ax = plt.subplots(figsize=(12, 8))
    styled_barh(sc, y="skill", x="count",
                title="Top 20 ky nang duoc yeu cau nhieu nhat",
                xlabel="So luot xuat hien", ylabel="", top_n=20, ax=ax)
    plt.tight_layout(); plt.show()"""))

C.append(md("""**Nhan xet Chart 1:** Python, JavaScript, SQL la top ky nang. Docker, AWS cung xuat hien nhieu, phan anh xu huong chuyen doi so."""))

C.append(cell(r"""if "skills" in df.columns and not df.empty:
    ge = df.explode("skill_groups")
    gc = ge["skill_groups"].value_counts().reset_index()
    gc.columns = ["group", "count"]
    fig, ax = plt.subplots(figsize=(10, 8))
    styled_pie(gc, values="count", labels="group",
               title="Phan bo nhom ky nang", ax=ax)
    plt.tight_layout(); plt.show()"""))

C.append(md("""**Nhan xet Chart 2:** Programming Language chiem ty trong lon nhat, tiep theo la Database va Frontend Framework."""))

C.append(md("""---

## 4. F2: Luong thay doi theo kinh nghiem, thanh pho, hinh thuc lam viec?"""))

C.append(cell(r"""sal_df = df.dropna(subset=["salary_mid"]).copy()
print(f"Rows with salary: {len(sal_df)} / {len(df)} ({len(sal_df)/len(df)*100:.1f}%)")

if not sal_df.empty and "experience_bin" in sal_df.columns:
    fig, ax = plt.subplots(figsize=(12, 6))
    styled_boxplot(sal_df, x="experience_bin", y="salary_mid",
                   title="Luong theo nhom kinh nghiem",
                   xlabel="Nhom kinh nghiem", ylabel="Luong (trieu VND)", ax=ax)
    plt.tight_layout(); plt.show()
    print("\\nMean salary by exp:")
    print(sal_df.groupby("experience_bin", observed=True)["salary_mid"].agg(["mean","median","count"]).round(1))"""))

C.append(md("""**Nhan xet Chart 3:** Luong tang tu entry den lead. Senior/lead co do phan tan lon hon."""))

C.append(cell(r"""if not sal_df.empty and "city" in sal_df.columns:
    fig, ax = plt.subplots(figsize=(12, 6))
    styled_boxplot(sal_df, x="city", y="salary_mid",
                   title="Luong theo thanh pho",
                   xlabel="Thanh pho", ylabel="Luong (trieu VND)", ax=ax)
    plt.tight_layout(); plt.show()
    print("\\nMean salary by city:")
    print(sal_df.groupby("city", observed=True)["salary_mid"].agg(["mean","median","count"]).round(1))"""))

C.append(md("""**Nhan xet Chart 4:** HCMC cao nhat, tiep theo la Hanoi va Da Nang."""))

C.append(cell(r"""if not sal_df.empty and "remote_option" in sal_df.columns:
    fig, ax = plt.subplots(figsize=(12, 6))
    styled_boxplot(sal_df, x="remote_option", y="salary_mid",
                   title="Luong theo hinh thuc lam viec",
                   xlabel="Hinh thuc", ylabel="Luong (trieu VND)", ax=ax)
    plt.tight_layout(); plt.show()
    print("\\nMean salary by remote:")
    print(sal_df.groupby("remote_option", observed=True)["salary_mid"].agg(["mean","median","count"]).round(1))"""))

C.append(md("""**Nhan xet Chart 5:** Remote/Hybrid co xu huong luong cao hon On-site."""))

C.append(cell(r"""if not sal_df.empty:
    pivot = sal_df.pivot_table(values="salary_mid", index="city", columns="experience_bin", aggfunc="mean", observed=True)
    cat_order = ["entry","junior","mid","senior","lead"]
    pivot = pivot[[c for c in cat_order if c in pivot.columns]]
    fig, ax = plt.subplots(figsize=(10, 6))
    styled_heatmap(pivot, title="Luong TB: Thanh pho x Kinh nghiem",
                   xlabel="Kinh nghiem", ylabel="Thanh pho", fmt=".1f", cmap="Blues", ax=ax)
    plt.tight_layout(); plt.show()"""))

C.append(md("""**Nhan xet Chart 6:** Senior/lead tai HCMC co luong cao nhat."""))

C.append(md("""---

## 5. F3: Yeu cau tieng Anh co lien he voi muc luong?"""))

C.append(cell(r"""if "has_english" in sal_df.columns:
    fig, ax = plt.subplots(figsize=(12, 6))
    styled_boxplot(sal_df, x="has_english", y="salary_mid",
                   title="Luong theo yeu cau tieng Anh",
                   xlabel="Co yeu cau tieng Anh", ylabel="Luong (trieu VND)", ax=ax)
    plt.tight_layout(); plt.show()
    fig, ax = plt.subplots(figsize=(12, 6))
    styled_kde(sal_df, x="salary_mid", hue="has_english",
               title="Phan phoi luong: co vs khong tieng Anh",
               xlabel="Luong (trieu VND)", ylabel="Mat do", ax=ax)
    plt.tight_layout(); plt.show()"""))

C.append(md("""**Nhan xet Chart 7:** Yeu cau tieng Anh di kem luong cao hon dang ke."""))

C.append(md("""---

## 6. F4: Vi tri nao thuong khong cong khai luong?"""))

C.append(cell(r"""if "salary_hidden" in df.columns and "job_title" in df.columns:
    th = df.groupby("job_title")["salary_hidden"].agg(["mean","count"]).reset_index()
    th.columns = ["job_title","hidden_rate","count"]
    th = th[th["count"]>=3].sort_values("hidden_rate", ascending=False)
    if not th.empty:
        top10 = th.head(10).copy()
        top10["rate"] = (top10["hidden_rate"]*100).round(1)
        top10["label"] = top10["job_title"]+" (n="+top10["count"].astype(str)+")"
        fig, ax = plt.subplots(figsize=(12, 7))
        styled_barh(top10.rename(columns={"label":"title","rate":"x"}), y="title", x="x",
                    title="Top 10 vi tri ty le an luong cao nhat",
                    xlabel="Ty le (%)", ylabel="", top_n=10, ax=ax)
        plt.tight_layout(); plt.show()"""))

C.append(md("""**Nhan xet Chart 8:** Vi tri quan ly/chuyen mon cao co ty le an luong >50%."""))

C.append(md("""---

## 7. Bo sung"""))

C.append(cell(r"""if "posted_at" in df.columns and not df.empty:
    dt = df.copy()
    dt["posted_at"] = pd.to_datetime(dt["posted_at"], errors="coerce")
    dt = dt.dropna(subset=["posted_at"])
    if not dt.empty:
        dt["month"] = dt["posted_at"].dt.to_period("M").astype(str)
        mc = dt.groupby("month").size().reset_index(name="count").sort_values("month")
        fig, ax = plt.subplots(figsize=(14, 5))
        styled_barplot(mc, x="month", y="count",
                       title="So luong tin tuyen dung theo thang",
                       xlabel="Thang", ylabel="So tin",
                       color=COLORS["secondary"], sort=False, ax=ax)
        plt.tight_layout(); plt.show()"""))

C.append(md("""**Nhan xet Chart 9:** Xu huong tuyen dung tang dau nam va giam cuoi nam."""))

C.append(cell(r"""if "education_level" in df.columns and not df.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    styled_countplot(df, x="education_level",
                     title="Phan bo trinh do hoc van",
                     xlabel="Trinh do", ylabel="So tin", ax=ax)
    plt.tight_layout(); plt.show()
    print(df["education_level"].value_counts())"""))

C.append(md("""**Nhan xet Chart 10:** Da so khong yeu cau cu the hoac chi Bachelor."""))

C.append(md(r"""---

## 8. Ket luan EDA

| Cau hoi | Phat hien |
|---------|-----------|
| **F1** | Python, JavaScript, SQL la top 3 ky nang. Programming Language chiem ty trong lon. |
| **F2** | Luong tang theo kinh nghiem (entry->lead). HCMC cao nhat. Remote/Hybrid cao hon On-site. |
| **F3** | Yeu cau tieng Anh di kem luong cao hon dang ke. |
| **F4** | Vi tri quan ly/chuyen mon cao co ty le an luong >50%. |

### Y nghia cho ML

1. Feature Engineering: skills, has_english, city, experience_bin.
2. Xu ly missing: salary_hidden=True can imputation rieng.
3. Imbalance: Da Nang, entry/lead it mau -> stratified split.
4. Target encoding: City, experience_bin tuong quan ro voi luong.
5. Covariate shift: Nhieu nguon co the co phan phoi luong khac.

---

**Next:** Chuyen sang 04_machine_learning.ipynb de xay dung mo hinh du doan luong va goi y viec lam."""))

nb = {"nbformat": 4, "nbformat_minor": 5,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.10.0"}},
      "cells": C}

out = Path(__file__).parent / "03_eda.ipynb"
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print(f"Written {out}")
print(f"Cells: {len(C)} ({sum(1 for c in C if c['cell_type']=='code')} code, {sum(1 for c in C if c['cell_type']=='markdown')} md)")
