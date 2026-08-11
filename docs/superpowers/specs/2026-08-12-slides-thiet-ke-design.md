# Thiết kế: Bộ Slide Thuyết Trình 15 Trang (PPTX) — Chuyên đề 4

**Ngày:** 2026-08-12
**Phạm vi:** Script mới `scripts/generate_pptx_slides.py` sinh `reports/slides/TrinhBay_ChuyenDe4.pptx` (python-pptx, nền tối hiện đại) — trình bày toàn bộ nội dung báo cáo: solution + thực nghiệm kết quả.

## 1. Vấn đề

Slide cũ `reports/slides/slide_deck.md` là markdown với nội dung cũ (F1-F6, nguồn kế hoạch cũ: vietnamworks/topdev), chưa khớp báo cáo mới (RQ1-RQ5, crawler v2, k=10, kết quả ML thật).

Yêu cầu: bộ slide PPTX thật ~15 trang, phong cách tối hiện đại, trình bày toàn bộ nội dung đã làm trong báo cáo — gồm solution và thực nghiệm kết quả.

## 2. Phong cách (đã duyệt: tối hiện đại)

- Nền tối xám đen `#1E1E2E`, chữ trắng `#FFFFFF`, accent xanh cyan `#00BCD4`.
- Tiêu đề 28-32pt bold cyan; nội dung 16-18pt trắng; bảng nền tối viền cyan.
- Kích thước 16:9 (13.33 × 7.5 in), font Calibri.

## 3. Cấu trúc 15 slide (đã duyệt)

| # | Slide | Nội dung |
|---|-------|----------|
| 1 | Bìa | Tên đề tài, Chuyên đề 4, nhóm, GVHD, ngày |
| 2 | Giới thiệu bài toán | Bối cảnh IT VN, nghịch lý cung-cầu, mục tiêu |
| 3 | Câu hỏi nghiên cứu | RQ1-RQ5 (bảng: câu hỏi → phương pháp) |
| 4 | Kiến trúc hệ thống | Pipeline end-to-end: crawl → clean → features → ML → rec |
| 5 | Crawler v2 | 4 nguồn, 22 keyword, HttpClient (UA rotation, rate-limit 1-3s, retry 429), BLOCKED_MARKERS, 4 kỹ thuật trích xuất (JSON-LD, __NEXT_DATA__, BS4, API), raw CSV+JSON |
| 6 | Cleaning | SalaryParser (8 type, USD→VND ×25000, 56% ẩn), SkillNormalizer (188→45, fuzzy >0.8), ExperienceNormalizer (5 bậc), Deduplicator (4 pha, loại 70) |
| 7 | Feature Engineering | ColumnTransformer 3 nhóm (numeric median+scaler, categorical OHE handle_unknown, ordinal OrdinalEncoder -1), target salary_mid, 80/20 + 5-fold CV |
| 8 | Dữ liệu tổng quan | Bảng thống kê: 1.193 tin, 44 cột, 4 nguồn, 56% ẩn lương, 6.6% skills, 70 trùng |
| 9 | EDA | F1-F4: kỹ năng top (JS, React, Python...), lương theo exp/city (Entry 10M → Lead 35M+), tiếng Anh +30%, ẩn lương cấp cao >50% |
| 10 | Kết quả Supervised | Bảng ML (Baseline 8.97/-0.010, Linear 4.17/0.783 +53.5%, DT 0.60/0.996 +93.3%, RF ~0/~1) + error analysis (12 worst <2.1M, residual mean≈0) + nhận định overfit |
| 11 | K-Means | k=10, silhouette 0.38, bảng 5 phân khúc (15.1M, 27.1M, 41.9M, 20.8M, 31.6M) |
| 12 | Recommendation | MLB 1500×45, cosine similarity, lọc city/exp, demo user_skills → Top-3 (DS, ML Eng, Data Eng) |
| 13 | Kết luận | Tóm tắt kết quả đạt được: 3 nhóm ML, RQ1-RQ5 trả lời đầy đủ |
| 14 | Hạn chế & Hướng phát triển | 6.6% skills, thiên lệch TP.HCM/Đà Nẵng, overfit; crawler sâu, NLP/BERT, DBSCAN, Hybrid Rec |
| 15 | Cảm ơn | Q&A |

## 4. Kỹ thuật

- Script mới `scripts/generate_pptx_slides.py` dùng python-pptx (đã cài 1.0.2).
- Helpers:
  - `add_title_slide(prs, title, subtitle, ...)` — bìa
  - `add_content_slide(prs, title, bullets)` — bullet list (level, accent cho level 0)
  - `add_table_slide(prs, title, data, col_widths=None)` — bảng viền cyan, header bold
  - `new_slide(prs)` — blank slide nền tối
- Bảng dữ liệu tái sử dụng nội dung từ `generate_docx_report.py` (ML_RESULTS_TABLE, CH2_STATS_TABLE, CH3_CLUSTER_TABLE, CH3_REC_TABLE) — copy trực tiếp vào script slide (không import để tránh chạy code docx).
- Output: `reports/slides/TrinhBay_ChuyenDe4.pptx`.

## 5. Verify

- Đếm slide = 15.
- Mỗi slide có title (trừ slide bìa/cảm ơn có title riêng).
- Slide 10 có bảng ML 5×4, slide 8 có bảng thống kê 7×2, slide 11 có bảng cluster 6×5.
- Các số liệu chính xuất hiện: 1.193, 4.17, 0.38, 1500, 56%, 6.6%.

## 6. Non-goals

- Không dùng template pptx sẵn, không ảnh/icon, không animation.
- Không sửa `generate_docx_report.py` (chỉ thêm file mới).
- Không tạo PDF/export (user tự làm trong PowerPoint).
- requirements.txt: thêm `python-pptx>=1.0`.
