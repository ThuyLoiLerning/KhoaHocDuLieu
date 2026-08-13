# Redesign 22 slide nền trắng — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chuyển bộ 22 slide từ nền tối text-thuần sang nền trắng học thuật với stat cards, icon emoji, badge section, keyphrase rich-text — câu từ đầy đủ không viết vắt tắt.

**Architecture:** Sửa tập trung trong `scripts/generate_pptx_slides.py` (source of truth duy nhất sinh `reports/slides/TrinhBay_ChuyenDe4.pptx`). Đổi bảng màu + 7 helper, thêm 3 helper mới, mở rộng verify. Không đụng ảnh chart, số liệu, số slide.

**Tech Stack:** python-pptx 1.0.2, Python 3 (chạy `PYTHONIOENCODING=utf-8 python scripts/generate_pptx_slides.py`).

## Global Constraints

- Giữ nguyên: 22 slide, thứ tự, số đánh (num), ảnh chart 12 PNG, bảng dữ liệu, số liệu (1.193, 4.17, 0.60, 0.38, 56%, 6.6%, 1500×45...).
- Mọi sửa đổi chỉ trong `scripts/generate_pptx_slides.py`.
- Sau mỗi change set: chạy script + verify phải `VERIFICATION PASSED`.
- Font: Calibri. Màu mới: nền `#FFFFFF`, chữ `#1F2937`, chữ phụ `#6B7280`, accent `#2563EB`, accent phụ `#F59E0B`, card `#EFF6FF` viền `#BFDBFE`, bảng xen kẽ `#F3F4F6`, box `#F8FAFC`.
- Bullets hỗ trợ cú pháp `**keyphrase**` → run đậm màu accent.
- File mục tiêu: `reports/slides/TrinhBay_ChuyenDe4.pptx`.

---

### Task 1: Bảng màu + nền trắng + title bar (badge, vạch, số tròn)

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — hằng màu (dòng 18-23), `new_slide` (69-73), `add_title_bar` (85-95).

**Interfaces:**
- Produces: `add_title_bar(slide, title, num=None)` giữ nguyên signature — thêm badge section + vạch accent + số tròn. Hằng: `BG, INK, SUB, BLUE, AMBER, CARD_BG, CARD_BORDER, TABLE_ALT, BOX_BG`.

- [ ] **Step 1: Đổi hằng màu**

```python
# --- Màu sắc (nền trắng học thuật) ---
BG = RGBColor(0xFF, 0xFF, 0xFF)          # nền trắng
INK = RGBColor(0x1F, 0x29, 0x37)         # chữ chính
SUB = RGBColor(0x6B, 0x72, 0x80)         # chữ phụ
BLUE = RGBColor(0x25, 0x63, 0xEB)        # accent chính
AMBER = RGBColor(0xF5, 0x9E, 0x0B)       # accent phụ (số liệu)
CARD_BG = RGBColor(0xEF, 0xF6, 0xFF)     # card nền
CARD_BORDER = RGBColor(0xBF, 0xDB, 0xFE) # card viền
TABLE_ALT = RGBColor(0xF3, 0xF4, 0xF6)   # hàng bảng xen kẽ
BOX_BG = RGBColor(0xF8, 0xFA, 0xFC)      # box pipeline nền
FONT_NAME = "Calibri"
```

- [ ] **Step 2: Sửa `new_slide` dùng BG mới** — không đổi code, chỉ đổi màu hằng. (Không cần sửa body.)

- [ ] **Step 3: Sửa `add_title_bar`** — số tròn + tiêu đề đen + vạch + badge:

```python
SECTION_BADGES = {
    range(1, 4): "GIỚI THIỆU",
    range(4, 9): "PHƯƠNG PHÁP",
    range(9, 12): "PHÂN TÍCH",
    range(12, 20): "KẾT QUẢ",
    range(20, 23): "KẾT LUẬN",
}

def _badge(slide, text, x=10.6, y=0.42, w=2.3, h=0.42):
    """Pill badge góc phải: nền xanh nhạt, chữ xanh đậm."""
    box = slide.shapes.add_shape(5, Inches(x), Inches(y), Inches(w), Inches(h))  # roundRect
    box.fill.solid()
    box.fill.fore_color.rgb = CARD_BG
    box.line.color.rgb = CARD_BORDER
    box.line.width = Pt(0.75)
    tf = box.text_frame
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    _r(r, 11, BLUE, bold=True)

def add_title_bar(slide, title, num=None):
    """Thanh tiêu đề: số tròn xanh + tiêu đề đen đậm + vạch accent + badge section."""
    label = f"{num}. {title}" if num else title
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.28), Inches(12.3), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = label
    _r(r, 28, INK, bold=True)
    # Vạch accent dưới tiêu đề
    bar = slide.shapes.add_shape(1, Inches(0.55), Inches(1.12), Inches(1.6), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()
    # Badge section (bỏ qua nếu không có num)
    if num:
        for rng, label_b in SECTION_BADGES.items():
            if num in rng:
                _badge(slide, label_b)
                break
    return tb
```

