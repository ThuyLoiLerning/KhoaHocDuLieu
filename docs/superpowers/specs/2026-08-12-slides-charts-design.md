# Thiết kế: Thêm chart từ notebook vào bộ slide PPTX — Chuyên đề 4

**Ngày:** 2026-08-12
**Yêu cầu:** Nội dung slide còn sơ sài — thêm ảnh chart đã mô tả trong notebook để mô tả kết quả thực nghiệm chi tiết hơn.

## Bối cảnh

- Bộ slide hiện tại: `reports/slides/TrinhBay_ChuyenDe4.pptx`, 15 trang, sinh bởi `scripts/generate_pptx_slides.py` (python-pptx, nền tối #1E1E2E, chữ trắng, accent cyan, 16:9).
- 10 chart PNG đã trích xuất từ notebook (matplotlib, nền trắng) vào `reports/slides/charts/`, tên gốc `datachartsXX_cYY_...png`.
- Quyết định user: **kết hợp** — giữ 15 slide hiện có + thêm 5 slide chart riêng = **20 slide**, đưa đủ cả 10 chart.

## Phạm vi

Sửa `scripts/generate_pptx_slides.py` + đổi tên 10 file chart. Không đụng docx, notebook, số liệu.

## Bố cục mới — 20 slide

| # | Slide | Thay đổi |
|---|-------|----------|
| 1 | Bìa | giữ |
| 2 | Giới thiệu bài toán | giữ |
| 3 | Câu hỏi nghiên cứu RQ1-RQ5 | giữ |
| 4 | Kiến trúc hệ thống — Pipeline | giữ |
| 5 | Crawler v2 | giữ |
| 6 | Làm sạch & Chuẩn hóa | giữ |
| **7** | **Cleaning — Chart dữ liệu thực tế** | **MỚI: missing values + experience years** |
| 8 | Feature Engineering | giữ |
| 9 | Dữ liệu sau xử lý (bảng) | giữ |
| 10 | EDA (bullets F1-F4) | giữ |
| **11** | **EDA — Chart chi tiết** | **MỚI: dải nhóm kỹ năng (full-width) + Top 20 skills + lương tiếng Anh** |
| 12 | Kết quả mô hình dự báo lương (bảng) | giữ |
| **13** | **Kết quả ML — Chart** | **MỚI: residuals + so sánh model** |
| 14 | Phân cụm thị trường K-Means (bảng) | giữ |
| **15** | **K-Means — Chart phân cụm** | **MỚI: silhouette + PCA 2D** |
| 16 | Hệ thống gợi ý việc làm (bảng) | giữ |
| **17** | **Gợi ý — Chart similarity** | **MỚI: similarity distribution** |
| 18 | Kết luận | giữ |
| 19 | Hạn chế & Hướng phát triển | giữ |
| 20 | Cảm ơn | giữ |

Đánh số lại liên tục 1→20 theo thứ tự mới (`num` trong `add_title_bar`).

## Chart → slide (10 chart)

| Chart (tên mới) | Nguồn notebook (cell) | Kích thước px (gốc) | Slide |
|---|---|---|---|
| `missing_values.png` | 02_c8 | 1189×590 | 7 |
| `experience_years.png` | 02_c18 | 989×490 | 7 |
| `skill_group_dist.png` | 03_c11 | 6752×675 (RẤT RỘNG) | 11 — dải full-width, co theo chiều cao ~2.2in |
| `top20_skills.png` | 03_c9 | 1295×784 | 11 |
| `salary_english.png` | 03_c23 | 1022×537 | 11 |
| `residuals.png` | 04_c18 | 1384×483 | 13 |
| `model_compare.png` | 04_c20 | 984×483 | 13 |
| `silhouette_scores.png` | 04_c24 | 984×483 | 15 |
| `pca_2d_clusters.png` | 04_c27 | 1184×784 | 15 |
| `similarity_dist.png` | 04_c33 | 1409×483 | 17 |

## Quyết định kỹ thuật

1. **Giữ nguyên toàn bộ slide hiện có** (text, bảng, note) — chỉ chèn 5 slide chart mới giữa các slide liên quan.
2. **Helper mới `add_chart_slide(prs, title, charts, num)`** trong `generate_pptx_slides.py`:
   - `charts`: list dict `{"path": ..., "caption": ..., "source": ...}` (tối đa 2 ảnh/slide, đặt cạnh nhau).
   - Tính kích thước ảnh bằng PIL (đã có trong requirements) → co giữ tỷ lệ về khung tối đa (cao ≤ 4.6in, rộng ≤ 5.9in mỗi ảnh khi 2 ảnh; full-width cao ≤ 2.2in cho dải 6752px).
   - Vị trí: title bar ở trên (giữ nguyên style `add_title_bar`), vùng ảnh từ ~1.4in → 6.9in.
   - Viền mảnh quanh mỗi ảnh (line ~1pt, màu TABLE_ALT) để tách nền trắng chart khỏi nền tối.
   - Caption 14pt gray dưới mỗi ảnh: `"Tên chart — Nguồn: notebook, cell cYY"`.
   - Ảnh 2D (ngang, tỷ lệ > ~2.2:1) đặt full-width phía trên, ảnh dưới chia cột.
3. **Đổi tên 10 file** trong `reports/slides/charts/` sang tên mô tả ở bảng trên (mv đơn giản, không sửa notebook).
4. **Đường dẫn ảnh trong script:** `CHARTS_DIR = PROJECT_ROOT / "reports" / "slides" / "charts"`, ánh xạ tên mô tả → slide.
5. **Verify cập nhật:**
   - Tổng 20 slide.
   - Slide 7, 11, 13, 15, 17 mỗi slide ≥ 1 picture shape (`shape.shape_type == MSO_SHAPE_TYPE.PICTURE`).
   - Tổng số picture trong deck ≥ 10.
   - Giữ các check cũ: bảng ML 5×4 (giờ slide 12), CH2 7×2 (slide 9), cluster 6×5 (slide 14), 6 số liệu chính.
   - Ảnh không vượt ranh giới slide (x ≥ 0, x+width ≤ 13.33in, y+height ≤ 7.5in).
6. **Không thêm dependency mới** — PIL (Pillow) đã có trong requirements qua matplotlib.

## Out of scope

- Không sửa nội dung text/bảng của 15 slide hiện có.
- Không chèn chart vào slide có sẵn (tránh chật, giữ slide chart riêng).
- Không sinh lại chart từ notebook — dùng 10 PNG có sẵn.
- Không sửa docx.

## Verify thủ công

- Mở PPTX mới: 20 slide, chart hiển thị rõ trên nền tối, caption + nguồn đúng.
- Các chart không bị bóp méo tỷ lệ (giữ aspect ratio).
