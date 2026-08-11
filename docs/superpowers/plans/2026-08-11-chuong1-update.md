# Cập nhật Chương 1 + Công thức OMML + Tài liệu tham khảo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mở rộng Chương 1 (cơ sở lý thuyết + tính khả dụng) trong `scripts/generate_docx_report.py`, thêm builder công thức OMML, hệ trích dẫn [1]–[10], và thay mục TÀI LIỆU THAM KHẢO cũ bằng danh sách mới, kèm verify mở rộng.

**Architecture:** Giữ nguyên kiến trúc 1-file hiện có. Thay `FULL_CONTENT["CHƯƠNG 1 ..."]` bằng cấu trúc 3 mục lớn (1.1, 1.2 với 4 nhóm con 1.2.1–1.2.4, 1.3). Thêm `make_math_paragraph()` sinh `<m:oMathPara>` OMML. Thêm `REFERENCES` list. Thêm section `("TÀI LIỆU THAM KHẢO", REFERENCE_ITEMS)` vào `sections` — `clear_existing_subsections_after` đã tự xóa nội dung ResNet50 cũ. Mở rộng `verify_report()`.

**Tech Stack:** Python 3, `python-docx`, lxml XML manipulation (không thêm thư viện).

## Global Constraints

- KHÔNG thêm thư viện mới; `requirements.txt` không đổi.
- Không tách module — mọi thay đổi ở `scripts/generate_docx_report.py`.
- Không đổi nội dung Chương 2, Chương 3, LỜI MỞ ĐẦU, KẾT LUẬN.
- Nội dung viết tiếng Việt, giọng học thuật.
- Mọi text chèn vào phải dùng font `Times New Roman`; tiêu đề phụ 13pt bold, thân bài 12pt.
- Công thức fallback: text thuần in nghiêng nếu OMML không biểu diễn được — không crash script.
- Verify giữ nguyên các checks cũ (5 headings, key phrases, ML table, không còn resnet50/rác thải).

---

### Task 1: Thêm builder OMML `make_math_paragraph`

**Files:**
- Modify: `scripts/generate_docx_report.py` (thêm hàm sau `insert_table_after_paragraph`, trước `find_paragraph_by_text` ~ dòng 106–124)

**Interfaces:**
- Consumes: `insert_paragraph_after()` (Task trước, đã có), `docx.oxml.OxmlElement`
- Produces: `make_math_paragraph(doc, anchor_p, segments)` — chèn 1 paragraph công thức OMML sau `anchor_p`; segments là list tuple `(text, kind)`; kind ∈ `{"t" (text thường), "i" (italic), "f" (frac: text dạng "tử/mẫu"), "b" (bold)}`. Trả về Paragraph mới.

- [ ] **Step 1: Viết hàm `make_math_paragraph`**

```python
MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

def _m_elem(tag, ns=MATH_NS):
    return docx.oxml.OxmlElement('m:' + tag, nsmap={'m': ns})

def _m_run(text, italic=False, bold=False):
    """Tạo <m:r> với <m:t>."""
    r = _m_elem('r')
    rpr = _m_elem('rPr')
    if italic:
        rpr.append(docx.oxml.OxmlElement('w:i'))
    if bold:
        rpr.append(docx.oxml.OxmlElement('w:b'))
    r.append(rpr)
    t = _m_elem('t')
    t.text = text
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    r.append(t)
    return r

def _m_frac(num_segs, den_segs):
    """Tạo <m:f> với num/den (mỗi cái là list của (text, kind))."""
    f = _m_elem('f')
    num = _m_elem('num')
    for txt, kind in num_segs:
        num.append(_m_run(txt, italic=(kind == 'i'), bold=(kind == 'b')))
    den = _m_elem('den')
    for txt, kind in den_segs:
        den.append(_m_run(txt, italic=(kind == 'i'), bold=(kind == 'b')))
    f.append(num)
    f.append(den)
    return f

def make_math_paragraph(doc, anchor_p, segments):
    """Chèn 1 paragraph công thức OMML sau anchor_p.

    segments: list các phần tử, mỗi phần tử là:
        ("text", "t"|"i"|"b")   -> run thường/italic/bold
        ("tử/mẫu", "f")          -> phân số (num=tử, den=mẫu)
    """
    p_elem = docx.oxml.OxmlElement('w:p')
    anchor_p._p.addnext(p_elem)

    omath_para = _m_elem('oMathPara')
    omath = _m_elem('oMath')
    for text, kind in segments:
        if kind == 'f' and '/' in text:
            num_str, den_str = text.split('/', 1)
            omath.append(_m_frac([(num_str, 't')], [(den_str, 't')]))
        else:
            omath.append(_m_run(text, italic=(kind == 'i'),
                                bold=(kind == 'b')))
    omath_para.append(omath)
    p_elem.append(omath_para)

    # Định dạng paragraph giống body: TNR 12pt, canh giữa
    p = docx.text.paragraph.Paragraph(p_elem, doc)
    p.style = doc.styles['Normal']
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(8)
    return p
```