- [ ] **Step 4: Chạy verify**

```bash
cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu; $env:PYTHONIOENCODING="utf-8"; python scripts/generate_pptx_slides.py
```
Expected: `Saved: ... (22 slides)` + `VERIFICATION PASSED: 22 slides, ...`

- [ ] **Step 5: Commit**
```bash
git add scripts/generate_pptx_slides.py
git commit -m "refactor(slides): nền trắng + title bar badge section"
```

---

### Task 2: Rich-text bullets (keyphrase **đậm**) + màu text mới

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `add_bullets` (98-117), `_set_text` (76-82).

**Interfaces:**
- Consumes: `_r(run, size, color, bold=False)` (đã có).
- Produces: `add_bullets` giữ signature; `_rich_para(p, text, size, base_color, accent)` — thêm runs cho text có `**...**`.

- [ ] **Step 1: Thêm helper `_rich_para`**

```python
def _rich_para(p, text, size, base_color, accent):
    """Thêm runs cho 1 paragraph: đoạn **...** in đậm màu accent, còn lại màu base."""
    first = True
    for i, seg in enumerate(text.split("**")):
        if not seg:
            continue
        r = p.add_run() if not first else (p.add_run() if not p.runs else p.runs[0])
        if p.runs and first:
            r = p.runs[0]
        r.text = seg
        bold = (i % 2 == 1)
        _r(r, size, accent if bold else base_color, bold=bold)
        first = False
```

- [ ] **Step 2: Sửa `add_bullets`** — dùng `_rich_para` thay cho add_run đơn:

```python
def add_bullets(slide, bullets, top=1.4, left=0.6, width=12.1, height=5.6, size=17):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in bullets:
        level = 0
        text = item
        if isinstance(item, tuple):
            text, level = item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        bullet_char = "• " if level == 0 else "– "
        _rich_para(p, bullet_char + text, size if level == 0 else size - 2,
                   INK if level == 0 else SUB, BLUE)
        p.space_after = Pt(8 if level == 0 else 4)
    return tb
```

- [ ] **Step 3: Sửa `_set_text`** — base color INK thay WHITE: không đổi code body (gọi với màu mới ở các chỗ dùng: `add_title_slide` chữ trắng → INK, `add_thanks_slide` CYAN → BLUE, `add_flow_slide` mũi tên CYAN → BLUE, `_add_pic` caption GRAY → SUB). Tìm các literal `WHITE`/`CYAN`/`GRAY` trong file và thay lần lượt:
  - `add_title_slide`: `34, WHITE` → `34, INK`; `18, GRAY` → `18, SUB`.
  - `add_thanks_slide`: `40, CYAN` → `40, BLUE`; `20, GRAY` → `20, SUB`.
  - `add_flow_slide`: `arr` `20, CYAN` → `20, BLUE`.
  - `_add_pic`: `12, GRAY` → `12, SUB`.

- [ ] **Step 4: Chạy verify** (lệnh Task 1 Step 4) → PASSED.
- [ ] **Step 5: Commit** `"refactor(slides): rich-text **keyphrase** + màu text nền trắng"`.

---

### Task 3: Stat cards (slide 2, 9, 20)

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — thêm `_stat_cards()`, gọi trong `build()` ở slide 2 (dòng 326), 9 (dòng 403), 20 (dòng 480).

**Interfaces:**
- Consumes: `_r()`, hằng màu Task 1.
- Produces: `_stat_cards(slide, cards, top, left=0.6, width=12.1)` — `cards: list dict {"emoji", "value", "label"}`; mỗi card rộng `(width-3*0.25)/4`, cao 1.35in, nền CARD_BG viền CARD_BORDER, emoji 22pt giữa, value 30pt đậm BLUE, label 12pt SUB.

- [ ] **Step 1: Thêm helper**

