# Cập nhật Trình bày Chuyên nghiệp — 22 Slide PPTX (Chuyên đề 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Khắc phục các khiếm khuyết trình bày phát hiện từ khảo sát preview — caption tràn 2 dòng, slide dày đặc, đồng nhất font — để bộ 22 slide trình bày chuyên nghiệp.

**Architecture:** Sửa tập trung trong `scripts/generate_pptx_slides.py` (source of truth duy nhất sinh `reports/slides/TrinhBay_ChuyenDe4.pptx`). Không đụng ảnh chart, không đổi số slide, không đổi nội dung số liệu.

**Tech Stack:** python-pptx 1.0.2, Python 3 (chạy `PYTHONIOENCODING=utf-8 python scripts/generate_pptx_slides.py`).

## Global Constraints

- Giữ nguyên: 22 slide, thứ tự, số đánh (num), ảnh chart, bảng, màu sắc, số liệu.
- Mọi sửa đổi chỉ trong `scripts/generate_pptx_slides.py`.
- Sau mỗi change set: chạy script + verify phải `VERIFICATION PASSED`.
- Font: Calibri, kích thước hiện tại (17/15pt bullets, 13pt bảng, 12pt caption).
- File mục tiêu: `reports/slides/TrinhBay_ChuyenDe4.pptx`.

---

### Task 1: Helper font nhất quán + caption ngắn gọn

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — thêm module-level `FONT_NAME = "Calibri"`; helper `_r(run, size, color, bold)` set font đồng nhất; thay các `r.font.name = "Calibri"` trong `add_bullets`, `add_table_slide`, `_add_pic` caption.
- Modify: `scripts/generate_pptx_slides.py` — rút gọn caption:
  - Slide 7: `"Missing values"` + `"Kinh nghiệm yêu cầu (nguồn: nb 02 c8)"` → caption ngắn gọn `"Missing values (nguồn: notebook 02)"` / `"Phân bố kinh nghiệm (nguồn: notebook 02)"`
  - Slide 11: `"Phân bố nhóm kỹ năng (nguồn: nb 03)"`, `"Top 20 kỹ năng (nguồn: nb 03)"`, `"Lương theo tiếng Anh (nguồn: nb 03)"`
  - Slide 13/17: `"SHAP summary plot — TreeExplainer (nguồn: scripts/generate_shap_plots.py)"` / `"... — LinearExplainer ..."`
  - Slide 14, 16, 19: rút gọn tương tự (bỏ "cell cYY" → "nguồn: notebook 04")

- [ ] **Step 1:** Thêm `FONT_NAME = "Calibri"` cạnh các hằng màu; tạo helper `_r(run, size, color, bold=False)`:
```python
FONT_NAME = "Calibri"

def _r(run, size, color, bold=False):
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    return run
```
Thay các đoạn gán font trong `add_bullets`, `add_table_slide`, `add_shap_slide`, `add_flow_slide` box bằng `_r(r, ...)`.

- [ ] **Step 2:** Rút gọn từng caption có 2 dòng (slide 7: `"Missing values — thiếu lương, kỹ năng, kinh nghiệm (nguồn: notebook 02, cell 8)"` → `"Missing values (nguồn: notebook 02)"`; tương tự cả 10 caption chart + 2 caption SHAP).