- [ ] **Step 2: Smoke-test import & chạy thử trong python nguyên thủy**

Run:
```
cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu
python -c "import sys; sys.path.insert(0,'scripts'); import generate_docx_report as g; print('ok', hasattr(g,'make_math_paragraph'))"
```
Expected: `ok True` (không lỗi syntax/import). Nếu lỗi (vd `OxmlElement` signature khác), sửa `_m_elem` cho khớp — tham khảo `help(docx.oxml.OxmlElement)`.

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat: add OMML math paragraph builder"
```

---

### Task 2: Thêm `REFERENCES` + `REFERENCE_ITEMS` + mở rộng `MAIN_HEADINGS`/`sections`

**Files:**
- Modify: `scripts/generate_docx_report.py` — sau `ML_RESULTS_TABLE` (dòng ~78), sửa `sections` trong `generate_report()` (dòng ~281–287)

**Interfaces:**
- Consumes: `FULL_CONTENT` (Task 3 sẽ sửa), `clear_existing_subsections_after`
- Produces: `REFERENCES` (list 10 str), `REFERENCE_ITEMS` (list 10 str `"[n] ..."`); `sections` list có thêm `("TÀI LIỆU THAM KHẢO", REFERENCE_ITEMS)` ở cuối.

- [ ] **Step 1: Thêm `REFERENCES` sau `ML_RESULTS_TABLE`**

```python
REFERENCES = [
    "Géron, A. (2022). Hands-On Machine Learning with Scikit-Learn, Keras & TensorFlow (3rd ed.). O'Reilly Media.",
    "James, G., Witten, D., Hastie, T., & Tibshirani, R. (2021). An Introduction to Statistical Learning (2nd ed.). Springer.",
    "Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
    "Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5–32.",
    "Quinlan, J. R. (1986). Induction of Decision Trees. Machine Learning, 1(1), 81–106.",
    "MacQueen, J. (1967). Some Methods for Classification and Analysis of Multivariate Observations. Proceedings of the 5th Berkeley Symposium.",
    "Rousseeuw, P. J. (1987). Silhouettes: A Graphical Aid to the Interpretation and Validation of Cluster Analysis. Journal of Computational and Applied Mathematics, 20, 53–65.",
    "Ricci, F., Rokach, L., & Shapira, B. (2022). Recommender Systems Handbook (3rd ed.). Springer.",
    "McKinney, W. (2022). Python for Data Analysis: Data Wrangling with Pandas, NumPy, and IPython (3rd ed.). O'Reilly Media.",
    "Beautiful Soup Developers. (2024). Beautiful Soup Documentation. https://www.crummy.com/software/BeautifulSoup/",
]
REFERENCE_ITEMS = [f"[{i}] {ref}" for i, ref in enumerate(REFERENCES, 1)]
```

- [ ] **Step 2: Thêm section TÀI LIỆU THAM KHẢO vào `generate_report()`**

Trong `generate_report()`, mở rộng `sections`:

```python
    sections = [
        ("LỜI MỞ ĐẦU", FULL_CONTENT["LỜI MỞ ĐẦU"]),
        ("TỔNG QUAN VỀ BÀI TOÁN VÀ CƠ SỞ LÝ THUYẾT", FULL_CONTENT["CHƯƠNG 1 TỔNG QUAN VỀ BÀI TOÁN VÀ CƠ SỞ LÝ THUYẾT"]),
        ("PHƯƠNG PHÁP NGHIÊN CỨU VÀ DỮ LIỆU ĐẦU VÀO", FULL_CONTENT["CHƯƠNG 2 PHƯƠNG PHÁP NGHIÊN CỨU VÀ DỮ LIỆU ĐẦU VÀO"]),
        ("QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ", FULL_CONTENT["CHƯƠNG 3 QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ"]),
        ("KẾT LUẬN", FULL_CONTENT["KẾT LUẬN"]),
        # LƯU Ý: REFERENCE_ITEMS phải wrap thành list tuple (item, "") — vì insert_content_after_paragraph duyệt for sub_title, sub_body in content_list
        ("TÀI LIỆU THAM KHẢO", [(item, "") for item in REFERENCE_ITEMS]),
    ]