```python
def _stat_cards(slide, cards, top, left=0.6, width=12.1):
    n = len(cards)
    gap = 0.25
    cw = (width - (n - 1) * gap) / n
    ch = 1.35
    for i, card in enumerate(cards):
        x = left + i * (cw + gap)
        box = slide.shapes.add_shape(1, Inches(x), Inches(top), Inches(cw), Inches(ch))
        box.fill.solid()
        box.fill.fore_color.rgb = CARD_BG
        box.line.color.rgb = CARD_BORDER
        box.line.width = Pt(1)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.05)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = card["emoji"] + "  " + card["value"]
        _r(r, 30, BLUE, bold=True)
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = card["label"]
        _r(r2, 12, SUB)
```

- [ ] **Step 2: Gọi trong `build()`** — slide 2 ngay sau `add_content_slide(...)`:

```python
    _stat_cards(slide2, [
        {"emoji": "🗂️", "value": "1.193", "label": "tin tuyển dụng"},
        {"emoji": "🌐", "value": "4", "label": "nguồn dữ liệu"},
        {"emoji": "📋", "value": "44", "label": "thuộc tính"},
        {"emoji": "🔒", "value": "56%", "label": "tin ẩn lương"},
    ], top=6.55)
```
(slide2 = biến nhận từ `add_content_slide` — cần gán: sửa dòng 326 thành `s2 = add_content_slide(...)` rồi gọi `_stat_cards(s2, [...], top=6.55)`.)

Slide 9 (sau `add_table_slide`):
```python
    s9 = add_table_slide(prs, "Dữ liệu sau xử lý", CH2_STATS_TABLE, num=9, col_widths=[7, 5.1],
                         note="1.193 tin tuyển dụng · 44 thuộc tính · 4 nguồn tuyển dụng chính tại Việt Nam")
    _stat_cards(s9, [
        {"emoji": "🗂️", "value": "1.193", "label": "tin tuyển dụng"},
        {"emoji": "🌐", "value": "4", "label": "nguồn dữ liệu"},
        {"emoji": "🔒", "value": "56%", "label": "tin ẩn lương"},
        {"emoji": "🧩", "value": "6.6%", "label": "độ phủ kỹ năng"},
    ], top=6.3)
```
Lưu ý: slide 9 đang có note ở bottom 6.6 — đẩy note lên 6.3 → sửa call `add_table_slide` để note không đè card: đổi note textbox `top=6.6` → `top=6.25` trong `add_table_slide` (dòng 143) — nhưng table slide 3/12/15/18 không có card nên vị trí note giữ nguyên là đẹp; thay vì đổi toàn cục, thêm param `note_top=6.6` mặc định, slide 9 truyền `note_top=6.25`.

Slide 20 (sau `add_content_slide`):
```python
    s20 = add_content_slide(prs, "Kết luận", [...bullets hiện tại...], num=20)
    _stat_cards(s20, [
        {"emoji": "🎯", "value": "RMSE 0.60", "label": "Decision Tree"},
        {"emoji": "📈", "value": "R² 0.996", "label": "Decision Tree"},
        {"emoji": "💎", "value": "0.38", "label": "Silhouette k=10"},
        {"emoji": "🎖️", "value": "Top-3", "label": "việc phù hợp"},
    ], top=6.55)
```
(Lưu ý: `RMSE 0.60` dài → card value 30pt sẽ hơi rộng; chấp nhận 24pt nếu cần: thêm param `size=30` mặc định, slide 20 truyền `size=24`.)

- [ ] **Step 3: Thêm param `note_top` vào `add_table_slide`** (dòng 143): `note_top=6.6` mặc định, `tb = slide.shapes.add_textbox(Inches(0.6), Inches(note_top), ...)`.
- [ ] **Step 4: Chạy verify** → PASSED.
- [ ] **Step 5: Commit** `"feat(slides): stat cards slide 2/9/20 — số liệu nổi bật"`.

---

### Task 4: Bảng mới + ảnh hòa nền trắng

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `add_table_slide` (120-145), `_add_pic` (154-162), `add_chart_slide` (164-200).

- [ ] **Step 1: Sửa `add_table_slide`** — header BLUE chữ trắng, hàng xen kẽ TABLE_ALT, chữ INK:

```python
    for r_i, row in enumerate(data):
        for c_i, val in enumerate(row):
            cell = tbl.cell(r_i, c_i)
            cell.fill.solid()
            cell.fill.fore_color.rgb = BLUE if r_i == 0 else (TABLE_ALT if r_i % 2 else BG)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            _r(r, 13, WHITE if r_i == 0 else INK, bold=(r_i == 0))
```
(Thêm hằng `WHITE = RGBColor(0xFF, 0xFF, 0xFF)` cho header chữ trắng.)

