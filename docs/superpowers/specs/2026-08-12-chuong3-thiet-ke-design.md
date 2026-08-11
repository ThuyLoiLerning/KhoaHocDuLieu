# Thiết kế: Mở rộng Chương 3 — Quả thực nghiệm và Đánh giá

**Ngày:** 2026-08-12
**Phạm vi:** `scripts/generate_docx_report.py` — mở rộng nội dung Chương 3 của báo cáo Word (EDA, trả lời RQ, supervised, K-Means, recommendation) theo kết quả thực nghiệm thật trong `reports/final_report.md` và code `src/ml/`.

## 1. Vấn đề

Chương 3 ("QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ") hiện chỉ có 4 mục 1-đoạn:

- `3.1. Phân tích Khám phá Dữ liệu (EDA) và Trả lời Câu hỏi Nghiên cứu` — 1 đoạn liệt kê F1-F4
- `3.2. Kết quả Đánh giá Mô hình Dự báo Lương` — 1 đoạn + bảng ML
- `3.3. Phân cụm Thị trường (K-Means)` — 1 đoạn
- `3.4. Hệ thống Gợi ý Việc làm` — 1 đoạn

Yêu cầu: chi tiết hóa theo kết quả thật, thêm bảng, trích dẫn học thuật, làm rõ số liệu.

## 2. Cấu trúc nội dung Chương 3 mới (5 mục, đã duyệt)

```
3.1. Phân tích Khám phá Dữ liệu (EDA)
     • Giữ nội dung hiện có, mở rộng F1-F4:
       F1: kỹ năng top — JavaScript, React, Kafka, Python, SQL, Docker,
           Spring Boot, TensorFlow; nhóm Data Science & Lập trình dẫn đầu
       F2: lương theo kinh nghiệm Entry ~10M → Lead ~35M+;
           HCMC & Hà Nội cao hơn rõ rệt
       F3: yêu cầu tiếng Anh → lương TB cao hơn 30%
       F4: Senior/Manager/Lead ẩn lương >50%
     • Trích dẫn [9] McKinney

3.2. Trả lời các Câu hỏi Nghiên cứu (RQ1-RQ5)
     • Mục mới: bảng ánh xạ RQ → câu trả lời → minh chứng
       RQ1: top kỹ năng → F1; RQ2: lương theo kinh nghiệm/thành phố → F2;
       RQ3: tiếng Anh → F3; RQ4: ẩn lương → F4; RQ5: gợi ý việc làm → 3.5
     • Bảng 6 dòng × 3 cột: "Câu hỏi nghiên cứu | Trả lời | Minh chứng"

3.3. Kết quả Đánh giá Mô hình Dự báo Lương (Supervised Models)
     • Mô tả pipeline: ColumnTransformer (numeric: Median Imputer + StandardScaler;
       categorical: SimpleImputer "Unknown" + OneHotEncoder handle_unknown="ignore";
       ordinal: SimpleImputer "unknown" + OrdinalEncoder unknown_value=-1) [3]
     • Bảng ML hiện có giữ nguyên (4 model × 4 cột)
     • Đoạn phân tích từng model:
       - Baseline (DummyMean): RMSE 8.97, MAE 7.36, R² -0.010 — mốc so sánh
       - Linear Regression: RMSE 4.17, MAE 2.94, R² 0.783 — cải thiện 53.5% so
         với baseline; dễ diễn giải (interpretable)
       - Decision Tree (max_depth=8, min_samples_leaf=5): RMSE 0.60, MAE 0.18,
         R² 0.996 — cải thiện 93.3% [5]
       - Random Forest (n_estimators=100, max_depth=15, min_samples_leaf=4):
         RMSE ≈ 0, R² ≈ 1 — dấu hiệu overfit trên tập dữ liệu hiện tại [4]
     • Đoạn Error Analysis: 12 trường hợp sai số lớn nhất có residual < 2.1M;
       over/under predict cân bằng; residual mean ≈ 0, std ≈ 0.6M
     • Nhận định: DT/RF đạt chỉ số gần tối ưu — cần dữ liệu đa dạng hơn để
       đánh giá tổng quát; thận trọng khi diễn giải

3.4. Phân cụm Thị trường (K-Means Clustering)
     • Cấu hình: features (experience_years, salary_mid, city, remote_option,
       skills); StandardScaler; PCA(n_components=2) trực quan hóa; khảo sát
       k=2..10; chọn k=10 với Silhouette Score 0.38 [7]; n_init=10,
       random_state=42 [6]
     • Bảng profile 5 phân khúc tiêu biểu (cluster 0/1/4/8/9):
       "Cluster | Tỷ lệ | Lương TB | Kinh nghiệm TB | Đặc điểm"
       - 0: 21% | 15.1M | 2.6y | Junior-Mid, Hà Nội
       - 1: 14% | 27.1M | 2.6y | Mid-Senior, TP.HCM
       - 4: 10% | 41.9M | 4.8y | Senior, thu nhập cao
       - 8: 21% | 20.8M | 2.1y | Mid, đa dạng
       - 9: 4%  | 31.6M | 2.7y | Việc làm Remote

3.5. Hệ thống Gợi ý Việc làm (Content-Based Recommendation)
     • Cơ chế: MultiLabelBinarizer → ma trận job×skill (1500 việc × 45 kỹ năng);
       cosine similarity [1]; bộ lọc thành phố (case-insensitive) + kinh nghiệm
       ±0.5 năm (fallback experience_bin) [8]
     • Demo: user_skills = [Python, SQL, Machine Learning] → Top gợi ý:
       Data Scientist, ML Engineer, Data Engineer
     • Bảng Top-N: 3 việc làm top (Data Scientist, ML Engineer, Data Engineer)
       | Similarity | Kỹ năng khớp | Kỹ năng thiếu — similarity/matched/missing
       là giá trị minh họa từ demo
```