```

- [ ] **Step 3: Chạy script toàn phần (tạm — chưa có nội dung chương 1 mới vẫn chạy được)**

Run: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu && python scripts/generate_docx_report.py`
Expected: không crash; cuối cùng in `VERIFICATION PASSED` hoặc liệt kê issue (issue về phrase mới chưa có vì verify chưa cập nhật — chấp nhận). Ít nhất phải có dòng `-> Cleared ...` cho TÀI LIỆU THAM KHẢO và không có Traceback.

- [ ] **Step 4: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat: add REFERENCES list and references section"
```

---

### Task 3: Viết nội dung Chương 1 mới (3 mục lớn, 4 nhóm lý thuyết + trích dẫn)

**Files:**
- Modify: `scripts/generate_docx_report.py` — thay toàn bộ `FULL_CONTENT["CHƯƠNG 1 TỔNG QUAN VỀ BÀI TOÁN VÀ CƠ SỞ LÝ THUYẾT"]` (hiện là list 2 tuple, dòng ~40–45)

**Interfaces:**
- Consumes: cấu trúc `content_list` hiện tại (list các `(sub_title, sub_body)` tuple) — `insert_content_after_paragraph` duyệt theo đúng format này
- Produces: danh sách các subsection mới — **quan trọng**: `insert_content_after_paragraph` hiện chỉ chèn text thuần; script phải được sửa để nhận biết công thức (xem Task 4)

Nội dung (viết đầy đủ, academic, có `[n]`):

```python
FULL_CONTENT = {
    # ... giữ nguyên LỜI MỞ ĐẦU, CHƯƠNG 2, CHƯƠNG 3, KẾT LUẬN ...
    "CHƯƠNG 1 TỔNG QUAN VỀ BÀI TOÁN VÀ CƠ SỞ LÝ THUYẾT": [
        ("1.1. Bối cảnh, Đặt vấn đề và Tính cấp thiết của đề tài",
         "Thị trường công nghệ thông tin (IT) Việt Nam đang trong giai đoạn tăng trưởng nhanh với nhu cầu nhân lực lớn... "
         "Tuy nhiên, thị trường đối mặt nghịch lý mất cân đối cung-cầu thông tin: dữ liệu tuyển dụng phân tán trên nhiều nền tảng "
         "(Itviec, Glints, TopCV, Careerviet) với định dạng phi cấu trúc (unstructured text) không đồng nhất, khiến ứng viên khó định giá năng lực, "
         "khó nhận diện kỹ năng cốt lõi và khó định hướng lộ trình học tập. Từ đó, đề tài đặt ra 5 câu hỏi nghiên cứu (RQ1): xu hướng kỹ năng nào đang được yêu cầu? "
         "(RQ2) Lương biến động theo kinh nghiệm, thành phố, kỹ năng như thế nào? (RQ3) Có thể dự báo lương từ dữ liệu tuyển dụng không và độ chính xác ra sao? "
         "(RQ4) Thị trường phân khúc thành những nhóm việc làm nào? (RQ5) Làm thế nào gợi ý việc làm phù hợp với hồ sơ kỹ năng? "
         "Các câu hỏi này được trả lời lần lượt trong Chương 3 (mục F1–F4). Giá trị ứng dụng: hỗ trợ ứng viên định giá năng lực, "
         "nhà tuyển dụng tối ưu mức lương cạnh tranh, và nền tảng giáo dục xây dựng lộ trình học tập dựa trên dữ liệu thực."),
        ("1.2. Cơ sở Lý thuyết về Phân tích Dữ liệu và Học máy",
         "Đề tài tuân thủ quy trình Khoa học Dữ liệu 9 bước tiêu chuẩn, từ thu thập, làm sạch, phân tích khám phá đến mô hình hóa và triển khai [1]. "
         "Nội dung lý thuyết được chia thành 4 nhóm tương ứng với bốn giai đoạn chính của pipeline: tiền xử lý dữ liệu phi cấu trúc, hồi quy học có giám sát, "
         "phân cụm không giám sát, và hệ gợi ý dựa trên nội dung."),
        ("1.2.1. Tiền xử lý dữ liệu phi cấu trúc (Unstructured Data Preprocessing)",
         "Dữ liệu tuyển dụng là dạng văn bản tự do, chứa nhiều biến thể ngôn ngữ và định dạng. Theo McKinney [9], làm sạch dữ liệu chiếm phần lớn thời gian "
         "trong pipeline phân tích dữ liệu. Đề tài xây dựng 4 thành phần tiền xử lý: (1) SalaryParser dùng 6 biểu thức chính quy để nhận diện 8 loại cấu trúc lương "
         "(RANGE, UP_TO, FROM, YEARLY, USD, HIDDEN, SINGLE, UNKNOWN); quy đổi USD sang VND với tỷ giá 25.000, lương năm chia 12 tháng, khoảng 'tới X' lấy mức giữa bằng 70% max, "
         "'từ X' lấy 130% min; (2) SkillNormalizer dùng từ điển 188 quy tắc đồng nghĩa chuẩn hóa về 45 kỹ năng, kết hợp fuzzy matching (Levenshtein) ngưỡng > 0.8 cho biến thể lỗi chính tả; "
         "(3) ExperienceNormalizer parse số năm kinh nghiệm từ nhiều định dạng TV/EN và xếp vào 5 bậc (entry, junior, mid, senior, lead); "
         "(4) Deduplicator triển khai 4 pha khử trùng lặp (exact job_id, exact title+company, fuzzy title ngưỡng 0.8, fuzzy description ngưỡng 0.7) đã loại bỏ 70 bản ghi trùng [1]. "
         "Kết quả thực tế: tỷ lệ ẩn lương là 56%, chỉ 6.6% tin có kỹ năng chi tiết — phản ánh giới hạn hiển thị của nguồn dữ liệu, được xử lý bằng gán cờ is_hidden và cột salary_mid."),
        ("1.2.2. Hồi quy học có giám sát (Supervised Regression)",
         "Hồi quy là bài toán học có giám sát dự đoán một biến liên tục từ tập đặc trưng đầu vào [2]. Mô hình hồi quy tuyến tính giả định quan hệ tuyến tính giữa đặc trưng và mục tiêu [2]:"),
        # Công thức 1: y = β₀ + β₁x₁ + … + βₙxₙ
        ("__MATH__ y = β0 + β1x1 + … + βnxn ; t",
         ""),
        ("",
         "Để đo chất lượng mô hình, đề tài sử dụng ba chỉ số sai số [1][3]: MSE, RMSE và R²."),
        # Công thức 2: MSE = (1/n)∑(yᵢ − ŷᵢ)²
        ("__MATH__ MSE = (1/n) ∑(y_i − ŷ_i)² ; t", ""),
        # Công thức 3: RMSE = √MSE
        ("__MATH__ RMSE = √MSE ; t", ""),
        # Công thức 4: R² = 1 − (∑(yᵢ − ŷᵢ)²)/(∑(yᵢ − ȳ)²)
        ("__MATH__ R² = 1 − (∑(y_i − ŷ_i)²) / (∑(y_i − ȳ)²) ; t", ""),
        ("",
         "Trong đó yᵢ là giá trị thực, ŷᵢ giá trị dự đoán, ȳ trung bình thực. R² ∈ (−∞,1], gần 1 nghĩa là mô hình giải thích tốt phương sai dữ liệu [2]. "
         "Trên thực tế, đề tài dùng cây quyết định (Decision Tree) với max_depth=10, min_samples_leaf=5 và rừng ngẫu nhiên (Random Forest, n_estimators=100, "
         "max_depth=15, min_samples_leaf=4) [4][5]. Pipeline đặc trưng dùng ColumnTransformer: imputer median + StandardScaler cho cột số, OneHotEncoder cho cột phân loại, "
         "OrdinalEncoder cho bậc kinh nghiệm; 7 nhóm đặc trưng (experience_years, city, job_type, remote_option, education_level, industry, company_size, experience_bin). "
         "Dữ liệu chia 80/20 với 5-fold cross-validation. Kết quả: Baseline RMSE 8.97, R² −0.010; Random Forest đạt ~1.0 R² (chi tiết bảng Chương 3)."),
        ("1.2.3. Phân cụm không giám sát (K-Means Clustering)",
         "Phân cụm nhóm các quan sát đồng dạng mà không cần nhãn [3]. K-Means tối thiểu hóa tổng bình phương khoảng cách đến tâm cụm [6]:"),
        # Công thức 5: J = Σₖ Σₓ ‖x − μₖ‖²
        ("__MATH__ J = ∑_k ∑_x ‖x − μ_k‖² ; t", ""),
        ("",
         "Để đánh giá chất lượng phân cụm, chỉ số Silhouette do Rousseeuw [7] đề xuất:"),
        # Công thức 6: s(i) = (b(i) − a(i))/max(a(i), b(i))
        ("__MATH__ s(i) = (b(i) − a(i)) / max(a(i), b(i)) ; t", ""),
        ("",
         "Trong đó a(i) là khoảng cách trung bình từ i đến các điểm cùng cụm, b(i) đến cụm gần nhất khác; s(i) ∈ [−1,1], >0 nghĩa là cụm tách biệt tốt [7]. "
         "Thực nghiệm khảo sát k từ 2 đến 10 chọn k=5 với Silhouette 0.38; dữ liệu được chuẩn hóa StandardScaler trước khi K-Means (n_init=10, random_state=42) "
         "và trực quan hóa qua PCA 2 chiều. Kết quả 5 phân khúc: Junior-Mid Hà Nội (15.1M), Mid-Senior TP.HCM (27.1M), Senior thu nhập cao (41.9M), "
         "việc phổ thông (20.8M), Remote (31.6M)."),
        ("1.2.4. Hệ gợi ý dựa trên nội dung (Content-based Recommendation)",
         "Hệ gợi ý dựa trên nội dung xây dựng hồ sơ người dùng từ các đặc trưng của mục đã tương tác và gợi ý mục tương tự [8]. "
         "Trong đề tài, hồ sơ là vector kỹ năng nhị phân của ứng viên, so với ma trận job×skill dùng MultiLabelBinarizer; độ tương đồng Cosine giữa hai vector A, B [8]:"),
        # Công thức 7: cos(A,B) = (A·B)/(|A||B|)
        ("__MATH__ cos(A,B) = (A·B) / (|A||B|) ; t", ""),
        ("",
         "Điểm tương đồng cao nghĩa là job có nhiều kỹ năng trùng với hồ sơ ứng viên. Hệ thống hỗ trợ lọc theo thành phố (case-insensitive) và kinh nghiệm "
         "(±0.5 năm, fallback experience_bin), trả về Top-N kèm danh sách matched/missing skills để ứng viên nhận diện kỹ năng cần bổ sung [8]."),
        ("1.3. Tính khả dụng của các phương pháp trong đề tài",
         "Tính khả dụng được đối chiếu lần lượt cho từng nhóm phương pháp với đặc thù dữ liệu tuyển dụng Việt Nam:\n"
         "• Tiền xử lý: các kỹ thuật regex và từ điển đồng nghĩa khả dụng ngay vì dữ liệu lương/kỹ năng có quy luật lặp lại cao; fuzzy matching bù cho biến thể gõ không dấu/viết tắt.\n"
         "• Hồi quy: khả dụng vì 44 thuộc tính cung cấp đủ đặc trưng phân loại; kết quả RF gần 1.0 R² cho thấy đặc trưng đủ mạnh để giải thích lương, dù cần thận trọng với overfitting (mục 2.1 KẾT LUẬN).\n"
         "• K-Means: khả dụng để khám phá phân khúc thị trường không cần nhãn; Silhouette 0.38 ở mức chấp nhận được cho dữ liệu nhiều chiều.\n"
         "• Content-based: khả dụng nhất khi kỹ năng được chuẩn hóa thành 45 tên gọi — nền tảng để so sánh Cosine; hạn chế là 6.6% tin có kỹ năng chi tiết.\n"
         "Tổng hợp: mỗi kỹ thuật được chọn vì phù hợp với dạng dữ liệu hiện có (phi cấu trúc, thiếu nhãn, độ phủ kỹ năng thấp) và cho kết quả định lượng rõ ràng; "
         "các hạn chế (overfitting, độ phủ kỹ năng) được ghi nhận là hướng cải tiến ở Chương 3 và KẾT LUẬN.")
    ],
}
```

**Quy ước đánh dấu công thức:** tuple có `sub_title` bắt đầu bằng `"__MATH__ "` biểu thị 1 công thức — phần text sau `;` là kind mapping (mặc định `t`). Body tuple `("", body_text)` là đoạn nối (không có tiêu đề). Task 4 sẽ dạy `insert_content_after_paragraph` hiểu 2 form này.

- [ ] **Step 1: Thay `FULL_CONTENT["CHƯƠNG 1 ..."]` bằng nội dung trên (copy nguyên văn)**

  Đảm bảo giữ nguyên các dict key khác (`LỜI MỞ ĐẦU`, `CHƯƠNG 2...`, `CHƯƠNG 3...`, `KẾT LUẬN`).

- [ ] **Step 2: Chạy script — dự kiến các `__MATH__` hiện thành tiêu đề xấu**

Run: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu && python scripts/generate_docx_report.py`
Expected: không crash; các dòng `__MATH__ ...` bị in thành tiêu đề (chấp nhận tạm). Ghi nhận output.

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat: chapter 1 full theoretical content with citations"
```

---

### Task 4: Dạy `insert_content_after_paragraph` xử lý công thức và đoạn nối

**Files:**
- Modify: `scripts/generate_docx_report.py` — `insert_content_after_paragraph` (dòng ~178–203)

**Interfaces:**
- Consumes: `make_math_paragraph()` (Task 1), cấu trúc content với `__MATH__` prefix
- Produces: hành vi mới — tuple `("__MATH__ <expr> ; <kind>", "")` → gọi `make_math_paragraph`; tuple `("", body)` → chỉ chèn body không tiêu đề.

- [ ] **Step 1: Cập nhật vòng lặp trong `insert_content_after_paragraph`**

```python
def insert_content_after_paragraph(doc, target_paragraph, content_list):
    current_p = target_paragraph
    for sub_title, sub_body in content_list:
        # Dạng công thức: sub_title bắt đầu "__MATH__"
        if sub_title.startswith('__MATH__'):
            expr = sub_title[len('__MATH__ '):]
            # expr dạng "<công thức> ; <kind>", kind mặc định 't'
            parts = expr.split(' ; ')
            math_expr = parts[0]
            kinds = parts[1].split(',') if len(parts) > 1 else ['t']
            print(f"  - Inserting math: {math_expr}")
            # kind hiện chỉ dùng 't' (text) — phân số được xử lý trong make_math_paragraph bằng cú pháp "num/den"
            math_p = make_math_paragraph(doc, current_p, [(math_expr, kinds[0])])
            current_p = math_p
            continue

        print(f"  - Inserting new sub-section: {sub_title}")
        if sub_title:
            new_p_sub = insert_paragraph_after(current_p, text=sub_title, style='Normal')
            new_p_sub.paragraph_format.space_before = Pt(12)
            new_p_sub.paragraph_format.space_after = Pt(2)
            if not new_p_sub.runs: new_p_sub.add_run(sub_title)
            for run in new_p_sub.runs:
                run.bold = True
                run.font.name = "Times New Roman"
                run.font.size = Pt(13)
            current_p = new_p_sub

        if sub_body:
            new_p_body = insert_paragraph_after(current_p, text=sub_body, style='Normal')
            new_p_body.paragraph_format.space_after = Pt(6)
            new_p_body.paragraph_format.line_spacing = 1.15
            if not new_p_body.runs: new_p_body.add_run(sub_body)
            for run in new_p_body.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
            current_p = new_p_body

        if "3.2. Kết quả Đánh giá Mô hình Dự báo Lương" in sub_title:
            print("    [Table] Inserting ML results table...")
            insert_table_after_paragraph(new_p_body, ML_RESULTS_TABLE)