- [ ] **Step 2: Sửa `_add_pic`** — bỏ viền tối (xóa 2 dòng `pic.line.color...`), caption SUB.

- [ ] **Step 3: Chạy verify** → PASSED.
- [ ] **Step 4: Commit** `"refactor(slides): bảng header xanh + ảnh không viền"`.

---

### Task 5: Pipeline (slide 4) — box trắng viền xanh

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `add_flow_slide` (215-264) + bullets slide 4.

- [ ] **Step 1: Sửa box** — `box.fill.fore_color.rgb = TABLE_ALT` → `BOX_BG`; `box.line.color.rgb = CYAN` → `BLUE`; title `14, CYAN` → `14, BLUE`; lines `10, WHITE` → `10, INK`.
- [ ] **Step 2: Sửa bullets slide 4** — chuyển câu viết tắt B1-B4 thành câu đầy đủ + `**` keyphrase:

```python
    add_bullets(slide, [
        ("**Thu thập dữ liệu:** Crawler v2 xoay vòng 3 User-Agent, giới hạn tốc độ 1-3 giây, chạy 22 từ khóa trên 4 nguồn, thu về 1.193 tin", 0),
        ("Trích lọc theo 4 kỹ thuật (JSON-LD, __NEXT_DATA__, HTML, API) rồi lưu dạng raw CSV + JSON kèm siêu dữ liệu nguồn", 1),
        ("**Làm sạch & chuẩn hóa:** SalaryParser đọc 8 cấu trúc lương (56% tin ẩn lương), SkillNormalizer gộp 188 quy tắc thành 45 kỹ năng chuẩn", 0),
        ("ExperienceNormalizer gán 5 bậc kinh nghiệm từ entry đến lead; Deduplicator loại 70 bản ghi trùng qua 4 pha kiểm tra", 1),
        ("**Feature Engineering:** ColumnTransformer xử lý 3 nhóm đặc trưng — numeric (trung vị + chuẩn hóa), categorical (OneHot), ordinal", 0),
        ("Loại bỏ cột thô, mục tiêu là salary_mid tính bằng triệu VND mỗi tháng", 1),
        ("**Mô hình & gợi ý:** hồi quy giảm RMSE từ 8.97 xuống 4.17 (Linear) rồi 0.60 (Decision Tree)", 0),
        ("K-Means với k = 10 đạt Silhouette 0.38; cosine similarity gợi ý Top-3 việc phù hợp cho hồ sơ", 1),
    ], top=3.6, size=14)
```

- [ ] **Step 3: Chạy verify** → PASSED.
- [ ] **Step 4: Commit** `"refactor(slides): pipeline box trắng viền xanh + câu đầy đủ"`.

---

### Task 6: SHAP + chart slides — caption và bullets câu đầy đủ

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `add_shap_slide` (275-287), caption các slide chart (7, 11, 14, 16, 19).

- [ ] **Step 1: Sửa `add_shap_slide`** — bullets text câu đầy đủ (giữ 3 bullet/slide, thêm `**`):

```python
    add_shap_slide(prs, "SHAP — Giải thích mô hình Decision Tree", "shap_tree_summary.png",
                   "SHAP summary plot (nguồn: scripts/generate_shap_plots.py)", [
        ("**TreeExplainer** tính đóng góp của 21 đặc trưng cho từng tin trong 105 tin kiểm thử (20% tập dữ liệu)", 0),
        ("**experience_years** và nhóm kỹ năng đóng góp lớn nhất — kinh nghiệm là yếu tố quyết định mức lương", 0),
        ("Đỏ đẩy lương lên, xanh kéo lương xuống — độ trải rộng của điểm màu phản ánh tác động phi tuyến của Decision Tree", 0),
    ], num=13)
```

```python
    add_shap_slide(prs, "SHAP — Giải thích mô hình Linear Regression", "shap_linear_summary.png",
                   "SHAP summary plot (nguồn: scripts/generate_shap_plots.py)", [
        ("**LinearExplainer** tính SHAP bằng hệ số nhân giá trị đặc trưng — quan hệ 1:1, dễ đọc trên 105 tin kiểm thử", 0),
        ("Các đặc trưng quan trọng nhất **khớp với Decision Tree** — kết quả ổn định giữa 2 mô hình", 0),
        ("Độ lớn SHAP là đóng góp tuyệt đối vào lương (triệu VND) — so sánh trực tiếp được độ quan trọng giữa các đặc trưng", 0),
    ], num=17)
```