## 3. Bảng mới (3 bảng, style Table Grid — đồng nhất bảng ML hiện có)

| # | Mục | Tên | Số dòng | Cột |
|---|-----|-----|---------|-----|
| 1 | 3.2 | Bảng ánh xạ RQ | 6 (header + 5 RQ) | Câu hỏi nghiên cứu / Trả lời / Minh chứng |
| 2 | 3.4 | Bảng profile cluster | 6 (header + 5) | Cluster / Tỷ lệ / Lương TB / Kinh nghiệm TB / Đặc điểm |
| 3 | 3.5 | Bảng Top-N | 4 (header + 3 top) | Việc làm / Similarity / Kỹ năng khớp / Kỹ năng thiếu |

- Marker: `__TABLE_CH3_RQ__`, `__TABLE_CH3_CLUSTER__`, `__TABLE_CH3_REC__` trong
  sub_title → `insert_content_after_paragraph` phát hiện và gọi
  `insert_table_after_paragraph` với bảng tương ứng.
- Font Times New Roman 11pt, header bold, canh giữa.

## 4. Trích dẫn

Tái sử dụng `REFERENCES` (10 mục đã có), không thêm mục mới:
- [9] McKinney — EDA/pandas (3.1)
- [3] scikit-learn — ColumnTransformer/preprocessing (3.3)
- [5] Quinlan — Decision Tree (3.3)
- [4] Breiman — Random Forest (3.3)
- [6] MacQueen — K-Means (3.4)
- [7] Rousseeuw — Silhouette (3.4)
- [8] Ricci — Recommender Systems (3.5)
- [1] Géron — cosine similarity / ML tổng quan (3.5)

## 5. Verify mở rộng (`verify_report()`)

Thêm key_phrases: `"3.2"`, `"RQ1"`, `"Error Analysis"`, `"phân tích sai số"`,
`"0.38"`, `"k=10"`, `"1500"`, `"45 kỹ năng"`, `"Top-N"`, `"53.5%"`, `"93.3%"`,
`"[4]"`, `"[5]"`, `"[6]"`, `"[7]"`, `"[8]"`.

Giữ nguyên mọi checks cũ (5 headings, 12 phrases chương 1, 8 phrases chương 2,
ML table, refs ≥ 10, không còn resnet50/rác thải, TOC cũ sạch).

## 6. Non-goals

- Chương 1, 2, LỜI MỞ ĐẦU, KẾT LUẬN, TÀI LIỆU THAM KHẢO: giữ nguyên.
  (Chương 1 vẫn ghi "k=5" — không đồng bộ sang k=10 trong phạm vi này.)
- Không thêm thư viện mới, không tách module, không đổi cơ chế chèn/verify.
