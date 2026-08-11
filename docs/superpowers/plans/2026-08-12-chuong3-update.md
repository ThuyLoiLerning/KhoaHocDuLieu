# Chương 3 — Chi Tiết Hóa Nội Dung Quả Thực Nghiệm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mở rộng Chương 3 trong `scripts/generate_docx_report.py` từ 4 mục 1-đoạn thành 5 mục chi tiết với 3 bảng mới, trích dẫn [4]-[8], và verify mở rộng.

**Architecture:** Sửa 1 file `scripts/generate_docx_report.py` theo pattern đã có từ chương 1-2: thêm constants bảng mới (CH3_RQ/CLUSTER/REC_TABLE), thay nội dung FULL_CONTENT["CHƯƠNG 3..."], thêm marker `__TABLE_CH3_*__` trong `insert_content_after_paragraph`, mở rộng key_phrases trong `verify_report`. Sau đó chạy script — `verify_report()` là bước kiểm nghiệm.

**Tech Stack:** python-docx, Python 3 (không thêm thư viện mới).

## Global Constraints

- Chỉ sửa `scripts/generate_docx_report.py`. Không tách module, không thêm thư viện.
- Chương 1, 2, LỜI MỞ ĐẦU, KẾT LUẬN, TÀI LIỆU THAM KHẢO: giữ nguyên nội dung.
- Số liệu lấy từ `reports/final_report.md`: Baseline RMSE 8.97/MAE 7.36/R² -0.010; Linear 4.17/2.94/0.783 (+53.5%); DT 0.60/0.18/0.996 (+93.3%, max_depth=8, min_samples_leaf=5); RF ≈0/≈0/~1.0; error analysis 12 worst < 2.1M, residual mean ≈ 0, std ≈ 0.6M; silhouette 0.38 (k=10); matrix 1500×45; demo [Python, SQL, Machine Learning] → DS/ML Engineer/Data Engineer.
- Chạy mọi lệnh Python với `PYTHONIOENCODING=utf-8` (Windows cp1252 sẽ lỗi Unicode).
- Bảng Top-N (3.5): similarity/matched/missing là giá trị minh họa từ demo (spec §2).

---

### Task 1: Thêm 3 bảng Chương 3 (constants)

**Files:**
- Modify: `scripts/generate_docx_report.py` — thêm sau `CH2_STATS_TABLE` (dòng ~136)

**Interfaces:**
- Produces: `CH3_RQ_TABLE` (6×3), `CH3_CLUSTER_TABLE` (6×5), `CH3_REC_TABLE` (4×4) — list-of-lists, dòng đầu là header. Task 3 đọc các constant này theo tên.

- [ ] **Step 1: Chèn 3 bảng mới sau block CH2_STATS_TABLE**

Sau khối `CH2_STATS_TABLE = [...]` (kết thúc dòng 136), chèn:

```python
# Bảng ánh xạ câu hỏi nghiên cứu (chương 3, mục 3.2)
CH3_RQ_TABLE = [
    ["Câu hỏi nghiên cứu", "Trả lời", "Minh chứng"],
    ["RQ1: Kỹ năng nào được yêu cầu nhiều nhất?",
     "JavaScript, React, Kafka, Python, SQL, Docker, Spring Boot, TensorFlow", "F1 (EDA)"],
    ["RQ2: Kinh nghiệm và thành phố ảnh hưởng lương thế nào?",
     "Lương tăng theo bậc kinh nghiệm (Entry ~10M → Lead ~35M+); TP.HCM & Hà Nội cao hơn rõ rệt", "F2 (EDA)"],
    ["RQ3: Yêu cầu tiếng Anh ảnh hưởng lương?",
     "Lương trung bình cao hơn 30%", "F3 (EDA)"],
    ["RQ4: Tỷ lệ ẩn lương phổ biến ở đâu?",
     "Vị trí cấp cao (Senior, Manager, Lead) ẩn lương >50%", "F4 (EDA)"],
    ["RQ5: Việc nào phù hợp với hồ sơ kỹ năng?",
     "Top-N việc có độ tương đồng cosine cao nhất, kèm kỹ năng còn thiếu", "Mục 3.5"],
]

# Bảng profile 5 phân khúc tiêu biểu (chương 3, mục 3.4)
CH3_CLUSTER_TABLE = [
    ["Cluster", "Tỷ lệ", "Lương TB", "Kinh nghiệm TB", "Đặc điểm"],
    ["0", "21%", "15.1M", "2.6y", "Junior-Mid, Hà Nội"],
    ["1", "14%", "27.1M", "2.6y", "Mid-Senior, TP.HCM"],
    ["4", "10%", "41.9M", "4.8y", "Senior, thu nhập cao"],
    ["8", "21%", "20.8M", "2.1y", "Mid, đa dạng"],
    ["9", "4%", "31.6M", "2.7y", "Việc làm Remote"],
]

# Bảng Top-3 gợi ý việc làm (chương 3, mục 3.5) — minh họa từ demo
CH3_REC_TABLE = [
    ["Việc làm", "Similarity", "Kỹ năng khớp", "Kỹ năng thiếu"],
    ["Data Scientist", "1.0", "Python, SQL, Machine Learning", "—"],
    ["ML Engineer", "0.67", "Python, Machine Learning", "Docker, Spark"],
    ["Data Engineer", "0.67", "Python, SQL", "Spark, Airflow"],
]
```