- [ ] **Step 2: Sửa caption chart slides** — caption câu đầy đủ (giữ ngắn, bỏ nguồn viết tắt):
  - Slide 7: `"Missing values (nguồn: notebook 02)"` → `"Tỷ lệ giá trị thiếu của các cột dữ liệu"`; `"Phân bố kinh nghiệm yêu cầu (nguồn: notebook 02)"` → `"Phân bố số năm kinh nghiệm yêu cầu trong tin tuyển dụng"`.
  - Slide 11: `"Phân bố nhóm kỹ năng (nguồn: notebook 03)"` → `"Tỷ lệ tin tuyển dụng theo từng nhóm kỹ năng"`; `"Top 20 kỹ năng được yêu cầu (nguồn: notebook 03)"` → `"20 kỹ năng được nhà tuyển dụng yêu cầu nhiều nhất"`; `"Lương trung bình theo tiếng Anh (nguồn: notebook 03)"` → `"Lương trung bình ở tin có và không yêu cầu tiếng Anh"`.
  - Slide 14: `"Residuals — dự đoán vs thực tế (nguồn: notebook 04)"` → `"Sai số dự đoán (residual) phân bố quanh mức 0"`; `"So sánh RMSE / MAE / R² của 4 mô hình (nguồn: notebook 04)"` → `"So sánh độ chính xác RMSE, MAE, R² giữa 4 mô hình"`.
  - Slide 16: `"Silhouette Score k = 2..10 (nguồn: notebook 04)"` → `"Silhouette Score khi khảo sát số cụm k từ 2 đến 10"`; `"PCA 2D — 10 cụm trên không gian 2 chiều (nguồn: notebook 04)"` → `"10 cụm thị trường nhìn trên không gian 2 chiều sau PCA"`.
  - Slide 19: `"Phân bố similarity của hồ sơ với các việc (nguồn: notebook 04)"` → `"Điểm tương đồng (similarity) giữa hồ sơ demo và các việc trong kho"`.

- [ ] **Step 3: Chạy verify** → PASSED.
- [ ] **Step 4: Commit** `"refactor(slides): SHAP + caption chart thành câu đầy đủ"`.

---

### Task 7: Text toàn bộ slide còn lại thành câu đầy đủ (không viết vắt tắt)

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `build()` bullets: slide 2, 5, 6, 8, 10, 12 (note), 15 (note), 18 (note), 20, 21, 3 (bảng RQ), 9 (note).

**Interfaces:**
- Consumes: `_rich_para` (Task 2) — mọi bullets giờ hỗ trợ `**...**`.
- Produces: nội dung bullets hoàn chỉnh cho 22 slide.

- [ ] **Step 1: Slide 2 — câu đầy đủ + stat cards đã có:**

```python
    s2 = add_content_slide(prs, "Giới thiệu bài toán", [
        ("Thị trường IT Việt Nam đang phát triển nhanh, nhu cầu tuyển dụng tập trung tại Hà Nội, TP.HCM và Đà Nẵng", 0),
        ("Tin tuyển dụng phân tán trên nhiều nền tảng với định dạng tự do — ứng viên rất khó so sánh lương và kỹ năng giữa các nguồn", 0),
        ("Bốn nền tảng lớn (Itviec, Glints, TopCV, Careerviet) đăng tin theo các dạng khác nhau nên dữ liệu thu về không đồng nhất", 0),
        ("**Mục tiêu của đề tài** — xây dựng một pipeline xử lý dữ liệu trọn vẹn:", 0),
        ("Thu thập tự động tin tuyển dụng IT từ 4 nguồn bằng Crawler v2", 1),
        ("Làm sạch và chuẩn hóa lương, kỹ năng, kinh nghiệm về cùng một định dạng", 1),
        ("Dự báo mức lương thị trường bằng 4 mô hình ML (Baseline, Linear, Decision Tree, Random Forest)", 1),
        ("Phân cụm thị trường bằng K-Means và gợi ý việc làm phù hợp với hồ sơ (Content-based)", 1),
    ], num=2)
    _stat_cards(s2, [
        {"emoji": "🗂️", "value": "1.193", "label": "tin tuyển dụng"},
        {"emoji": "🌐", "value": "4", "label": "nguồn dữ liệu"},
        {"emoji": "📋", "value": "44", "label": "thuộc tính"},
        {"emoji": "🔒", "value": "56%", "label": "tin ẩn lương"},
    ], top=6.55)
```
(Lưu ý: slide 2 có 8 bullets → để không chạm card ở 6.55, bullets top=1.4 height=5.6 sẽ chạm; giảm size bullets slide 2 xuống 15, hoặc giảm 1 bullet level 0. Chọn: giữ 8 bullets, đổi call `add_content_slide` → gọi `add_bullets(s2, [...], top=1.4, size=15)`.)

