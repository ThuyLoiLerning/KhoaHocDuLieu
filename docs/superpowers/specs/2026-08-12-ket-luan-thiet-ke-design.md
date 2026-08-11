# Thiết kế: Mở rộng Phần KẾT LUẬN — Kết luận, Hạn chế, Hướng phát triển

**Ngày:** 2026-08-12
**Phạm vi:** `scripts/generate_docx_report.py` — mở rộng nội dung phần KẾT LUẬN của báo cáo Word (3 mục, mỗi mục 2-3 đoạn), thêm trích dẫn [1], [8], mở rộng verify.

## 1. Vấn đề

Phần "KẾT LUẬN" (Heading 1) trong template gốc chỉ có 3 tiêu đề bold không nội dung:
`1. Kết luận:`, `2. Hạn chế:`, `3. Hướng phát triển trong tương lai:`.

Script hiện tại (`scripts/generate_docx_report.py`, FULL_CONTENT["KẾT LUẬN"]) thay bằng 3 mục,
mỗi mục 1 đoạn ngắn — chưa đầy đủ so với kết quả thực nghiệm đã trình bày ở Chương 3.

Yêu cầu: chi tiết hóa 3 mục (đã duyệt: "3 mục, mỗi mục mở rộng", "mục 1 gồm 3 đoạn",
"thêm trích dẫn [1], [8]").

## 2. Cấu trúc nội dung mới (đã duyệt)

```
1. Kết luận
   • Đoạn 1 — tổng quan hệ thống: pipeline Khoa học Dữ liệu end-to-end
     (crawler v2: 4 nguồn, 22 keyword, 1.193 tin; cleaning: salary/skill/
     experience/dedup; feature engineering: ColumnTransformer; 3 nhóm ML)
     — đáp ứng 100% tiêu chí kỹ thuật học phần.
   • Đoạn 2 — kết quả thực nghiệm: supervised (Baseline RMSE 8.97 →
     Linear 4.17, R² 0.783, +53.5% → DT 0.60, R² 0.996, +93.3%),
     K-Means k=10 silhouette 0.38 (5 phân khúc thị trường),
     Content-based Top-3 (Data Scientist, ML Engineer, Data Engineer).
   • Đoạn 3 — đối chiếu RQ: RQ1-RQ5 đều trả lời (F1-F4 + gợi ý việc làm),
     khớp mục tiêu Chương 1.

2. Hạn chế của đề tài
   • Đoạn 1 — dữ liệu: 6.6% tin có kỹ năng chi tiết (Careerviet/TopCV);
     thiên lệch phân bố thành phố (TP.HCM ~50%, Đà Nẵng ~4%);
     salary midpoint (min+max)/2 thay vì lương thực tế.
   • Đoạn 2 — mô hình: DT/RF overfit trên tập dữ liệu hiện tại;
     chưa dùng skill encoding và text features (description) trong regression.

3. Hướng phát triển
   • Đoạn 1 — dữ liệu: crawler truy cập sâu trang chi tiết từng tin;
     thu thập thêm nguồn, cập nhật dữ liệu theo thời gian.
   • Đoạn 2 — mô hình: NLP/BERT trích xuất đặc trưng từ mô tả công việc;
     thử DBSCAN/Hierarchical clustering; kết hợp collaborative + content-based
     (Hybrid Recommendation) [8]; cơ sở phương pháp theo [1].
```

- Tiêu đề mỗi mục giữ đúng tên template: `1. Kết luận`, `2. Hạn chế của đề tài`,
  `3. Hướng phát triển` (không đổi style Heading, chỉ nội dung đoạn mở rộng).
- Format đoạn: body 12pt Times New Roman, line_spacing 1.15 (khớp
  `insert_content_after_paragraph` hiện có).

## 3. Trích dẫn

Tái sử dụng `REFERENCES` (10 mục đã có), không thêm mục mới:
- [1] Géron — cơ sở phương pháp ML cho hướng phát triển (mục 3, đoạn 2)
- [8] Ricci — Hybrid Recommendation (mục 3, đoạn 2)

## 4. Verify mở rộng (`verify_report()`)

Thêm key_phrases: `"RQ1-RQ5"`, `"silhouette 0.38"`, `"Hybrid Recommendation"`,
`"TP.HCM ~50%"` (hoặc `"Đà Nẵng"`), `"salary midpoint"` — chọn phrase khớp
chính xác text chèn.

Giữ nguyên mọi checks cũ (5 headings, phrases chương 1/2/3, ML table,
refs ≥ 10, không còn resnet50/rác thải/ô nhiễm).

## 5. Non-goals

- Chương 1, 2, 3, LỜI MỞ ĐẦU, TÀI LIỆU THAM KHẢO: giữ nguyên.
- Không thêm refs mới, không thêm bảng, không đổi tên/style tiêu đề template.
- Không thêm thư viện mới, không tách module.