```

**Lưu ý:** `make_math_paragraph` trả về Paragraph mới — gán trực tiếp `current_p = math_p` (không dùng trick `getnext() and ...`).

- [ ] **Step 2: Chạy script**

Run: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu && python scripts/generate_docx_report.py`
Expected: không crash; log có dòng `- Inserting math: ...`; `VERIFICATION PASSED` có thể chưa vì verify chưa cập nhật — chấp nhận.

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat: handle math paragraphs and continuation bodies in inserter"
```

---

### Task 5: Mở rộng `verify_report()`

**Files:**
- Modify: `scripts/generate_docx_report.py` — `verify_report()` (dòng ~206–257)

**Interfaces:**
- Consumes: `normalize_text()`, các key phrases mới
- Produces: verify đầy đủ — thêm phrases, count tài liệu tham khảo.

- [ ] **Step 1: Thêm key phrases + count references vào `verify_report`**

Trong `doc_full_text` block, mở rộng `key_phrases`:

```python
    key_phrases = [
        "1.193 bản ghi việc làm",
        "44 thuộc tính chi tiết",
        "tỷ lệ ẩn lương ghi nhận thực tế là 56%",
        "188 quy tắc ánh xạ",
        "Content-based Recommendation",
        "tính khả dụng",
        "1.2.3",
        "R² = 1 −",
        "cos(A,B)",
        "Géron",
        "Rousseeuw",
        "[1]",
    ]