- [ ] **Step 2: Slide 5 (Crawler) — câu đầy đủ:**

```python
    add_content_slide(prs, "Crawler v2 — Thu thập dữ liệu", [
        ("Crawler chạy vòng lặp qua từng nguồn và từ khóa (22 từ khóa), dừng khi đủ số tin tối thiểu, lịch sử ghi vào crawl_history.json", 0),
        ("**HttpClient (httpx)** bật xác thực SSL, tự động theo redirect và timeout 20 giây để hạn chế lỗi kết nối bị chặn", 0),
        ("**Chống chặn:** xoay vòng 3 User-Agent, giới hạn tốc độ 1-3 giây, thử lại khi máy chủ trả HTTP 429", 0),
        ("Nhận diện trang bị chặn qua danh sách BLOCKED_MARKERS (captcha, cf-challenge)", 0),
        ("**4 kỹ thuật trích xuất** dữ liệu từ trang:", 0),
        ("JSON-LD Parsing — đọc dữ liệu nhúng trong thẻ script application/ld+json", 1),
        ("__NEXT_DATA__ Extraction — lấy JSON state của trang web Next.js", 1),
        ("HTML Parsing bằng BeautifulSoup cho các trang tĩnh", 1),
        ("API JSON — gọi trực tiếp endpoint trả dữ liệu", 1),
        ("Lưu dữ liệu thô dạng CSV + JSON theo từng nguồn vào data/raw/, kèm log siêu dữ liệu", 0),
    ], num=5)
```

- [ ] **Step 3: Slide 6 (Cleaning) — câu đầy đủ:**

```python
    add_content_slide(prs, "Làm sạch & Chuẩn hóa dữ liệu", [
        ("**SalaryParser** nhận diện 8 cấu trúc lương bằng 6 regex, đổi USD sang VND (×25.000), quy lương năm về tháng", 0),
        ("56% tin ẩn lương (24+ từ khóa như cạnh tranh, thỏa thuận) — khoảng \"tới X\" ≈ 70%, \"từ X\" ≈ 130% quy về điểm giữa", 1),
        ("**SkillNormalizer** gộp 188 quy tắc đồng nghĩa thành 45 kỹ năng chuẩn thuộc 12 nhóm, khớp mờ ngưỡng > 0.8 (độ phủ 6.6%)", 0),
        ("**ExperienceNormalizer** gán 5 bậc kinh nghiệm (entry đến lead) bằng 6 regex tiếng Việt và tiếng Anh", 0),
        ("**Deduplicator** loại 70 bản ghi trùng qua 4 pha: job_id, title + company, khớp mờ title/desc", 0),
        ("Kết quả: bộ dữ liệu 1.193 tin sạch, lương, kỹ năng, kinh nghiệm chuẩn hóa đồng nhất", 1),
    ], num=6)
```

- [ ] **Step 4: Slide 8 (Feature Engineering) — câu đầy đủ:**

```python
    add_content_slide(prs, "Feature Engineering", [
        ("**3 nhóm đặc trưng** trong ColumnTransformer [3]:", 0),
        ("Numeric (experience_years): điền giá trị thiếu bằng trung vị rồi chuẩn hóa về phân phối chuẩn", 1),
        ("Categorical (city, job_type, remote_option, education_level, industry, company_size): điền \"Unknown\" khi thiếu, OneHotEncoder bỏ qua giá trị mới lạ", 1),
        ("Ordinal (experience_bin từ entry đến lead): giữ thứ tự qua OrdinalEncoder, giá trị thiếu gán -1", 1),
        ("**Biến mục tiêu** là salary_mid (triệu VND/tháng)", 0),
        ("Loại cột thô (job_id, description, source_url...); ColumnTransformer dùng remainder=\"drop\"", 0),
        ("Chia dữ liệu 80/20 và đánh giá 5-fold cross-validation để ước lượng độ ổn định của mô hình", 0),
    ], num=8)
```

- [ ] **Step 5: Slide 10 (EDA) — câu đầy đủ:**