- [ ] **Step 3:** Chạy: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu; $env:PYTHONIOENCODING="utf-8"; python scripts/generate_pptx_slides.py`
Expected: `Saved: ... (22 slides)` + `VERIFICATION PASSED: 22 slides, ...`

- [ ] **Step 4:** Kiểm tra không còn tràn: `python scripts/inspect_slides.py` → chỉ còn tối đa 0 flag logic (caption ≤ 1 dòng). Commit:
```bash
git add scripts/generate_pptx_slides.py
git commit -m "refactor(slides): font helper + caption ngắn gọn — hết tràn 2 dòng"
```

---

### Task 2: Slide 6 (Làm sạch) — giảm mật độ, tách dòng khóa học

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — nội dung bullets slide 6 trong `build()`.

**Vấn đề:** 8 bullets câu dài (level 0 + 1) → ~4.3in text, chật trong khung 5.6in, trông nặng.

- [ ] **Step 1:** Rút còn 6 bullets level 0 (gộp 2 cặp level 1 vào câu gốc), mỗi bullet ≤ ~95 ký tự:
```python
("SalaryParser nhận diện 8 cấu trúc lương (6 regex, USD→VND ×25.000, năm→tháng)", 0),
("56% tin ẩn lương (24+ từ khóa cạnh tranh, thỏa thuận) → xử lý trước khi dùng ML", 0),
("Khoảng \"tới X\" ≈ 70%, \"từ X\" ≈ 130% — chuẩn hóa về điểm giữa phản ánh thị trường", 1),
("SkillNormalizer gộp 188 quy tắc đồng nghĩa → 45 kỹ năng chuẩn thuộc 12 nhóm (fuzzy > 0.8, độ phủ 6.6%)", 0),
("ExperienceNormalizer gán 5 bậc kinh nghiệm (entry→lead) bằng 6 regex TV/EN", 0),
("Deduplicator loại 70 bản ghi trùng qua 4 pha: job_id, title+company, fuzzy title/desc", 0),
```

- [ ] **Step 2:** Chạy verify script → PASSED. Kiểm tra `inspect_slides.py` slide 6: textbox cần ≤ 4.5in.
- [ ] **Step 3:** Commit `"refactor(slides): slide 6 giảm mật độ — gộp bullets dài thành 6 câu"`.

---

### Task 3: Slide 4 (Pipeline) — cân bằng box + bullets gọn hơn

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `add_flow_slide` và call slide 4.

**Vấn đề:** Box content 11pt 3 dòng có thể chật (2.9in×1.75in); bullets B1-B4 dài 2 dòng mỗi ý.

- [ ] **Step 1:** Box font content 11→10pt, line spacing `space_before Pt(1)`; tiêu đề box 15→14pt. Cho `box.height` cố định 1.75in (giữ).
- [ ] **Step 2:** Rút gọn từng bullet B1-B4 còn ≤ ~90 ký tự (bỏ từ thừa, giữ số liệu): ví dụ `"B1 — Thu thập: HTTP client xoay vòng 3 User-Agent, rate-limit 1-3s, crawl 22 keyword × 4 nguồn"` → `"B1 — Crawler v2: 3 User-Agent xoay vòng, rate-limit 1-3s, 22 keyword × 4 nguồn, 1.193 tin"`.
- [ ] **Step 3:** Verify PASSED + `inspect_slides.py` slide 4 box không tràn (needed ≤ 1.75in). Commit `"refactor(slides): slide 4 cân bằng box + bullets pipeline gọn"`.

---

### Task 4: Slide 13/17 (SHAP) — ảnh + text giảm trùng lặp

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `add_shap_slide` + call slide 13/17.

**Vấn đề:** Bullets phải (w=5.8in) câu dài wrap nhiều dòng; ảnh SHAP cũng hiển thị feature importance (trùng thông điệp).

- [ ] **Step 1:** Giảm mỗi slide còn 3 bullets ngắn (≤ ~80 ký tự), bỏ 1 bullet trùng với nội dung ảnh:
  - Slide 13: giữ giải thích đỏ/xanh, experience_years top, bỏ bullet "cộng dồn baseline" (ảnh đã thể hiện).
  - Slide 17: giữ LinearExplainer formula, top-khớp DT, bỏ bullet "độ lớn SHAP tuyệt đối" (trùng ảnh).
- [ ] **Step 2:** Tăng ảnh lên w=6.6in (bù chỗ trống bên phải), bullets size 16→15pt, left 7.45→7.3.
- [ ] **Step 3:** Verify PASSED + `inspect_slides.py` slide 13/17 bullets ≈ 2.5-3.5in. Commit `"refactor(slides): SHAP ảnh to hơn, bullets 3 câu gọn"`.

---

### Task 5: Slide 10 (EDA) + Slide 20 (Kết luận) — cắt bớt mật độ

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — slide 10, 20 bullets.

**Vấn đề:** Slide 10: 6 bullets level 0/1 dài (≈3.9in); Slide 20: 6 bullets dài (≈3.7in) — dày hơn cần thiết.

- [ ] **Step 1:** Slide 10 giữ 6 bullets nhưng rút gọn mỗi câu ≤ ~95 ký tự, bỏ đuôi giải thích thừa ở level 1 (giữ số liệu + ý chính):
```python
("F1 — Nhóm kỹ năng Data Science & Lập trình dẫn đầu (1.193 tin)", 0),
("Top kỹ năng: JavaScript, React, Kafka, Python, SQL, Docker, Spring Boot, TensorFlow", 1),
("F2 — Lương tăng theo bậc: Entry ~10M → Mid ~17M → Senior ~28M → Lead ~35M+", 0),
("TP.HCM & Hà Nội lương trung bình cao hơn rõ rệt", 1),
("F3 — Yêu cầu tiếng Anh: lương trung bình cao hơn ~30%", 0),
("F4 — Vị trí cấp cao (Senior, Manager, Lead) ẩn lương >50%", 0),
```
- [ ] **Step 2:** Slide 20 rút gọn tương tự, mỗi bullet ≤ ~105 ký tự, giữ nguyên số liệu RMSE/R²/Silhouette.
- [ ] **Step 3:** Verify PASSED + inspect. Commit `"refactor(slides): slide 10/20 gọn hơn, giữ số liệu"`.

---

### Task 6: Slide 5 (Crawler) — tách 1 bullet chống chặn dài thành ngắn

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — slide 5 bullets.

**Vấn đề:** Bullet "Chống chặn: xoay vòng 3 User-Agent, rate-limit 1-3s, retry HTTP 429, nhận diện trang chặn qua BLOCKED_MARKERS (captcha, cf-challenge)" ~150 ký tự → 3 dòng.

- [ ] **Step 1:** Tách thành 2 bullet level 0: `("Chống chặn: xoay vòng 3 User-Agent, rate-limit 1-3s, retry 429", 0)` + `("Nhận diện trang chặn qua BLOCKED_MARKERS (captcha, cf-challenge)", 0)`.
- [ ] **Step 2:** Verify + inspect slide 5 (≤4.5in). Commit `"refactor(slides): slide 5 tách bullet chống chặn dài"`.

---

### Task 7: Verify cuối + kiểm tra thủ công preview

**Files:**
- Modify: không — verify hiện có trong script.

- [ ] **Step 1:** Chạy 2 lệnh:
```bash
cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu; $env:PYTHONIOENCODING="utf-8"; python scripts/generate_pptx_slides.py
python scripts/inspect_slides.py | Select-String -Pattern "tràn|NGHI"
```
Expected: `VERIFICATION PASSED` + không dòng "CÓ THỂ TRÀN" (hoặc chỉ flag đã biết).

- [ ] **Step 2:** Export preview mới (PowerShell COM như đã làm) → Read 3-4 slide đại diện (1, 4, 6, 13) kiểm tra trực quan.
- [ ] **Step 3:** Nếu ổn: commit tổng `"refactor(slides): trình bày chuyên nghiệp — caption, mật độ, SHAP"`; nếu có vấn đề còn lại → ghi vào báo cáo cuối.