- [ ] **Step 2: Xác minh không lỗi cú pháp**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python -c "import ast; ast.parse(open('scripts/generate_docx_report.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat(ch3): add CH3 tables — RQ mapping, cluster profiles, top-3 rec"
```

---

### Task 2: Thay nội dung FULL_CONTENT Chương 3 (5 mục + markers)

**Files:**
- Modify: `scripts/generate_docx_report.py:99-108` — thay toàn bộ list `"CHƯƠNG 3 QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ": [...]`

**Interfaces:**
- Consumes: `CH3_RQ_TABLE`, `CH3_CLUSTER_TABLE`, `CH3_REC_TABLE` (Task 1)
- Produces: content_list 9 phần tử cho `insert_content_after_paragraph`; marker `__TABLE_CH3_RQ__`, `__TABLE_CH3_CLUSTER__`, `__TABLE_CH3_REC__` (Task 3 xử lý); sub_title "3.3. Kết quả Đánh giá Mô hình Dự báo Lương (Supervised Models)" (Task 3 dùng cho ML table check)

- [ ] **Step 1: Thay list chương 3 cũ (dòng 99-108)**

Thay toàn bộ khối:

```python
    "CHƯƠNG 3 QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ": [
        ("3.1. Phân tích Khám phá Dữ liệu (EDA) và Trả lời Câu hỏi Nghiên cứu",
         "Thông qua các biểu đồ phân tích (EDA), đề tài đã giải quyết các câu hỏi nghiên cứu quan trọng:\n• F1 - Phân bố Kỹ năng: Nhóm kỹ năng Data Science & Lập trình chiếm tỷ trọng hàng đầu. Top các kỹ năng được yêu cầu nhiều nhất gồm: JavaScript, React, Kafka, Python, SQL, Docker, Spring Boot, TensorFlow.\n• F2 - Tương quan Lương theo Kinh nghiệm & Thành phố: Mức lương trung bình tăng dần theo cấp bậc kinh nghiệm (Entry: ~10M, Lead: ~35M+). Khu vực TP.HCM và Hà Nội có mức lương trung bình cao hơn rõ rệt.\n• F3 - Yếu tố Tiếng Anh: Tin tuyển dụng có yêu cầu tiếng Anh ghi nhận mức lương trung bình cao hơn 30%.\n• F4 - Tỷ lệ Ẩn lương: Các vị trí cấp cao (Senior, Manager, Lead) có tỷ lệ không công khai mức lương vượt mức 50%."),
        ("3.2. Kết quả Đánh giá Mô hình Dự báo Lương (Supervised Models)",
         "Pipeline biến đổi đặc trưng (ColumnTransformer) thực hiện Median Imputer & Scaling, One-Hot Encoding, Ordinal Encoding. Kết quả đánh giá trên tập Test (chia 80/20) được trình bày trong bảng dưới đây:"),
        ("3.3. Phân cụm Thị trường (K-Means Clustering)",
         "Áp dụng K-Means với k=5 (Silhouette Score = 0.38) cho phép phân nhóm thị trường thành 5 phân khúc chính: Nhóm Junior-Mid tại Hà Nội (Lương TB: 15.1M), Mid-Senior tại TP.HCM (27.1M), Chuyên gia/Senior thu nhập cao (41.9M), công việc phổ thông (20.8M) và việc làm Remote (31.6M)."),
        ("3.4. Hệ thống Gợi ý Việc làm (Content-Based Recommendation)",
         "Hệ thống Content-based Recommendation sử dụng MultiLabelBinarizer và Cosine Similarity. Khi ứng viên cung cấp danh mục kỹ năng, hệ thống phản hồi Top-N vị trí phù hợp nhất, kèm theo chỉ số Similarity Score và danh sách kỹ năng còn thiếu.")
    ],