```python
    add_content_slide(prs, "Phân tích khám phá dữ liệu (EDA)", [
        ("**F1 — Nhóm kỹ năng** Data Science & Lập trình xuất hiện nhiều nhất trong 1.193 tin", 0),
        ("Top kỹ năng được yêu cầu: JavaScript, React, Kafka, Python, SQL, Docker, Spring Boot, TensorFlow", 1),
        ("**F2 — Lương tăng theo bậc kinh nghiệm:** Entry ~10M → Mid ~17M → Senior ~28M → Lead ~35M+", 0),
        ("TP.HCM & Hà Nội có lương trung bình cao hơn rõ rệt so với các thành phố khác", 1),
        ("**F3 — Yêu cầu tiếng Anh:** lương trung bình của tin yêu cầu tiếng Anh cao hơn ~30%", 0),
        ("**F4 — Vị trí cấp cao** (Senior, Manager, Lead) ẩn lương với tỷ lệ >50%", 0),
    ], num=10)
```

- [ ] **Step 6: Note các slide 12, 15, 18 — câu đầy đủ:**

```python
    add_table_slide(prs, "Kết quả mô hình dự báo lương", ML_RESULTS_TABLE, num=12,
                    col_widths=[4.5, 2.5, 2.5, 2.6],
                    note="Linear giảm RMSE 53.5%, Decision Tree giảm 93.3% so với Baseline trung bình. 12 sai số lớn nhất đều dưới 2.1 triệu VND. Residual phân bố quanh mức 0 (std ≈ 0.6M) nên dự đoán không thiên lệch. Random Forest học vẹt (overfit) trên tập dữ liệu hiện tại.")
```
```python
    add_table_slide(prs, "Phân cụm thị trường (K-Means)", CH3_CLUSTER_TABLE, num=15,
                    col_widths=[1.5, 1.5, 1.8, 2.2, 5.1],
                    note="Khảo sát số cụm k từ 2 đến 10, chọn k = 10 với Silhouette Score 0.38. Năm phân khúc đặc trưng: Junior-Mid Hà Nội 15.1M, Mid-Senior TP.HCM 27.1M, Senior 41.9M, Mid đa dạng 20.8M, Remote 31.6M.")
```
```python
    add_table_slide(prs, "Hệ thống gợi ý việc làm (Content-based)", CH3_REC_TABLE, num=18,
                    col_widths=[3.2, 1.8, 4.1, 3.0],
                    note="Kỹ năng được mã hóa thành ma trận 1500 việc × 45 kỹ năng. Hệ thống lọc theo thành phố và kinh nghiệm ±0.5 năm trước khi tính cosine để giảm nhiễu. Demo hồ sơ [Python, SQL, Machine Learning] → Top-3: Data Scientist 1.0, ML Engineer 0.67, Data Engineer 0.67.")
```

- [ ] **Step 7: Slide 20 (Kết luận) + slide 21 (Hạn chế) — câu đầy đủ:**

```python
    s20 = add_content_slide(prs, "Kết luận", [
        ("Pipeline khoa học dữ liệu end-to-end hoàn chỉnh, đáp ứng đủ các tiêu chí của học phần", 0),
        ("**Hồi quy:** RMSE giảm từ 8.97 (Baseline) xuống 4.17 (Linear, R² 0.783) rồi 0.60 (Decision Tree, R² 0.996)", 0),
        ("**SHAP xác nhận** kinh nghiệm và nhóm kỹ năng là nhân tố chính quyết định lương, nhất quán giữa 2 mô hình", 0),
        ("**K-Means** k = 10 (Silhouette 0.38) nhận diện 5 phân khúc thị trường rõ rệt", 0),
        ("**Content-based** gợi ý Top-3 việc phù hợp kèm kỹ năng còn thiếu", 0),
        ("Toàn bộ RQ1-RQ5 được trả lời qua EDA (F1-F4), SHAP và hệ gợi ý", 0),
    ], num=20)
    _stat_cards(s20, [
        {"emoji": "🎯", "value": "RMSE 0.60", "label": "Decision Tree"},
        {"emoji": "📈", "value": "R² 0.996", "label": "Decision Tree"},
        {"emoji": "💎", "value": "0.38", "label": "Silhouette k=10"},
        {"emoji": "🎖️", "value": "Top-3", "label": "việc phù hợp"},
    ], top=6.55, size=24)
```
```python
    add_content_slide(prs, "Hạn chế & Hướng phát triển", [
        ("**Hạn chế của dữ liệu và mô hình:**", 0),
        ("Kỹ năng chi tiết chỉ xuất hiện trong 6.6% tin — giới hạn từ nguồn dữ liệu, ảnh hưởng đến độ chính xác của đặc trưng kỹ năng", 1),
        ("Dữ liệu thiên lệch địa lý: TP.HCM chiếm ~50% tin trong khi Đà Nẵng chỉ ~4% — chưa đại diện đồng đều cho cả thị trường", 1),
        ("Decision Tree và Random Forest overfit trên tập hiện tại; dùng salary midpoint (điểm giữa khoảng) thay vì lương thực tế do 56% tin ẩn lương", 1),
        ("**Hướng phát triển trong tương lai:**", 0),
        ("Crawler truy cập sâu vào trang chi tiết từng tin, mở rộng số nguồn và cập nhật dữ liệu theo thời gian", 1),
        ("Dùng NLP/BERT trích xuất đặc trưng ngữ nghĩa từ mô tả công việc — tận dụng nguồn thông tin thay cho kỹ năng bị ẩn", 1),
        ("Thử DBSCAN / Hierarchical Clustering và Hybrid Recommendation (collaborative + content-based)", 1),
    ], num=21)
```