```

Sau block check old_phrases, thêm:

```python
    # Verify mục TÀI LIỆU THAM KHẢO: đếm số dòng "[n] ..."
    ref_count = 0
    for p in doc.paragraphs:
        if p.style.name.startswith('toc') or p.style.name.startswith('TOC'):
            continue
        if re.match(r'^\[\d+\] ', normalize_text(p.text)):
            ref_count += 1
    if ref_count < 10:
        found_issues.append(f"Thiếu mục tài liệu tham khảo: chỉ có {ref_count}/10 mục")
```

- [ ] **Step 2: Chạy script — verify đầy đủ**

Run: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu && python scripts/generate_docx_report.py`
Expected: `VERIFICATION PASSED`.

- [ ] **Step 3: Test tay — mở docx kiểm tra công thức hiển thị**

Run:
```
cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu
python -c "
import docx
d = docx.Document('reports/BaoCao_MonHoc_NguyenMinhTan_Complete.docx')
maths = [p.text for p in d.paragraphs if 'oMath' in p._p.xml or 'β' in p.text or '∑' in p.text]
print('Math-ish paragraphs:', len(maths))
for m in maths[:10]: print(repr(m))
"
```
Expected: ≥ 6 mục có dấu β/∑/√/‖; không có text `__MATH__` còn sót trong file.