```

bằng:

```python
    "CHƯƠNG 3 QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ": [
        ("3.1. Phân tích Khám phá Dữ liệu (EDA)",
         "Thông qua các biểu đồ phân tích (EDA), đề tài đã khảo sát cấu trúc và đặc điểm của bộ dữ liệu gồm 1.193 tin tuyển dụng với 44 thuộc tính [9]. Các phát hiện chính được tổng hợp theo từng nhóm nội dung:\n• F1 - Phân bố Kỹ năng: Nhóm kỹ năng Data Science & Lập trình chiếm tỷ trọng hàng đầu. Top các kỹ năng được yêu cầu nhiều nhất gồm: JavaScript, React, Kafka, Python, SQL, Docker, Spring Boot, TensorFlow.\n• F2 - Tương quan Lương theo Kinh nghiệm & Thành phố: Mức lương trung bình tăng dần theo cấp bậc kinh nghiệm (Entry: ~10M, Lead: ~35M+). Khu vực TP.HCM và Hà Nội có mức lương trung bình cao hơn rõ rệt.\n• F3 - Yếu tố Tiếng Anh: Tin tuyển dụng có yêu cầu tiếng Anh ghi nhận mức lương trung bình cao hơn 30%.\n• F4 - Tỷ lệ Ẩn lương: Các vị trí cấp cao (Senior, Manager, Lead) có tỷ lệ không công khai mức lương vượt mức 50%."),
        ("3.2. Trả lời các Câu hỏi Nghiên cứu",
         "Từ các kết quả EDA, đề tài đối chiếu với 5 câu hỏi nghiên cứu RQ1-RQ5 đã nêu ở Chương 1. Bảng dưới đây tóm tắt câu trả lời và minh chứng tương ứng cho từng câu hỏi:"),
        ("__TABLE_CH3_RQ__ Bảng ánh xạ câu hỏi nghiên cứu", ""),
        ("3.3. Kết quả Đánh giá Mô hình Dự báo Lương (Supervised Models)",
         "Pipeline biến đổi đặc trưng (ColumnTransformer) thực hiện Median Imputer & Scaling cho nhóm số, One-Hot Encoding cho nhóm phân loại và Ordinal Encoding cho bậc kinh nghiệm [3]. Toàn bộ mô hình được đánh giá trên tập kiểm tra (chia 80/20), kết quả được trình bày trong bảng dưới đây:"),
        ("",
         "Phân tích từng mô hình:\n• Baseline (Dummy Mean): RMSE 8.97, MAE 7.36, R² -0.010 — dự đoán hằng số bằng giá trị trung bình, là mốc so sánh cho các mô hình phức tạp hơn.\n• Linear Regression: RMSE 4.17, MAE 2.94, R² 0.783 — cải thiện 53.5% RMSE so với baseline; quan hệ lương-kỹ năng phi tuyến khiến sai số còn đáng kể.\n• Decision Tree (max_depth=8, min_samples_leaf=5): RMSE 0.60, MAE 0.18, R² 0.996 — cải thiện 93.3% so với baseline [5]; cây quyết định nắm bắt tốt các quy luật cục bộ của dữ liệu.\n• Random Forest (n_estimators=100, max_depth=15, min_samples_leaf=4): RMSE ≈ 0, R² ≈ 1 — tập hợp 100 cây cho kết quả gần như hoàn hảo trên tập kiểm tra, là dấu hiệu overfit mạnh do độ đa dạng dữ liệu thấp [4]."),
        ("",
         "Phân tích sai số (Error Analysis): 12 trường hợp dự đoán sai lớn nhất đều có sai số tuyệt đối dưới 2.1 triệu đồng; phân bố over/under predict cân bằng với residual mean ≈ 0 và độ lệch chuẩn ≈ 0.6 triệu [2]. Các mô hình cây đạt chỉ số gần tối ưu trên tập dữ liệu hiện tại; cần thu thập thêm dữ liệu đa dạng hơn (nhiều thành phố, nhiều ngành) để đánh giá khả năng tổng quát hóa."),
        ("3.4. Phân cụm Thị trường (K-Means Clustering)",
         "Phân cụm được thực hiện trên các đặc trưng lương trung bình, số năm kinh nghiệm, thành phố, hình thức làm việc (remote) và kỹ năng; dữ liệu được chuẩn hóa bằng StandardScaler và trực quan hóa qua PCA với 2 thành phần chính [6]. Tiến hành khảo sát số cụm k từ 2 đến 10, cấu hình k=10 đạt Silhouette Score cao nhất 0.38, cho phép phân chia thị trường thành các phân khúc rõ rệt [7]. Bảng dưới đây mô tả 5 phân khúc tiêu biểu nhất:"),
        ("__TABLE_CH3_CLUSTER__ Bảng profile 5 phân khúc tiêu biểu", ""),
        ("3.5. Hệ thống Gợi ý Việc làm (Content-Based Recommendation)",
         "Hệ thống xây dựng ma trận nhị phân việc làm × kỹ năng (1500 việc × 45 kỹ năng) bằng MultiLabelBinarizer, sau đó tính độ tương đồng cosine giữa hồ sơ kỹ năng ứng viên và từng tin tuyển dụng [1]. Kết quả được lọc theo thành phố (không phân biệt hoa/thường) và khung kinh nghiệm ±0.5 năm (hoặc bậc kinh nghiệm tương đương khi thiếu số liệu) trước khi chọn Top-N phù hợp nhất [8]. Với hồ sơ mẫu user_skills = [Python, SQL, Machine Learning], hệ thống gợi ý các vị trí Data Scientist, ML Engineer và Data Engineer. Kết quả Top-3 được trình bày trong bảng dưới đây, kèm danh sách kỹ năng khớp và kỹ năng ứng viên còn thiếu để định hướng bổ sung:"),
        ("__TABLE_CH3_REC__ Bảng Top-3 gợi ý việc làm", ""),
    ],