- [ ] **Step 8: Slide 3 (bảng RQ) + slide 9 (note) — câu đầy đủ:** bảng RQ giữ nguyên (câu đã đủ); note slide 9 giữ nguyên.
- [ ] **Step 9: Chạy verify** → PASSED.
- [ ] **Step 10: Commit** `"refactor(slides): toàn bộ bullets thành câu đầy đủ, không viết vắt tắt"`.

---

### Task 8: Verify mở rộng + preview thủ công + commit

**Files:**
- Modify: `scripts/generate_pptx_slides.py` — `verify()` (508-572).

- [ ] **Step 1: Thêm check vào `verify()`:** sau check ảnh bounds:

```python
    # Nền trắng: không còn màu nền tối cũ trong slide (kiểm tra fill của 2 slide bất kỳ)
    from pptx.util import Emu
    for idx in (0, 5):
        slide_bg = slides[idx].background.fill
        if slide_bg.type is not None and slide_bg.fore_color.type is not None:
            c = slide_bg.fore_color.rgb
            if c == RGBColor(0x1E, 0x1E, 0x2E):
                issues.append(f"Slide {idx + 1} vẫn dùng nền tối cũ")
    # Stat cards: slide 2, 9, 20 mỗi slide ≥ 4 shape là hình chữ nhật (stat card)
    for idx in (1, 8, 19):
        n_rect = sum(1 for sh in slides[idx].shapes
                     if sh.shape_type == MSO_SHAPE_TYPE.RECTANGLE)
        if n_rect < 4:
            issues.append(f"Slide {idx + 1} thiếu stat cards (rect < 4)")
```

- [ ] **Step 2: Chạy verify** → PASSED. Chạy `python scripts/inspect_slides.py` → không dòng "CÓ THỂ TRÀN".
- [ ] **Step 3: Export preview 4 slide đại diện (1, 4, 9, 13) qua PowerPoint COM:**

```powershell
New-Item -ItemType Directory -Force reports/slides/preview | Out-Null
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("$PWD\reports\slides\TrinhBay_ChuyenDe4.pptx", $true, $true, $false)
foreach ($idx in 1, 4, 9, 13) {
    $s = $pres.Slides($idx)
    $s.Export("$PWD\reports\slides\preview\slide$idx.png", "PNG", 1280, 720)
}
$pres.Close(); $pp.Quit()
```

- [ ] **Step 4: Read 4 PNG** — kiểm tra: nền trắng, title bar badge đúng section, stat cards slide 9 hiển thị đủ, SHAP slide 13 hòa nền. Nếu có lỗi trực quan → sửa rồi lặp Step 2-4.
- [ ] **Step 5: Commit tổng:**
```bash
git add scripts/generate_pptx_slides.py
git commit -m "feat(slides): redesign nền trắng — stat cards, badge, icon, rich-text, câu đầy đủ"
```

- [ ] **Step 6: Báo cáo** — tổng kết 8 task, verify PASSED, preview OK; hỏi user giữ/xóa thư mục preview.

---

## Self-Review Notes

- **Spec coverage:** bảng màu (T1) · badge+icon title (T1) · stat cards (T3) · rich-text (T2) · bảng mới (T4) · pipeline (T5) · SHAP/caption (T6) · câu đầy đủ toàn bộ (T7) · verify mở rộng + preview (T8). Icons emoji theo slide: đặt trong tiêu đề qua param — giữ đơn giản: emoji chỉ ở stat cards + badge, không thêm icon riêng từng slide (tránh 22 slide icon rời lộn xộn; spec cho phép, YAGNI).
- **Placeholder scan:** không có TBD; mọi step có code đầy đủ.
- **Type consistency:** `_stat_cards(slide, cards, top, left, width, size)` — slide 20 dùng `size=24`; `add_table_slide` thêm param `note_top`; `add_bullets` giữ signature cũ.