- [ ] **Step 4: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat: extend verification with chapter-1 phrases and reference count"
```

---

### Task 6: Chạy script hoàn chỉnh + ghi nhận kết quả

**Files:**
- (không đổi file)

- [ ] **Step 1: Chạy toàn bộ từ đầu**

Run: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu && python scripts/generate_docx_report.py`
Expected: log đầy đủ — `Loading template`, 6 section xử lý, `-> Cleared ...`, các `- Inserting new sub-section`, `- Inserting math`, cuối cùng `VERIFICATION PASSED: Báo cáo đã được làm sạch và cập nhật hoàn hảo!`

- [ ] **Step 2: Ghi nhận số liệu đầu ra**

Run:
```
python -c "
import docx, re
d = docx.Document('reports/BaoCao_MonHoc_NguyenMinhTan_Complete.docx')
ps = [p for p in d.paragraphs if not p.style.name.startswith('toc')]
tnr = sum(1 for p in ps if 'Times New Roman' in p._p.xml)
print('paragraphs:', len(ps), '| TNR runs:', tnr)
print('math elems:', d._element.body.xml.count('<m:oMath>'))
"
```
Expected: TNR chiếm đa số, `math elems >= 7`.

- [ ] **Step 3: Commit (nếu có thay đổi dư từ debug)**

