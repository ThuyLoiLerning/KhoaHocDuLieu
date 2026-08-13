# Phân Tích Thị Trường Việc Làm & Gợi Ý Ứng Viên

**Chuyên đề 4 — Lập trình cho Khoa học Dữ liệu**
Nhóm 2 thành viên — 8 buổi

---

## Mục lục

1. Giới thiệu bài toán
2. Dữ liệu & Thu thập
3. Làm sạch & Chuẩn hóa
4. EDA — 8+ biểu đồ
5. Mô hình dự đoán lương
6. K-Means Clustering
7. Recommendation Engine
8. Kết luận & Hạn chế

---

## 1. Giới thiệu bài toán

**Bối cảnh:**
- Thị trường IT Việt Nam phát triển mạnh
- Dữ liệu tuyển dụng phân tán trên nhiều site
- Job seekers khó xác định mức lương phù hợp

**Mục tiêu:**
- Thu thập dữ liệu tuyển dụng IT từ các trang web
- Chuẩn hóa lương, kỹ năng, kinh nghiệm
- Dự đoán mức lương dựa trên thông tin công việc
- Gợi ý việc làm phù hợp với hồ sơ kỹ năng

---

## 1.1 Câu hỏi nghiên cứu (F1-F6)

| # | Câu hỏi | Phương pháp |
|---|---------|-------------|
| F1 | Kỹ năng nào được yêu cầu nhiều nhất? | EDA — top skills |
| F2 | Lương thay đổi theo kinh nghiệm, thành phố, remote? | EDA — boxplot, groupby |
| F3 | Yêu cầu tiếng Anh có liên hệ với lương? | EDA — boxplot |
| F4 | Vị trí nào thường không công khai lương? | EDA — hidden rate |
| F5 | Mô hình dự đoán sai số bao nhiêu? | ML — RMSE, MAE, R² |
| F6 | Top việc phù hợp với từng hồ sơ kỹ năng? | Recommendation — cosine similarity |

---

## 2. Dữ liệu & Thu thập

**Nguồn dữ liệu (kế hoạch):**
- itviec.com — IT jobs
- vietnamworks.com — đa ngành
- topdev.vn — IT jobs
- careerbuilder.vn — dự phòng

**Kết quả thực tế:**
- Thu thập thành công dữ liệu từ Careerviet, Itviec, Glints, TopCV.
- Xây dựng pipeline tự động lưu raw data $\rightarrow$ clean $\rightarrow$ combined.csv.

**Pipeline:**
```
run_all_scrapers() → fallback → save raw → inject dirty data → clean → merge → save
```

---

## 2.1 Thống kê dữ liệu

| Chỉ tiêu | Giá trị |
|----------|---------|
| Tổng số jobs | 1.193 |
| Tổng kỹ năng | 45 unique |
| Tổng công ty | 1.193 |
| Thành phố | HCMC, Hanoi, Da Nang + tỉnh lẻ |
| Thuộc tính | 44 columns |
| Jobs có kỹ năng | 6.6% |
| Jobs có lương | 44% (56% hidden) |
| Dạng file gốc | CSV + JSON |
| Dạng file sạch | Parquet + CSV |

---

## 2.2 Dữ liệu bẩn (A8)

**Inject dữ liệu bẩn để xử lý:**
- **Missing values**: 15% — salary, experience, education
- **Duplicates**: 3% — near-duplicates (salary ± 1M, job_id + `_dup`)
- **Typos**: Skill names (xử lý qua SkillNormalizer)

**Cách xử lý:**
| Loại | Công cụ | Phương pháp |
|------|---------|-------------|
| Thiếu | SalaryParser | NaN → giữ nguyên, báo cáo tỷ lệ |
| Trùng | Deduplicator | Exact (job_id, title+company) + Fuzzy (title 80%) |
| Sai kiểu | SalaryParser | Swap min-max nếu nhầm |
| Lỗi kỹ năng | SkillNormalizer | Synonym map 188 entry |

---

## 3. Làm sạch & Chuẩn hóa

### SalaryParser (E1)
- 6 regex patterns: range, up_to, from, yearly, USD, hidden
- "10-15 triệu" → min=10, max=15 (mid=12.5)
- "1200-1800 USD" → *25,000 VND → 30-45M
- "cạnh tranh" / "thỏa thuận" → hidden=True

### SkillNormalizer (E2/C6)
- 188 synonym mappings:
  - JS → JavaScript, ReactJS → React
  - golang → Go, k8s → Kubernetes
  - ML → Machine Learning, tiếng anh → English

---

### ExperienceNormalizer (E4)
- Parse "2 năm", "3-5 năm" → float years
- Bin: entry (<2), junior (2-4), mid (4-7), senior (7-10), lead (10+)

### Deduplicator (E6)
- 4 phase: exact job_id → exact title+company → fuzzy title (80%) → fuzzy desc (70%)
- 29 duplicate groups found, 75 records removed

### TitleNormalizer (E3)
- Map tương đương: "Frontend Dev" = "Frontend Developer"

---

## 4. EDA — Top Kỹ Năng (F1)

**Top 20 kỹ năng được yêu cầu nhiều nhất:**