```

- [ ] **Step 2: Xác minh cú pháp**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python -c "import ast; ast.parse(open('scripts/generate_docx_report.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat(ch3): replace chapter 3 content — 5 sections + RQ/cluster/rec markers"
```

---

### Task 3: Xử lý marker `__TABLE_CH3_*__` + chuyển ML table sang 3.3

**Files:**
- Modify: `scripts/generate_docx_report.py:372-378` — block check bảng trong `insert_content_after_paragraph`

**Interfaces:**
- Consumes: markers từ Task 2, `CH3_RQ_TABLE`/`CH3_CLUSTER_TABLE`/`CH3_REC_TABLE` từ Task 1, hàm `insert_table_after_paragraph(new_p_body, data)` có sẵn
- Produces: 3 bảng mới chèn sau body paragraph; ML_RESULTS_TABLE chèn ở 3.3 thay vì 3.2

- [ ] **Step 1: Đổi check ML table từ "3.2" sang "3.3" + thêm 3 check marker**

Thay khối (dòng 372-378):

```python
        if "3.2. Kết quả Đánh giá Mô hình Dự báo Lương" in sub_title:
            print("    [Table] Inserting ML results table...")
            insert_table_after_paragraph(new_p_body, ML_RESULTS_TABLE)

        if sub_title.startswith('__TABLE_CH2__'):
            print("    [Table] Inserting chapter-2 stats table...")
            insert_table_after_paragraph(new_p_body, CH2_STATS_TABLE)
```

bằng:

```python
        if "3.3. Kết quả Đánh giá Mô hình Dự báo Lương" in sub_title:
            print("    [Table] Inserting ML results table...")
            insert_table_after_paragraph(new_p_body, ML_RESULTS_TABLE)

        if sub_title.startswith('__TABLE_CH2__'):
            print("    [Table] Inserting chapter-2 stats table...")
            insert_table_after_paragraph(new_p_body, CH2_STATS_TABLE)

        if sub_title.startswith('__TABLE_CH3_RQ__'):
            print("    [Table] Inserting chapter-3 RQ mapping table...")
            insert_table_after_paragraph(new_p_body, CH3_RQ_TABLE)

        if sub_title.startswith('__TABLE_CH3_CLUSTER__'):
            print("    [Table] Inserting chapter-3 cluster profile table...")
            insert_table_after_paragraph(new_p_body, CH3_CLUSTER_TABLE)

        if sub_title.startswith('__TABLE_CH3_REC__'):
            print("    [Table] Inserting chapter-3 top-N rec table...")
            insert_table_after_paragraph(new_p_body, CH3_REC_TABLE)
```

