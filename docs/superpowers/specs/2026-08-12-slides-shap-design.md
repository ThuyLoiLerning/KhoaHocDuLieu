# Thiết kế: Mở rộng nội dung slide + Trình bày kết quả bằng SHAP — Chuyên đề 4

**Ngày:** 2026-08-12
**Yêu cầu:** "Nội dung còn quá sơ sài hãy chỉnh chu chi tiết hơn, bổ sung những chỗ trình bày bằng SHAP thì ok hơn."
**Phạm vi user duyệt:** SHAP + mở rộng slide (đã duyệt thiết kế ngày 12/08: "Duyệt, triển khai").

## Bối cảnh

- Bộ slide hiện tại: `reports/slides/TrinhBay_ChuyenDe4.pptx`, 20 trang, sinh bởi `scripts/generate_pptx_slides.py` (nền tối #1E1E2E, accent cyan, 16:9).
- SHAP 0.52.0 đã cài (pip), script `scripts/generate_shap_plots.py` đã sinh 2 PNG thành công:
  - `reports/slides/charts/shap_tree_summary.png` — TreeExplainer trên Decision Tree, 21 features.
  - `reports/slides/charts/shap_linear_summary.png` — LinearExplainer trên Linear Regression.
- Cả 2 ảnh xác nhận hợp lệ (nền trắng, feature names rõ), CHƯA commit.

## Phạm vi

Sửa `scripts/generate_pptx_slides.py` (thêm slide SHAP + mở rộng bullets + đánh số lại + verify). Đồng bộ caption nguồn `scripts/generate_shap_plots.py`. Không đụng docx, notebook, số liệu.

## Bố cục mới — 22 slide

| # | Slide | Thay đổi |
|---|-------|----------|
| 1 | Bìa | giữ |
| 2 | Giới thiệu bài toán | giữ |
| 3 | Câu hỏi nghiên cứu RQ1-RQ5 | giữ |
| 4 | Kiến trúc hệ thống — Pipeline | giữ |
| 5 | Crawler v2 | giữ |
| 6 | Làm sạch & Chuẩn hóa | giữ |
| 7 | Cleaning — Chart | giữ |
| 8 | Feature Engineering | giữ |
| 9 | Dữ liệu sau xử lý (bảng) | giữ |
| 10 | EDA (bullets F1-F4) | **mở rộng bullets F1-F4** |
| 11 | EDA — Chart | giữ |
| 12 | Kết quả ML (bảng) | **mở rộng note** |
| **13** | **SHAP — Decision Tree** | **MỚI: shap_tree_summary.png + 3 bullets giải thích** |
| 14 | Kết quả ML — Chart | giữ (nhích xuống 1 bậc) |
| 15 | K-Means (bảng) | **mở rộng note** |
| 16 | K-Means — Chart | giữ (nhích xuống 1 bậc) |
| **17** | **SHAP — Linear** | **MỚI: shap_linear_summary.png + 3 bullets** |
| 18 | Gợi ý (bảng) | **mở rộng note** |
| 19 | Gợi ý — Chart | giữ (nhích xuống 1 bậc) |
| 20 | Kết luận | **mở rộng 5 RQ → bằng chứng + thêm bullet SHAP** |
| 21 | Hạn chế & Hướng phát triển | giữ — **sửa num bug 18 → 19** |
| 22 | Cảm ơn | giữ |

## Nội dung cụ thể

### Slide SHAP — tiêu đề: "SHAP — Giải thích mô hình [Decision Tree | Linear Regression]" (13, 17)

| # | Slide | Ảnh | Bullets |
|---|-------|-----|---------|
| 13 | SHAP — Decision Tree | `shap_tree_summary.png` | • TreeExplainer [12] tính 21 feature contributions cho từng tin.\n• experience_years & nhóm kỹ năng đóng góp lớn nhất — bấc kinh nghiệm là yếu tố quyết định lương.\n• Đỏ: đẩy lương lên, xanh: kéo xuống — điểm màu trải rộng phản ánh tác động phi tuyến của DT. |
| 17 | SHAP — Linear | `shap_linear_summary.png` | • LinearExplainer: hệ số nhân giá trị feature (đường thẳng qua 0).\n• Top features khớp DT (experience_years, skill groups) — ổn định qua 2 mô hình.\n• Độ lớn SHAP là đóng góp tuyệt đối (triệu VND) — so sánh trực tiếp độ quan trọng. |

Caption nguồn dưới ảnh: `"SHAP summary plot — nguồn: scripts/generate_shap_plots.py (TreeExplainer/LinearExplainer)"`.

### Mở rộng bullets chi tiết hơn

- **Slide 10 EDA (6 → 8 bullets):**
  - F1 — dữ liệu 1.193 tin, nhóm Data Science & Lập trình chiếm ưu thế.
  - Top kỹ năng: JavaScript, React, Kafka, Python, SQL, Docker, Spring Boot, TensorFlow.
  - F2 — Entry ~10M → Mid ~17M → Senior ~28M → Lead ~35M+ (tăng trưởng qua từng bậc).
- **Slide 12 note** — thêm: giảm RMSE 53.5% (Linear) và 93.3% (DT) so Baseline; RF overfit.
- **Slide 15 note** — thêm: 5 phân khúc đặc trưng dựa trên lương TB & kỹ năng chính (Junior-Mid HN 15.1M · Senior 41.9M · Remote 31.6M).
- **Slide 18 note** — làm rõ: Lọc thành phố + phân khúc kinh nghiệm ±0.5 năm → giảm nhiễu; multi-skill weight (frequency-based).

## Quyết định kỹ thuật

1. **Layout slide SHAP:** không dùng `add_chart_slide` (không có param bullets). Slide SHAP dựng trực tiếp: `new_slide` + `add_title_bar(slide, "SHAP — Giải thích mô hình ...", num)` + ảnh trái qua `_add_pic(slide, path, 0.6, 1.3, w, h, caption)` (kích thước theo `_img_size_px`, ar ≥1 → w=6.0in) + `add_bullets(slide, bullets, top=1.3, left=7.0, width=5.8, height=5.3, size=16)` — ảnh trái 0.6→6.6in, bullets phải 7.0→12.8in.

2. **Đánh số lại:** 20 slide → 22 slide. Sửa comment/num: 10 "Kết quả ML" → 12, K-Means 14 → 15, gợi ý 16 → 18. Sửa **bug num=18 lặp** ở slide "Hạn chế" → num=19 (sửa num bug trên slide 19 hiện tại, comment "19. Hạn chế").

3. **Verify cập nhật:**
   - Tổng slide = 22.
   - Slide 13, 17 mỗi slide ≥ 1 picture; tổng pictures ≥ 12.
   - Index chart_slides (0-based) = {6, 10, 12, 13, 15, 18} (slide 7, 11, 13 SHAP, 14, 16, 19): mỗi slide có pics ≥ 1.
   - Tổng pictures ≥ 12 (2 SHAP + 10 chart).
   - Bảng ML 5×4 → slide 12 (idx 11), CH2 7×2 → slide 9 (idx 8), cluster 6×5 → slide 15 (idx 14).
   - Giữ 6 số liệu.

4. **No new dependency** (shap đã có ở môi trường; requirements không phải thêm vì script SHAP là tool sinh ảnh tĩnh, phụ thuộc dev môi trường).

## Out of scope

- Không sửa nội dung các slide còn lại ngoài bullets/note nêu trên.
- Không chèn SHAP vào slide có sẵn.
- Không sửa docx, notebook.

## Verify thủ công

- Mở PPTX: 22 slide, slide 13/17 hiển thị SHAP rõ (ảnh đủ rộng), bullets giải thích đúng, đánh số liên tục 1→22, không trùng số.