# Báo cáo Đồ án — Phân Tích Thị Trường Việc Làm & Gợi Ý Ứng Viên

**Môn:** Lập trình cho Khoa học Dữ liệu
**Chuyên đề:** 4 — Phân tích thị trường việc làm & gợi ý ứng viên
**Nhóm:** 2 thành viên
**Ngày:** 2026-07-20

---

## 1. Giới thiệu

### 1.1 Bối cảnh
Thị trường việc làm IT tại Việt Nam đang phát triển mạnh mẽ, với nhiều nền tảng tuyển dụng khác nhau như itviec.com, vietnamworks.com, topdev.vn. Tuy nhiên, dữ liệu tuyển dụng phân tán, thiếu chuẩn hóa, gây khó khăn cho người tìm việc trong việc xác định mức lương phù hợp và kỹ năng cần thiết.

### 1.2 Mục tiêu
1. Thu thập dữ liệu tuyển dụng IT từ các trang web
2. Chuẩn hóa lương, kỹ năng, kinh nghiệm
3. Phân tích thị trường qua EDA
4. Xây dựng mô hình dự đoán lương
5. Gợi ý việc làm phù hợp với hồ sơ kỹ năng

### 1.3 Câu hỏi nghiên cứu (F1-F6)
| # | Câu hỏi | Phương pháp |
|---|---------|-------------|
| F1 | Kỹ năng nào được yêu cầu nhiều nhất? | Top skills bar chart |
| F2 | Lương thay đổi theo kinh nghiệm, thành phố, hình thức? | Boxplot, groupby |
| F3 | Yêu cầu tiếng Anh có liên hệ với lương? | Boxplot, KDE |
| F4 | Vị trí nào thường không công khai lương? | Hidden rate by title |
| F5 | Mô hình dự đoán sai số bao nhiêu? | RMSE, MAE, R², error analysis |
| F6 | Top việc phù hợp với hồ sơ kỹ năng? | Cosine similarity |

---

## 2. Dữ liệu

### 2.1 Kiến trúc dữ liệu (ER)
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

### 2.2 Từ điển dữ liệu (Data Dictionary)
| Column | Type | Description | Values |
|--------|------|-------------|--------|
| job_id | string | Mã định danh | fallback_000000 |
| job_title | string | Tên vị trí | Machine Learning Engineer |
| city | string | Thành phố | HCMC, Hanoi, Da Nang |
| experience_years | float | Số năm kinh nghiệm | 0.5 - 15.0 |
| salary_mid | float | Lương TB (triệu VND) | 5 - 80 |
| skills | list[string] | Kỹ năng yêu cầu | ["Python", "SQL"] |
| has_english | bool | Có yêu cầu tiếng Anh | True/False |
| remote_option | string | Hình thức làm việc | On-site, Hybrid, Remote |
| experience_bin | string | Nhóm kinh nghiệm | entry → lead |

### 2.3 Thống kê
| Chỉ tiêu | Giá trị |
|----------|---------|
| Số jobs | 1.329 |
| Số thuộc tính | 34 |
| Thành phố | 3 (HCMC, Hanoi, Da Nang) |
| Kỹ năng unique | 45, với 188 synonym mappings |
| Jobs có skills | 100% |
| Salary hidden | 25% |
| Nguồn | Fallback (100%) |

---

## 3. Thu thập dữ liệu

### 3.1 Scrapers
4 scrapers được triển khai:
- **itviec.com**: CSS selectors theo cấu trúc HTML (no cards found)
- **vietnamworks.com**: URL pattern `/viec-lam/{keyword}` (404)
- **topdev.vn**: HTML + JSON-LD parsing (no cards found)
- **careerbuilder.vn**: Đa ngành fallback (no cards)

**Kết quả:** 100% site block → fallback data (đáp ứng A4)

### 3.2 Fallback data
Generator sinh 1500 jobs realistic với:
- 32 job titles, 33 companies, 45 skills
- Salary phân phối log-normal
- Inject dirty data: 15% missing, 3% duplicates

---

## 4. Làm sạch dữ liệu

### 4.1 SalaryParser (E1)
6 regex patterns cho các định dạng lương thực tế:
- Range: "10-15 triệu" → (10, 15)
- Up to: "tới 20 triệu" → (None, 20)
- From: "từ 15 triệu" → (15, None)
- USD: "1200-1800 USD" → *25,000 → VND
- Yearly: "80-120 triệu/năm" → /12
- Hidden: "cạnh tranh", "thỏa thuận", "negotiable"

Xử lý: swap min-max nếu nhầm, NaN → giữ nguyên.

### 4.2 SkillNormalizer (E2, C6)
188 synonym mappings:
- JS → JavaScript, ReactJS → React, Python3 → Python
- golang → Go, k8s → Kubernetes, ML → Machine Learning
- tiếng anh → English
- Fuzzy fallback: SequenceMatcher > 0.8

### 4.3 ExperienceNormalizer (E4)
Parse text → float → bin:
- entry: 0-2 năm, junior: 2-4, mid: 4-7, senior: 7-10, lead: 10+

### 4.4 Deduplicator (E6)
4-phase detection:
1. Exact by job_id
2. Exact by title + company
3. Fuzzy by title (SequenceMatcher > 0.8)
4. Fuzzy by description (> 0.7, skip nếu > 500 rows)

Kết quả: 29 duplicate groups, 75 records removed.

### 4.5 TitleNormalizer (E3)
Map tương đương: "Frontend Dev" = "Frontend Developer"

---

## 5. EDA & Trực quan hóa

### 5.1 Top kỹ năng (F1)
Top 10: JavaScript (376), React (214), Kafka (208), Ruby (204),
TensorFlow (201), Vue.js (197), Jenkins (196), Spring Boot (194),
Go (191), Docker (188)