- [ ] **Step 2: Xác minh cú pháp**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python -c "import ast; ast.parse(open('scripts/generate_docx_report.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat(ch3): handle __TABLE_CH3_*__ markers, move ML table to 3.3"
```

---

### Task 4: Mở rộng verify_report — key_phrases chương 3

**Files:**
- Modify: `scripts/generate_docx_report.py:405-426` — list `key_phrases`

**Interfaces:**
- Consumes: nội dung chương 3 mới (Task 2)
- Produces: verify_report() trả True chỉ khi mọi phrase chương 3 có trong file xuất

- [ ] **Step 1: Thêm 16 phrase chương 3 vào cuối list key_phrases**

Thay list `key_phrases = [...]` (dòng 405-426) bằng list cũ + 16 mục mới ở cuối:

```python
        "80/20",
        "3.2",
        "RQ1",
        "Error Analysis",
        "phân tích sai số",
        "0.38",
        "k=10",
        "1500",
        "45 kỹ năng",
        "Top-N",
        "53.5%",
        "93.3%",
        "[4]",
        "[5]",
        "[6]",
        "[7]",
        "[8]"
    ]
```

- [ ] **Step 2: Chạy script tổng thể — phải PASSED**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python scripts/generate_docx_report.py 2>&1 | tail -20`
Expected: dòng cuối `VERIFICATION PASSED: Báo cáo đã được làm sạch và cập nhật hoàn hảo!` và `Old TOC entries remaining: 0`.

Nếu FAILED: đọc danh sách issue, sửa nội dung tương ứng (kiểm tra chính tả phrase đúng với text chèn), chạy lại.

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat(ch3): extend verify — RQ1, k=10, 53.5%, [4]-[8] key phrases"
```

---

### Task 5: Kiểm chứng file xuất (bảng + cấu trúc) và hoàn tất

**Files:**
- Test: `reports/BaoCao_MonHoc_NguyenMinhTan_Complete.docx` (output của Task 4)

- [ ] **Step 1: Đếm bảng + kiểm tra 3 bảng mới tồn tại**

Run:
```bash
cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python -c "
import docx
d = docx.Document('reports/BaoCao_MonHoc_NguyenMinhTan_Complete.docx')
print('tables:', len(d.tables))
for t in d.tables:
    print(len(t.rows), 'x', len(t.columns), '|', t.rows[0].cells[0].text)
h1 = [p.text for p in d.paragraphs if p.style.name == 'Heading 1']
print('H1 count:', len(h1))
for h in h1: print(' -', h)
"
```
Expected: `tables: 6` (cover 1×2, CH2 7×2, ML 5×4, CH3_RQ 6×3, CH3_CLUSTER 6×5, CH3_REC 4×4); header đầu mỗi bảng hiển thị; `H1 count: 6` (5 chương + TÀI LIỆU THAM THẢO).

- [ ] **Step 2: Xác minh heading chương 3 mới**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python -c "
import docx
d = docx.Document('reports/BaoCao_MonHoc_NguyenMinhTan_Complete.docx')
for p in d.paragraphs:
    t = p.text.strip()
    if t.startswith('3.') and len(t) < 60:
        print(' -', t)
"
`
Expected: 5 dòng `3.1.` … `3.5.` đúng thứ tự, không còn "3.1. ... và Trả lời" hay "3.4. Hệ thống Gợi ý Việc làm" đứng sau mục 3.2 (thứ tự cũ 3.3→3.4 bị đổi tên).

- [ ] **Step 3: Báo cáo hoàn tất cho người dùng**

Nhắc: TOC trong Word là bản cũ — mở file, References → Update Table để refresh.

**Skipped:** không có — spec yêu cầu 3 bảng, verify mở rộng, không đổi chương khác, đều đủ trong 4 task. Thêm khi cần: đồng bộ "k=5"→"k=10" ở chương 1 (ngoài phạm vi, spec §6).