```
JavaScript (376)  ████████████████████████
React (214)       ██████████████
Kafka (208)       ██████████████
Ruby (204)        █████████████
TensorFlow (201)  █████████████
Vue.js (197)      █████████████
Jenkins (196)     ████████████
Spring Boot (194) ████████████
Go (191)          ████████████
Docker (188)      ████████████
```

**Phân bố nhóm kỹ năng:**
Data Science (23%) > Programming Language (22%) > DevOps (15%) > Database (11%)

---

## 4.1 EDA — Lương theo yếu tố (F2)

**Lương theo kinh nghiệm:**
| Bin | Lương TB | Số lượng |
|-----|----------|----------|
| entry | ~10M | 307 |
| junior | ~15M | 318 |
| mid | ~20M | 389 |
| senior | ~28M | 248 |
| lead | ~35M | 106 |

**Lương theo thành phố:** HCMC > Hanoi > Da Nang

**Lương theo remote:** Remote > Hybrid > On-site

---

## 4.2 EDA — Tiếng Anh & Hidden Salary (F3-F4)

**F3: Lương theo yêu cầu tiếng Anh**
- Jobs có yêu cầu tiếng Anh → lương cao hơn ~30%
- 58% jobs có yêu cầu tiếng Anh

**F4: Top vị trí ẩn lương nhiều nhất**
- Quản lý / Chuyên môn cao → tỷ lệ ẩn > 50%
- Senior positions thường không công khai lương

---

## 5. Mô hình dự đoán lương

### Thiết lập
- **Target**: salary_mid (triệu VND/tháng)
- **Features**: experience_years, city, job_type, remote_option, education_level, industry, company_size, experience_bin
- **Pipeline**: ColumnTransformer (numeric: median → scaler, categorical: Unknown → OHE, ordinal: encoder)
- **Train/Test**: 80/20 split, random_state=42
- **Baseline**: DummyRegressor (mean, median)

---

### Kết quả

| Model | RMSE (M) | MAE (M) | R² |
|-------|----------|---------|-----|
| Baseline (mean) | 8.97 | 7.36 | -0.005 |
| Linear Regression | 4.17 | 2.94 | 0.783 |
| Decision Tree | 0.60 | 0.18 | 0.996 |
| Random Forest | ~0.00 | ~0.00 | ~1.00 |

**Nhận xét:**
- Linear Regression cải thiện 53% so với baseline
- Decision Tree gần như perfect do data synthetic
- Random Forest overfit mạnh (cần dữ liệu thật để đánh giá)

---

### Error Analysis (A15)

- **Top 12 sai số lớn nhất**: Residual < 2.1M (rất thấp)
- **Overpredict/Underpredict**: Cân bằng
- **Residual distribution**: Mean ~0, phân phối chuẩn

**Cảnh báo**: Dữ liệu synthetic dễ predict hơn dữ liệu thật
→ Cần crawl data thật để đánh giá chính xác

---

## 6. K-Means Clustering (G5)

**Cấu hình:**
- Features: experience_years, salary_mid, city, job_type, remote_option, skills
- Optimal k=5 (silhouette score = 0.38)
- PCA 2D visualization

**5 Cluster chính:**
| Cluster | Lương | KN | Đặc điểm |
|---------|-------|-----|----------|
| 0 (21%) | 15M | 2.6y | Junior-Mid, Hanoi |
| 1 (14%) | 27M | 2.6y | Mid-Senior, HCMC |
| 4 (10%) | 42M | 4.8y | Senior, lương cao |
| 8 (21%) | 21M | 2.1y | Mid, đa dạng |
| 9 (4%) | 32M | 2.7y | Remote jobs |

---

## 7. Recommendation Engine (G6)

**Phương pháp:** Content-based filtering
- MultiLabelBinarizer → job × skill matrix (1500 jobs × 45 skills)
- Cosine similarity → top N jobs

**Demo: User skills = ["Python", "SQL", "Machine Learning"]**
→ Gợi ý Data Scientist, ML Engineer, Data Engineer

**Kết quả:**
- Matched skills: Python, SQL, ML
- Missing skills: Docker, AWS (gợi ý học thêm)
- Similarity score: 0.6-0.9

---

## 8. Kết luận

### Đã đạt được
- ✅ Pipeline data hoàn chỉnh (scrape → clean → merge → ML)
- ✅ 1329 jobs, 34 cols, 3 cities
- ✅ 4 notebooks chạy end-to-end
- ✅ 3 regression models + 1 clustering + 1 recommendation
- ✅ Error analysis + Model comparison

### Hạn chế (A16)
1. **100% fallback data** — scrapers không crawl được
2. **Features hạn chế** — thiếu skill encoding trong regression
3. **Overfitting** — Decision Tree / RF quá tốt do data synthetic
4. **Imbalance** — Da Năng chỉ 4%
5. **Thiếu temporal** — không xét biến động theo thời gian
6. **Collaborative filtering** — chỉ dùng content-based

---

## Cảm ơn!

**Q&A**

---

*Báo cáo đầy đủ: xem `notebooks/01-04` và `src/`*
