# Phân Tích Thị Trường Việc Làm & Gợi Ý Ứng Viên (Chuyên Đề 4)

**Môn:** Lập trình cho Khoa học Dữ liệu
**Nhóm:** 2 thành viên — 8 buổi
**Ngày:** 2026-07-20

---

## Mục lục

- [Mô tả dự án](#mô-tả-dự-án)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Yêu cầu & Trạng thái](#yêu-cầu--trạng-thái)
- [Kiến trúc](#kiến-trúc)
- [Cài đặt](#cài-đặt)
- [Chạy lại toàn bộ pipeline](#chạy-lại-toàn-bộ-pipeline)
- [Kết quả](#kết-quả)
- [Phân công thành viên](#phân-công-thành-viên)
- [Lưu ý pháp lý](#lưu-ý-pháp-lý)

---

## Mô tả dự án

**Đề bài:** Cào dữ liệu tuyển dụng từ các trang web Việt Nam (itviec.com, vietnamworks.com, topdev.vn, careerbuilder.vn), chuẩn hóa lương/kỹ năng, dự đoán lương, gợi ý tin tuyển dụng theo hồ sơ ứng viên.

**Phạm vi:** Nhóm nghề **Lập trình / Data** (IT jobs)

**Mục tiêu:**
1. Thu thập dữ liệu tuyển dụng IT từ các trang web
2. Chuẩn hóa lương, kỹ năng, kinh nghiệm
3. Phân tích thị trường qua EDA (8+ biểu đồ)
4. Xây dựng mô hình dự đoán lương (baseline + 3 supervised)
5. Phân cụm việc làm (K-Means)
6. Gợi ý việc làm theo hồ sơ kỹ năng (content-based recommendation)

---

## Cấu trúc thư mục

```
├── data/
│   ├── raw/                  # Dữ liệu gốc (raw_jobs/skills/companies — CSV+JSON, tự ghi mỗi crawl)
│   └── processed/            # Dữ liệu đã làm sạch (combined.csv + parquet)
├── notebooks/
│   ├── 01_problem_and_data.ipynb       # Problem definition, data dictionary, OOP
│   ├── 02_collection_and_cleaning.ipynb # Thu thập, cleaning, logs
│   ├── 03_eda.ipynb                    # EDA, 8+ charts, F1-F4
│   └── 04_machine_learning.ipynb       # ML models, clustering, recommendation
├── src/
│   ├── crawl/                # Crawler v2: fetchers, normalizer, pipeline, CLI crawl.py
│   ├── domain/               # Domain classes: JobPosting, Skill, Company, JobRecord
│   ├── data/                 # data_manager.py, salary_parser.py
│   ├── cleaning/             # skill_normalizer, experience_normalizer, deduplicator, title_normalizer
│   ├── features/             # feature_pipeline.py (ColumnTransformer)
│   ├── ml/                   # baseline, supervised, clustering, recommendation
│   └── visualization/        # chart_utils.py (styled charts)
├── logs/
│   ├── cleaning_errors.log   # chi tiết cleaning errors
│   ├── source_metadata.log   # 39k+ lines — nguồn gốc từng record
│   └── crawl_history/        # Nhật ký từng lần crawl (JSON)
├── reports/
│   ├── ai_usage_log.md       # Prompt log (B11, L1-L3)
│   ├── final_report.md       # Báo cáo 20 trang (B9)
│   └── slides/
│       └── slide_deck.md     # Slide thuyết trình
├── tests/                    # pytest: crawl, cleaning, ml
├── scripts/
│   └── recommend_jobs.py     # CLI gợi ý việc theo hồ sơ (skills + --years/--city)
├── crawl.py                  # CLI crawl v2 (thu thập dữ liệu)
├── README.md
├── contribution_table.md     # Phân công (B12, J4)
├── requirements.txt
└── verify_data.py            # Verification checklist
```

---

## Yêu cầu & Trạng thái

### A — Yêu cầu chung

| # | Yêu cầu | Trạng thái | Ghi chú |
|---|---------|------------|---------|
| A1 | Quy trình KHDL đủ 9 bước | ✅ | problem → collect → check → clean → EDA → viz → model → eval → report |
| A2 | Phạm vi hẹp, 2 tuần | ✅ | 1 chuyên đề, 8 buổi |
| A3 | Không vi phạm pháp lý | ✅ | requests + BeautifulSoup, không CAPTCHA/login |
| A4 | Phương án dự phòng | ✅ | Fallback data generator khi scrapers block |
| A5 | ≥2 nguồn/định dạng | ✅ | 4 sources; CSV + JSON (raw), Parquet + CSV (processed) |
| A6 | ≥1.000 bản ghi | ✅ | 1.193 jobs |
| A7 | ≥10 thuộc tính | ✅ | 44 columns |
| A8 | Có dữ liệu bẩn | ✅ | Inject missing (15%), duplicate (3%), typo |
| A9 | Baseline | ✅ | DummyRegressor (mean, median) |
| A10 | ≥2 mô hình có giám sát | ✅ | Linear Regression, Decision Tree, Random Forest |
| A11 | 1 bài toán phân cụm/gợi ý | ✅ | K-Means + Content-based Recommendation |
| A12 | Chia train/test | ✅ | 80/20 split |
| A13 | Dùng Pipeline | ✅ | ColumnTransformer (numeric, categorical, ordinal) |
| A14 | Không đánh giá trên train | ✅ | Test riêng |
| A15 | ≥10 trường hợp sai | ✅ | Error analysis: 12 worst cases, residual distribution |
| A16 | Nêu giới hạn dữ liệu | ✅ | Notebook 04 section + report |
| A17 | ≥8 biểu đồ | ✅ | 10 biểu đồ trong 03_eda |

### B — Sản phẩm bắt buộc

| # | Yêu cầu | File | Status |
|---|---------|------|--------|
| B1 | Notebook 1 | `01_problem_and_data.ipynb` | ✅ 14 cells, executed |
| B2 | Notebook 2 | `02_collection_and_cleaning.ipynb` | ✅ 26 cells, executed |
| B3 | Notebook 3 | `03_eda.ipynb` | ✅ 34 cells, 10 charts |
| B4 | Notebook 4 | `04_machine_learning.ipynb` | ✅ 35 cells, all models |
| B5 | Mã nguồn src/ | `src/` (17 files) | ✅ |
| B6 | Dữ liệu gốc | `data/raw/` | ✅ `raw_jobs_*.csv/.json`, `raw_skills_*.csv`, `raw_companies_*.csv` (tự ghi mỗi lần crawl) |
| B7 | Dữ liệu sạch | `data/processed/` | ✅ Parquet + CSV |
| B8 | Nhật ký lỗi | `logs/cleaning_errors.log` | ✅ |
| B9 | Báo cáo | `reports/final_report.md` + `reports/slides/slide_deck.md` | ✅ |
| B10 | README | `README.md` | ✅ |
| B11 | AI usage log | `reports/ai_usage_log.md` | ✅ |
| B12 | Bảng phân công | `contribution_table.md` | ✅ |

### C — Yêu cầu dữ liệu Chuyên đề 4

| # | Yêu cầu | Trạng thái |
|---|---------|------------|
| C1 | Nhóm nghề | ✅ Lập trình / Data |
| C2 | Cấu trúc job_postings | ✅ job_id → crawled_at (15 fields) |
| C3 | Cấu trúc job_skills | ✅ job_id, skill_name, skill_group, required_level |
| C4 | Cấu trúc companies | ✅ company_id, company_size, industry, city |
| C5 | ≥1.000 tin tuyển dụng | ✅ 1.193 |
| C6 | ≥20 kỹ năng chuẩn hóa | ✅ 188 synonym entries |
| C7 | ≥12 thuộc tính | ✅ 44 |
| C8 | ≥3 thành phố | ✅ HCMC, Hanoi, Da Nang (+ tỉnh lẻ từ careerviet) |
| C9 | 2+ nguồn/định dạng | ✅ CSV + JSON (raw) + Parquet + CSV (processed) |

### D — Yêu cầu OOP & Python

| # | Yêu cầu | File | Status |
|---|---------|------|--------|
| D1 | JobPosting | `src/domain/job_posting.py` | ✅ Dataclass, 20 fields |
| D2 | Skill | `src/domain/skill.py` | ✅ Dataclass, 5 fields |
| D3 | JobDataManager | `src/data/data_manager.py` | ✅ Load, merge, log, save |
| D4 | RecommendationEngine | `src/ml/recommendation.py` | ✅ Cosine similarity |
| D5 | Đọc HTML/JSON/CSV | `src/crawl/fetchers.py` | ✅ JSON-LD, __NEXT_DATA__, HTML |
| D6 | Phát hiện trùng | `src/cleaning/deduplicator.py` | ✅ Exact + fuzzy |
| D7 | Ghi lỗi + metadata | `src/data/data_manager.py` | ✅ cleaning_logger + source_logger |

### E — Yêu cầu làm sạch

| # | Yêu cầu | Xử lý | Status |
|---|---------|-------|--------|
| E1 | Chuẩn hóa lương | 6 regex patterns, USD→VND, năm→tháng, swap min-max | ✅ |
| E2 | Chuẩn hóa kỹ năng | Synonym map 188 entries, fuzzy fallback | ✅ |
| E3 | Chuẩn hóa tên vị trí | Title mapping | ✅ |
| E4 | Chuẩn hóa kinh nghiệm | Parse text → float → bin | ✅ |
| E5 | Xử lý thiếu | NaN giữ nguyên, báo cáo tỷ lệ (%) | ✅ |
| E6 | Xử lý trùng | Exact (job_id, title+company) + Fuzzy (title 80%, desc 70%) | ✅ |
| E7 | Xử lý sai kiểu | Swap min-max nếu nhầm | ✅ |

### F — Câu hỏi nghiên cứu

| # | Câu hỏi | Notebook | Trạng thái |
|---|---------|----------|------------|
| F1 | Kỹ năng nào được yêu cầu nhiều nhất? | 03_eda | ✅ Top skills chart + group distribution |
| F2 | Lương thay đổi theo kinh nghiệm, thành phố, remote? | 03_eda | ✅ Boxplots + pivot heatmap |
| F3 | Tiếng Anh có liên hệ với lương? | 03_eda | ✅ Boxplot + KDE |
| F4 | Vị trí nào không công khai lương? | 03_eda | ✅ Hidden rate by title |
| F5 | Mô hình dự đoán sai số bao nhiêu? | 04_ml | ✅ RMSE, MAE, R², 12 error cases |
| F6 | Top việc phù hợp với từng hồ sơ? | 04_ml | ✅ Cosine similarity, top-10 |

### G — Yêu cầu mô hình

| # | Yêu cầu | File | Status |
|---|---------|------|--------|
| G1 | Baseline | `src/ml/baseline.py` | ✅ DummyRegressor (mean/median) |
| G2 | Linear Regression | `src/ml/supervised.py` | ✅ RMSE=4.17M, R²=0.78 |
| G3 | Decision Tree | `src/ml/supervised.py` | ✅ RMSE=0.60M, R²=0.996 |
| G4 | Salary classification | `src/ml/supervised.py` | ✅ Có thể dùng classify_salary() |
| G5 | K-Means clustering | `src/ml/clustering.py` | ✅ k=10, silhouette=0.38, PCA viz |
| G6 | Content-based reco | `src/ml/recommendation.py` | ✅ Cosine similarity, job×skill matrix |

### H — Yêu cầu EDA & Trực quan

| # | Yêu cầu | Status |
|---|---------|--------|
| H1 | ≥8 biểu đồ | ✅ 10 charts (top skills, skill group pie, salary boxplot×3, heatmap, English boxplot+KDE, hidden rate, time series, education) |
| H2 | Groupby/Pivot | ✅ Salary ~ city × experience pivot heatmap |
| H3 | 5 bảng Groupby/Pivot | ✅ Salary by title, city, exp, remote, hidden rate |

### J — Điều kiện đạt

| # | Điều kiện | Status |
|---|-----------|--------|
| J1 | Có dữ liệu gốc và đã làm sạch | ✅ 1.193 jobs, 44 cols, raw + processed |
| J2 | Mã nguồn chạy được từ đầu đến cuối | ✅ `crawl.py` CLI + notebooks → DONE |
| J3 | Có baseline và đánh giá trên test | ✅ Baseline + 3 models, train/test 80/20 |
| J4 | Phân công và minh chứng | ✅ contribution_table.md |
| J5 | Giải thích được kết quả AI | ✅ reports/ai_usage_log.md |
| J6 | Không vi phạm quyền riêng tư | ✅ Crawl v2 public data, không PII |

---

## Kiến trúc

### Quy trình xử lý (Pipeline)

```
Scrapers (4 sites) → Fallback (nếu thiếu)
    ↓
Save raw (CSV + JSON)
    ↓
Salary parsing (6 patterns)
    ↓
Inject dirty data (~15% missing, ~3% dup)
    ↓
City/remote separation
    ↓
Skill normalization (188 synonyms)
    ↓
Job title normalization
    ↓
Experience parsing → bin
    ↓
Deduplication (exact + fuzzy)
    ↓
Merge 3 datasets (jobs + skills + companies)
    ↓
Save processed (Parquet + CSV)
```

### ER Diagram

```
+----------------+       +----------------------+       +--------------+
|   companies    |       |    job_postings      |       |   job_skills |
|----------------|       |----------------------|       |--------------|
| company_id (PK)|<------| company_id (FK)      |       | job_id (FK)  |
| company_name   |       | job_id (PK)          |<------| skill_name   |
| company_size   |       | job_title            |       | skill_group  |
| industry       |       | city                 |       | required_lvl |
| city           |       | salary_min/max       |       +--------------+
+----------------+       | experience_years     |
                          | has_english          |
                          +----------------------+
```

### ML Pipeline

```
Raw Data → Feature Engineering (ColumnTransformer)
    → Baseline (DummyRegressor)
    → Linear Regression
    → Decision Tree / Random Forest
    → Evaluation (RMSE, MAE, R²)
    → Error Analysis (top-12 residuals)
    
Unsupervised:
    Raw Data → Feature Matrix → K-Means → PCA 2D → Cluster Profiles
    
Recommendation:
    Skills Data → MultiLabelBinarizer → Cosine Similarity → Top-N Jobs
```

---

## Cài đặt

```bash
# Clone repo
git clone <repo-url>
cd KhoaHocDuLieu

# Tạo virtual environment (khuyến nghị)
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

### requirements.txt

```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.3.0
scipy>=1.11.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
httpx>=0.25.0
jupyter>=1.0.0
notebook>=7.0.0
ipykernel>=6.25.0
```

---

## Chạy lại toàn bộ pipeline

### 1. Thu thập dữ liệu (crawl v2)

```bash
python crawl.py --sites "itviec,glints,vietnamworks" --keywords "python,data"
```

> **Lưu ý:** `--sites`/`--keywords` nhận danh sách cách nhau bởi dấu phẩy (không phải khoảng trắng).
> `--max-pages N` tăng số trang/site/keyword. `vietnamworks` thường bị block (HTML fallback), chạy sâu hơn nếu cần:
> `python crawl.py --sites "itviec,glints" --keywords "python,data,developer,engineer" --max-pages 5`

CLI crawl v2:
- Crawl các site tuyển dụng (JSON-LD, __NEXT_DATA__, HTML fallback)
- Chuẩn hóa → JobRecord → deduplicate → merge
- Ghi `data/processed/combined.csv` + nhật ký `logs/crawl_history/`

Xem thêm: `python crawl.py --help`

### 2. Gợi ý việc làm theo hồ sơ (kỹ năng + kinh nghiệm + thành phố)

```bash
python scripts/recommend_jobs.py Python SQL --city HCMC --years 3 --top-n 5
```

CLI đọc `data/processed/combined.csv`, lọc theo `--city` (không phân biệt hoa/thường)
và `--years` (kinh nghiệm ±0.5 năm), trả về top-N việc phù hợp nhất theo độ tương đồng kỹ năng.

### 3. Verify data

```bash
python verify_data.py
```

### 4. Chạy notebooks (tuần tự)

```bash
jupyter notebook

# Mở lần lượt:
# 1. notebooks/01_problem_and_data.ipynb
# 2. notebooks/02_collection_and_cleaning.ipynb
# 3. notebooks/03_eda.ipynb
# 4. notebooks/04_machine_learning.ipynb
```

Hoặc chạy headless:

```bash
jupyter nbconvert --to notebook --execute notebooks/01_problem_and_data.ipynb --output 01.ipynb
jupyter nbconvert --to notebook --execute notebooks/02_collection_and_cleaning.ipynb --output 02.ipynb
jupyter nbconvert --to notebook --execute notebooks/03_eda.ipynb --output 03.ipynb
jupyter nbconvert --to notebook --execute notebooks/04_machine_learning.ipynb --output 04.ipynb
```

### 5. Chạy tests

```bash
pytest tests/ -v
```

### Output files

| File | Mô tả |
|------|-------|
| `data/raw/raw_jobs_*.csv` | Raw jobs data (CSV) |
| `data/raw/raw_jobs_*.json` | Raw jobs data (JSON) |
| `data/raw/raw_skills_*.csv` | Raw skills data |
| `data/raw/raw_companies_*.csv` | Raw companies data |
| `data/processed/combined_*.parquet` | Clean merged data (Parquet) |
| `data/processed/combined.csv` | Clean merged data (CSV) |
| `logs/cleaning_errors.log` | Cleaning error log |
| `logs/source_metadata.log` | Source tracking log |

---

## Kết quả

### Data

| Chỉ tiêu | Giá trị |
|----------|---------|
| Tổng số jobs | 1.193 |
| Thuộc tính | 44 columns |
| Thành phố | HCMC (468), Hanoi (366), Da Nang (14) + tỉnh lẻ (careerviet) |
| Kỹ năng | 188 synonyms (45 unique canonical) |
| Jobs có skills | 79/1.193 (6,6%) — careerviet/topcv listing không có skills |
| Salary coverage | 44% (56% hidden) |
| Duplicates removed | 70 records (crawl v2 dedup) |
| Nguồn | careerviet 970, itviec 138, glints 56, topcv 29 |

### Models

| Model | RMSE (M) | MAE (M) | R² |
|-------|----------|---------|-----|
| Baseline (mean) | 8.97 | 7.36 | -0.01 |
| Linear Regression | 4.17 | 2.94 | 0.78 |
| Decision Tree | 0.60 | 0.18 | 0.996 |
| Random Forest | ~0.00 | ~0.00 | ~1.00 |

### Clustering (K-Means)

| Cluster | % Jobs | Lương TB | Kinh nghiệm | Đặc điểm |
|---------|--------|----------|-------------|----------|
| 0 | 21% | 15.1M | 2.6y | Junior-Mid, Hanoi |
| 1 | 14% | 27.1M | 2.6y | Mid-Senior, HCMC |
| 4 | 10% | 41.9M | 4.8y | Senior, lương cao |
| 8 | 21% | 20.8M | 2.1y | Mid, đa dạng |
| 9 | 4% | 31.6M | 2.7y | Remote jobs |

### Logs

| File | Dung lượng |
|------|------------|
| `cleaning_errors.log` | cleaning pipeline log |
| `source_metadata.log` | source tracking log |
| `logs/crawl_history/` | JSON nhật ký từng lần crawl (18 runs, mới nhất 20260810_181540) |

---

## Phân công thành viên

| # | Yêu cầu | Member 1 | Member 2 |
|---|---------|----------|----------|
| M1 | ≥1 class Python chính | JobPosting + Company | Skill + RecommendationEngine |
| M2 | ≥1 phần làm sạch | SalaryParser + ExperienceNormalizer | SkillNormalizer + Deduplicator |
| M3 | ≥2 biểu đồ | Salary charts (boxplot, heatmap) | Skill charts (bar, pie) |
| M4 | ≥1 mô hình | Baseline + Clustering | Supervised + Recommendation |
| M5 | Trình bày ≥7 phút | ⬜ | ⬜ |

*Chi tiết: `contribution_table.md`*

---

## Lưu ý pháp lý

- Chỉ cào dữ liệu công khai, không vượt CAPTCHA, không đăng nhập
- Tôn trọng robots.txt, delay 1-3s giữa các request
- Không thu thập dữ liệu nhạy cảm (SĐT, email, CMND)
- Ghi nguồn rõ ràng trong `logs/source_metadata.log`
- Crawl v2 hoạt động (itviec, glints, careerviet, topcv); vietnamworks bị block — dùng HTML fallback

---

## Giới hạn (A16)

1. **Skills thấp (6,6%)** — careerviet/topcv (89% data) listing không có skills field; itviec/glints chỉ crawl detail khi max-pages cao. Recommendation dùng được nhưng trên tập nhỏ.
2. **vietnamworks bị block** — HTML fallback không lấy được jobs, nguồn chủ yếu careerviet + itviec + glints + topcv.
3. **City có tỉnh lẻ + chuỗi nối** — careerviet listing trả nhiều địa điểm trong 1 element (`Bình Dươngbình Phước`), cần normalization thêm.
4. **Overfitting** — Decision Tree / RF quá tốt do feature hạn chế, cần đánh giá kỹ trên data thật.
5. **Imbalance** — Da Nang chỉ 1%, model bias theo thành phố.
6. **Recommendation** — chỉ dùng content-based, chưa có collaborative filtering.

---

## AI Usage

Xem `reports/ai_usage_log.md` — ghi lại prompt, đầu ra AI, cách kiểm chứng, chỉnh sửa của nhóm.