Phân bố nhóm: Data Science (23%) > Programming Language (22%) > DevOps (15%)

### 5.2 Lương theo yếu tố (F2)
- **Kinh nghiệm**: Lương tăng đều entry→lead (10M→35M)
- **Thành phố**: HCMC > Hanoi > Da Nang
- **Remote**: Remote/Hybrid > On-site
- **Kết hợp**: Senior/lead tại HCMC có lương cao nhất

### 5.3 Tiếng Anh & lương (F3)
Jobs yêu cầu tiếng Anh có lương cao hơn ~30%.
58% jobs có yêu cầu tiếng Anh.

### 5.4 Hidden Salary (F4)
Vị trí quản lý/cấp cao có tỷ lệ ẩn lương > 50%.

---

## 6. Mô hình Machine Learning

### 6.1 Feature Engineering
- **Pipeline**: ColumnTransformer
  - Numeric: experience_years → median imputer → StandardScaler
  - Categorical: city, job_type, remote_option, education_level → Unknown → OHE
  - Ordinal: experience_bin → OrdinalEncoder
- **Target**: salary_mid (triệu VND/tháng)
- **Train/Test**: 80/20

### 6.2 Baseline (G1)
DummyRegressor: mean (RMSE=8.97M), median (RMSE=9.18M)

### 6.3 Linear Regression (G2)
RMSE=4.17M, R²=0.78, cải thiện 53.5% so với baseline.
Dễ interpret, feature importance rõ ràng.

### 6.4 Decision Tree (G3)
RMSE=0.60M, R²=0.996, cải thiện 93.3%.
Feature: max_depth=8, min_samples_leaf=5.

### 6.5 Random Forest
RMSE≈0, R²≈1 — overfit (data synthetic không đủ noise).

### 6.6 Error Analysis (A15)
- 12 worst cases: residual < 2.1M
- Over/under predict cân bằng
- Residual mean ≈ 0, std ≈ 0.6M

**Warning:** Kết quả quá tốt so với thực tế do dữ liệu synthetic.
Cần crawl data thật để đánh giá chính xác.

---

## 7. K-Means Clustering (G5)

**Cấu hình:**
- Features: experience_years, salary_mid, city, remote_option, skills
- Silhouette score: 0.38 (k=10)

**5 cluster tiêu biểu:**
| Cluster | % | Salary | Kinh nghiệm | Đặc điểm |
|---------|---|--------|------------|----------|
| 0 | 21% | 15.1M | 2.6y | Junior-Mid, Hanoi |
| 1 | 14% | 27.1M | 2.6y | Mid-Senior, HCMC |
| 4 | 10% | 41.9M | 4.8y | Senior, lương cao |
| 8 | 21% | 20.8M | 2.1y | Mid, đa dạng |
| 9 | 4% | 31.6M | 2.7y | Remote jobs |

---

## 8. Content-based Recommendation (G6)

**Phương pháp:**
- MultiLabelBinarizer → job × skill matrix (1500 × 45)
- Cosine similarity → top-N jobs

**Demo: user_skills = ["Python", "SQL", "Machine Learning"]**
→ Top recommendations: Data Scientist, ML Engineer, Data Engineer

**Kết quả:** Matched skills + missing skills visualization.

---

## 9. Đánh giá & Hạn chế (A16)

### 9.1 Rủi ro thiên lệch
1. **100% fallback data** → không đại diện thị trường thật
2. **Imbalance**: HCMC (50%), Da Nang (4%) → model bias
3. **Salary midpoint**: Dùng (min+max)/2 thay vì lương thực tế
4. **Thiếu feature**: Skill encoding trong regression, text features từ description

### 9.2 Hạn chế
1. Scrapers không crawl được dữ liệu thật
2. Decision Tree/RF overfit do data synthetic
3. Chưa có collaborative filtering
4. Chưa xét yếu tố thời gian (seasonality)
5. Feature engineering còn đơn giản

### 9.3 Cải thiện
1. Fix URL patterns cho scrapers
2. Thu thập dữ liệu thật từ các site
3. Thêm skill encoding vào regression features
4. Thử DBSCAN / Hierarchical Clustering
5. Kết hợp collaborative + content-based filtering

---

## 10. Kết luận

Đã xây dựng thành công pipeline phân tích thị trường việc làm:
- ✅ 4 notebooks chạy end-to-end không lỗi
- ✅ 1329 jobs, 34 cols, 3 cities
- ✅ Cleaning đầy đủ: salary, skills, experience, dedup
- ✅ 8+ EDA charts (top skills, salary by factors, etc.)
- ✅ Baseline + Linear Regression + Decision Tree + Random Forest
- ✅ K-Means clustering + phân tích cluster profiles
- ✅ Content-based recommendation với cosine similarity
- ✅ Logs: cleaning errors (23k lines), source metadata (36k lines)
- ✅ AI usage log, contribution table, README

---

## 11. Phân công thành viên

| # | Yêu cầu | Member 1 | Member 2 |
|---|---------|----------|----------|
| M1 | ≥1 class | JobPosting + Company | Skill + RecommendationEngine |
| M2 | ≥1 cleaning | SalaryParser + ExperienceNormalizer | SkillNormalizer + Deduplicator |
| M3 | ≥2 charts | Salary charts (boxplot, heatmap) | Skill charts (bar, pie) |
| M4 | ≥1 model | Baseline + Clustering | Supervised + Recommendation |
| M5 | Trình bày | Phần của mình | Phần của mình |

*Bảng phân công chi tiết: `contribution_table.md`*

---

*Báo cáo được tạo ngày 2026-07-20.*
*AI usage log: `reports/ai_usage_log.md`*