```bash
git add scripts/generate_docx_report.py
git commit -m "chore: final verification run"
```
(chỉ commit nếu Task 5-6 sửa gì đó; nếu không, bỏ qua)

---

## Self-Review

**1. Spec coverage:**
- Cấu trúc Chương 1 (1.1/1.2/1.3, 4 nhóm 1.2.1–1.2.4) → Task 3 ✓
- Công thức OMML (7 cái, `make_math_paragraph`) → Task 1 + Task 4 ✓
- Trích dẫn [1]–[10] + REFERENCES + section TÀI LIỆU THAM KHẢO → Task 2 + Task 3 ✓
- Verify mở rộng (phrases mới, count refs) → Task 5 ✓
- Fallback an toàn, không crash → Task 1 (fallback `'t'` khi không có `;`) ✓
- Non-goals (không đụng chương khác, không thêm lib) → giữ qua các task ✓

**2. Placeholder scan:** không có TBD/TODO; mọi step có code/command cụ thể.

**3. Type consistency:** `make_math_paragraph(doc, anchor_p, segments)` — định nghĩa Task 1, dùng Task 4 với `[(math_expr, 't')]` ✓. `REFERENCE_ITEMS` dùng ở Task 2 Step 2 và Task 2 Step 3/4 ✓. `sections` thêm phần tử cuối — `insert_content_after_paragraph` với các tuple `(sub_title, body)` chuẩn (REFERENCE_ITEMS là list str — **LƯU Ý**: `REFERENCE_ITEMS` là list `str`, nhưng `insert_content_after_paragraph` duyệt `for sub_title, sub_body in content_list` — str không unpack được 2 phần tử → lỗi runtime!** Cần sửa: chuyển `REFERENCE_ITEMS` thành list tuple `(item, "")` hoặc wrap trong `sections`:

```python
("TÀI LIỆU THAM KHẢO", [(item, "") for item in REFERENCE_ITEMS]),
```

→ đã ghi chú ở Task 2 Step 2 — ép kiểu tuple. Kiểm tra lại: Task 2 Step 2 viết `("TÀI LIỆU THAM KHẢO", REFERENCE_ITEMS)` — **SỬA** thành:

```python
("TÀI LIỆU THAM KHẢO", [(item, "") for item in REFERENCE_ITEMS]),
```

✓ type-safe.

**Lưu ý thêm:** `insert_content_after_paragraph` ở Task 4 xử lý tuple rỗng `("", "")` → `if sub_title:` (bỏ trống) và `if sub_body:` (bỏ trống) → không crash.