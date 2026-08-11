# Thiết kế: Mở rộng Chương 2 — Phương pháp nghiên cứu & Dữ liệu đầu vào

**Ngày:** 2026-08-11
**Phạm vi:** `scripts/generate_docx_report.py` — mở rộng nội dung Chương 2 của báo cáo Word (Crawler v2, cleaning pipeline, feature engineering, tổng quan dữ liệu).

## 1. Vấn đề

Chương 2 ("PHƯƠNG PHÁP NGHIÊN CỨU VÀ DỮ LIỆU ĐẦU VÀO") hiện chỉ có 2 mục sơ sài:

- `2.1. Kiến trúc Hệ thống Thu thập Dữ liệu (Crawler v2)` — 1 đoạn ngắn
- `2.2. Quy trình Chuẩn hóa và Làm sạch Dữ liệu (Data Cleaning Pipeline)` — 1 đoạn liệt kê

Yêu cầu: viết chi tiết hơn theo 4 mục, phản ánh đúng kiến trúc thực tế trong code (`src/crawl/`, `src/cleaning/`, `src/features/`).

## 2. Cấu trúc nội dung Chương 2 mới

```
2.1. Kiến trúc Hệ thống Thu thập Dữ liệu (Crawler v2)
     • Luồng tổng thể run_crawl(): vòng lặp site × keyword (22 keyword),
       threshold min_total_jobs (chối ghi CSV nếu dưới ngưỡng),
       crawl_history JSON (timestamp, n_jobs, n_new, src_counts)
     • HttpClient: httpx verify=True + follow_redirects + timeout 20s;
       User-Agent xoay vòng (3 UA); rate-limit ngẫu nhiên 1–3s (chống 429)
     • Chống chặn: BLOCKED_MARKERS phát hiện Cloudflare/captcha
     • 4 kỹ thuật trích xuất: JSON-LD parsing, __NEXT_DATA__, BeautifulSoup HTML, API JSON
     • Lưu raw: CSV + JSON theo site (data/raw/), log source_metadata

2.2. Quy trình Chuẩn hóa và Làm sạch Dữ liệu
     2.2.1. Chuẩn hóa Lương (SalaryParser)
            • 8 SalaryType (RANGE, UP_TO, FROM, YEARLY, USD, HIDDEN, SINGLE, UNKNOWN)
            • 6 nhóm regex; USD→VND ×25.000; lương năm ÷12; UP_TO mid=70% max; FROM mid=130% min
            • HIDDEN: 24+ từ khóa (cạnh tranh, thỏa thuận, negotiable...) → 56% tin ẩn lương
     2.2.2. Chuẩn hóa Kỹ năng (SkillNormalizer)
            • 188 quy tắc đồng nghĩa → 45 tên chuẩn; 12 nhóm kỹ năng
            • Fuzzy matching (difflib SequenceMatcher) ngưỡng > 0.8
            • Độ phủ thực tế 6.6% — giới hạn nguồn hiển thị
     2.2.3. Chuẩn hóa Kinh nghiệm (ExperienceNormalizer)
            • 6 nhóm regex (range, from, up-to, exact, zero/fresher)
            • 5 bậc: entry (0-1), junior (1-3), mid (3-5), senior (5-8), lead (8+)
            • Fallback: parse từ description_raw nếu thiếu
     2.2.4. Khử Trùng lặp (Deduplicator)
            • 4 pha: exact job_id; exact title+company; fuzzy title ≥0.8; fuzzy description ≥0.7
            • Kết quả: loại 70 bản ghi trùng

2.3. Xây dựng Đặc trưng và Tiền xử lý cho Học máy
     • 3 nhóm đặc trưng:
       - numeric: experience_years → SimpleImputer(median) + StandardScaler
       - categorical: city, job_type, remote_option, education_level, industry, company_size
         → SimpleImputer("Unknown") + OneHotEncoder(handle_unknown="ignore")
       - ordinal: experience_bin (entry→lead) → SimpleImputer("unknown") + OrdinalEncoder(unknown_value=-1)
     • Target: salary_mid (triệu VND/tháng)
     • Drop cột raw: job_id, company_id, job_title, description, source_url...
     • ColumnTransformer(remainder="drop")

2.4. Tổng quan Dữ liệu sau Xử lý
     • 1.193 bản ghi, 44 thuộc tính, 4 nguồn
     • Bảng thống kê: Thuộc tính | Giá trị (7 dòng)
     • Chia train/test 80/20 (stratify experience_bin) + 5-fold CV
```

**Mỗi mục con 2.2.x giữ format:** tiêu đề bold 13pt + body 12pt (khớp `insert_content_after_paragraph`).

## 3. Bảng thống kê 2.4

```python
CH2_STATS_TABLE = [
    ["Thuộc tính", "Giá trị"],
    ["Tổng bản ghi việc làm", "1.193"],
    ["Số thuộc tính (cột)", "44"],
    ["Nguồn dữ liệu", "Itviec, Glints, TopCV, Careerviet"],
    ["Tỷ lệ ẩn lương", "56%"],
    ["Độ phủ kỹ năng chi tiết", "6.6%"],
    ["Bản ghi trùng đã loại", "70"],
]
```

- Marker trong sub_title: `"__TABLE_CH2__"` → `insert_content_after_paragraph` phát hiện và gọi `insert_table_after_paragraph(new_p_body, CH2_STATS_TABLE)`.
- Style: Table Grid, Times New Roman 11pt, header bold, canh giữa (đồng nhất bảng ML).

## 4. Trích dẫn

Tái sử dụng `REFERENCES` (10 mục đã có):
- [9] McKinney — Pandas/data pipeline (2.2)
- [3] scikit-learn docs — ColumnTransformer/OneHot/Ordinal (2.3)
- [1] Géron — pipeline tổng quan, feature engineering (2.3)
- [10] BeautifulSoup — trích xuất HTML (2.1)

Không thêm mục tài liệu mới.

## 5. Verify mở rộng

Thêm key_phrases: `"22 keyword"`, `"BLOCKED_MARKERS"`, `"2.2.1"`, `"2.2.4"`, `"ColumnTransformer"`, `"handle_unknown"`, `"80/20"`, `"OrdinalEncoder"`.
Giữ nguyên mọi checks cũ (headings, phrases chương 1, ML table, refs ≥ 10, không còn resnet50).

## 6. Non-goals

- Không đổi chương 1, 3, LỜI MỞ ĐẦU, KẾT LUẬN.
- Không thêm thư viện mới.
- Không tách module, không đổi cơ chế chèn/verify hiện tại.
