# Thiết kế: Redesign bộ 22 slide — nền trắng học thuật + stat cards + icon + badge (Chuyên đề 4)

**Ngày:** 2026-08-12
**Yêu cầu:** "Slide vẫn chưa được thay đổi nhiều, trình bày đang quá thô."
**Phạm vi user duyệt (AskUserQuestion 12/08):** Emoji Unicode · Toàn bộ 22 slide · Chuyển nền trắng · kèm "các câu từ giải thích không được ghi vắn tắt".

## Bối cảnh

- Bộ slide hiện tại: `reports/slides/TrinhBay_ChuyenDe4.pptx` (22 slide, nền tối #1E1E2E), sinh bởi `scripts/generate_pptx_slides.py` — 19/22 slide chỉ có title + bullets text thuần, thiếu visual.
- 12 ảnh chart PNG trong `reports/slides/charts/` đều nền trắng — chuyển nền trắng giúp hòa hợp tự nhiên, bỏ viền tối.

## Bảng màu mới

| Vai trò | Giá trị |
|---|---|
| Nền | `#FFFFFF` |
| Chữ chính | `#1F2937` |
| Chữ phụ | `#6B7280` |
| Accent chính (tiêu đề, số, badge, header bảng) | `#2563EB` |
| Accent phụ (số liệu nổi bật, keyphrase) | `#F59E0B` |
| Card nền | `#EFF6FF`, viền `#BFDBFE` |
| Hàng bảng xen kẽ | `#F3F4F6` |
| Box pipeline nền | `#F8FAFC`, viền `#2563EB` |

## Component mới (lặp lại mọi slide)

1. **Title bar + badge section**: số slide trong vòng tròn xanh, tiêu đề đen đậm 28pt, vạch accent 3pt dưới tiêu đề. Pill badge góc phải: `GIỚI THIỆU` (slide 1-3) · `PHƯƠNG PHÁP` (4-8) · `PHÂN TÍCH` (9-11) · `KẾT QUẢ` (12-19) · `KẾT LUẬN` (20-22).
2. **Icon emoji** cạnh tiêu đề mỗi slide: 🕷️ Crawler · 🧹 Cleaning · 🧮 Feature · 📊 EDA · 🤖 ML · 🎯 K-Means · 💡 Gợi ý · 🏆 Kết luận · 📋 Giới thiệu/RQ/Data.
3. **Stat cards** (slide 2, 9, 20): hàng 4 card — emoji + số lớn 30pt accent + label xám 13pt:
   - Slide 2: `1.193 tin` · `4 nguồn` · `44 cột` · `56% ẩn lương`
   - Slide 9: `1.193 tin` · `4 nguồn` · `56% ẩn lương` · `6.6% kỹ năng`
   - Slide 20: `RMSE 0.60` · `R² 0.996` · `Silhouette 0.38` · `Top-3 đề xuất`
4. **Keyphrase rich-text**: bullets hỗ trợ cú pháp `**từ khóa**` → run in đậm màu accent (chia run bằng split "**").
5. **Bảng**: header nền xanh `#2563EB` chữ trắng, hàng xen kẽ `#F3F4F6`, chữ `#1F2937` — giữ col_widths, cỡ chữ.
6. **Slide 4 pipeline**: box nền `#F8FAFC` viền xanh, tiêu đề box xanh đậm, mũi tên xanh; bullets đen.

## Nguyên tắc viết text

- Mọi bullet = câu đầy đủ, có chủ ngữ, không viết vắn tắt/ghi chú (bỏ cách viết "B1 — Crawler v2: 3 User-Agent..." → "Thu thập dữ liệu: Crawler v2 xoay vòng 3 User-Agent, giới hạn tốc độ 1-3 giây...", giữ số liệu).
- Tối đa ~6 bullet level 0/slide (17pt); keyphrase quan trọng bôi `**đậm màu**`.
- Nội dung số liệu giữ nguyên tuyệt đối (1.193, 4.17, 0.60, 0.38, 56%, 6.6%, 1500×45...).

## Kiến trúc

Chỉ sửa `scripts/generate_pptx_slides.py` (source of truth duy nhất). Sửa helper: `new_slide` (nền trắng), `add_title_bar` (badge + vạch + số tròn), `add_bullets` (rich-text **), `add_table_slide` (màu mới), `_add_pic` (bỏ viền, caption xám), `add_flow_slide` (box trắng viền xanh), `add_shap_slide`. Thêm helper: `_badge()`, `_stat_cards()`, `_rich_para()`. Không đụng ảnh chart, số liệu, số slide.

## Verify

- Giữ các check cũ: 22 slide, bảng ML 5×4 (slide 12), CH2 7×2 (slide 9), cluster 6×5 (slide 15), chart_slides {6,10,12,13,15,18} có ảnh, tổng pics ≥ 12, SHAP slide 13/17, 6 số liệu lowercase ["1.193","4.17","0.38","1500","56%","6.6%"], bounds ảnh.
- Thêm: layout nền trắng (không còn #1E1E2E trong pptx), slide 2/9/20 có ≥ 4 stat cards (check số lượng textbox hoặc shape), mỗi slide có badge.
- Chạy: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu; $env:PYTHONIOENCODING="utf-8"; python scripts/generate_pptx_slides.py` → VERIFICATION PASSED.
- Manual: export preview 4 slide đại diện (1, 4, 9, 13) qua PowerPoint COM, Read PNG kiểm tra.

## Out of scope

- Không sửa ảnh chart, bảng dữ liệu, số liệu, số slide.
- Không đụng docx, notebook, final_report.
- Không thêm dependency (emoji Unicode Windows render sẵn).
