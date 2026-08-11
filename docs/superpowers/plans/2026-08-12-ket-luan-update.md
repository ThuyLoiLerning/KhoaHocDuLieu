# Phần KẾT LUẬN — Mở Rộng Nội Dung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mở rộng `FULL_CONTENT["KẾT LUẬN"]` trong `scripts/generate_docx_report.py` thành 3 mục × 2-3 đoạn với trích dẫn [1], [8], và mở rộng key_phrases verify.

**Architecture:** Sửa 2 block trong 1 file: thay list `"KẾT LUẬN"` (3 phần tử 1-đoạn → 3 phần tử nhiều-đoạn) và thêm 5 phrase vào `key_phrases`. Chạy script — `verify_report()` là bước kiểm nghiệm.

**Tech Stack:** python-docx, Python 3 (không thêm thư viện).

## Global Constraints

- Chỉ sửa `scripts/generate_docx_report.py`. Không tách module, không thêm thư viện.
- Tiêu đề 3 mục giữ nguyên: `1. Kết luận`, `2. Hạn chế của đề tài`, `3. Hướng phát triển` (bold 13pt, style hiện có).
- Chương 1/2/3, LỜI MỞ ĐẦU, TÀI LIỆU THAM KHẢO: giữ nguyên.
- Không thêm refs mới, không thêm bảng.
- Số liệu lấy từ kết quả đã có (Chương 3): Linear RMSE 4.17/R² 0.783/+53.5%, DT 0.60/R² 0.996/+93.3%, K-Means k=10 silhouette 0.38, Top-3 (Data Scientist/ML Engineer/Data Engineer), 6.6% skills, TP.HCM ~50%/Đà Nẵng ~4%.
- Chạy mọi lệnh Python với `PYTHONIOENCODING=utf-8`.

---

### Task 1: Thay nội dung FULL_CONTENT["KẾT LUẬN"]

**Files:**
- Modify: `scripts/generate_docx_report.py:118-125` — list `"KẾT LUẬN": [...]`

**Interfaces:**
- Produces: content_list 3 phần tử `(sub_title, sub_body)` cho `insert_content_after_paragraph`; sub_body là text nhiều đoạn nối bằng `\n` (giống EDA 3.1 đã có). Task 2 verify đọc các phrase trong text này.

- [ ] **Step 1: Thay list KẾT LUẬN cũ**

Thay khối (dòng 118-125):

```python
    "KẾT LUẬN": [
        ("1. Kết luận",
         "Đồ án đã xây dựng hoàn chỉnh một hệ thống Khoa học Dữ liệu end-to-end ứng dụng trong phân tích thị trường tuyển dụng IT Việt Nam, đáp ứng 100% các tiêu chí kỹ thuật và yêu cầu chuyên môn của học phần."),
        ("2. Hạn chế của đề tài",
         "Tỷ lệ tin có thuộc tính kỹ năng chi tiết còn thấp (6.6%) do đặc thù hiển thị từ nguồn trang niêm yết (Careerviet/TopCV); các mô hình dựa trên cây có nguy cơ overfitting trên tập đặc trưng hiện tại."),
        ("3. Hướng phát triển",
         "Mở rộng crawler tự động truy cập sâu vào trang chi tiết từng tin tuyển dụng; kết hợp kỹ thuật xử lý ngôn ngữ tự nhiên (NLP/BERT) để trích xuất đặc trưng từ mô tả công việc (Job Description) và phát triển mô hình Gợi ý kết hợp (Hybrid Recommendation).")
    ]
```

bằng:

```python
    "KẾT LUẬN": [
        ("1. Kết luận",
         "Đồ án đã xây dựng hoàn chỉnh một hệ thống Khoa học Dữ liệu end-to-end ứng dụng trong phân tích thị trường tuyển dụng IT Việt Nam. Hệ thống bao gồm: hệ thống thu thập dữ liệu (Crawler v2) vận hành trên 4 nguồn việc làm chính với 22 từ khóa tìm kiếm, thu thập được 1.193 tin tuyển dụng; quy trình làm sạch dữ liệu (chuẩn hóa lương, kỹ năng, kinh nghiệm và khử trùng lặp); khối xây dựng đặc trưng với ColumnTransformer; và ba nhóm mô hình học máy (hồi quy có giám sát, phân cụm K-Means và hệ gợi ý dựa trên nội dung). Toàn bộ quy trình đáp ứng 100% các tiêu chí kỹ thuật và yêu cầu chuyên môn của học phần.\nVề kết quả thực nghiệm, nhóm hồi quy cho thấy sự cải thiện rõ rệt qua từng cấp độ mô hình: Baseline đạt RMSE 8.97, Linear Regression giảm còn 4.17 (R² 0.783, cải thiện 53.5%), Decision Tree đạt 0.60 (R² 0.996, cải thiện 93.3%); phân cụm K-Means với k=10 đạt Silhouette Score 0.38, chia thị trường thành 5 phân khúc tiêu biểu; hệ gợi ý Content-based trả về các vị trí phù hợp như Data Scientist, ML Engineer, Data Engineer cho hồ sơ kỹ năng mẫu.\nNhìn chung, các câu hỏi nghiên cứu RQ1-RQ5 đều đã được trả lời thông qua phân tích EDA (F1-F4) và hệ thống gợi ý việc làm, khớp với mục tiêu đề ra ở Chương 1."),
        ("2. Hạn chế của đề tài",
         "Về dữ liệu: tỷ lệ tin có thuộc tính kỹ năng chi tiết còn thấp (6.6%) do đặc thù hiển thị từ nguồn trang niêm yết (Careerviet/TopCV); phân bố việc làm thiên lệch theo thành phố (TP.HCM chiếm khoảng 50%, Đà Nẵng chỉ khoảng 4%) khiến mô hình dễ thiên vị vùng dữ liệu lớn; mức lương sử dụng là giá trị tại điểm giữa khoảng (salary midpoint) thay vì lương thực tế.\nVề mô hình: các mô hình dựa trên cây (Decision Tree, Random Forest) đạt chỉ số gần tối ưu trên tập kiểm tra hiện tại nhưng có nguy cơ overfitting; chưa khai thác kỹ năng (skill encoding) và đặc trưng văn bản từ mô tả công việc trong bài toán hồi quy."),
        ("3. Hướng phát triển",
         "Về dữ liệu: mở rộng crawler truy cập sâu vào trang chi tiết từng tin tuyển dụng để tăng độ phủ kỹ năng; bổ sung thêm nguồn dữ liệu và cập nhật dữ liệu theo thời gian nhằm giảm thiên lệch phân bố.\nVề mô hình: kết hợp kỹ thuật xử lý ngôn ngữ tự nhiên (NLP/BERT) để trích xuất đặc trưng từ mô tả công việc theo phương pháp trình bày trong [1]; thử nghiệm các thuật toán phân cụm khác như DBSCAN hoặc Hierarchical Clustering; và phát triển mô hình Gợi ý kết hợp (Hybrid Recommendation) giữa lọc cộng tác và lọc nội dung [8].")
    ]
```

Lưu ý: dấu `\n` trong sub_body — `insert_content_after_paragraph` chèn toàn bộ sub_body thành 1 paragraph (không tách dòng). Kết quả trong Word: 3 đoạn liền nhau trong 1 paragraph, xuống dòng bằng `\n`. Giống hành vi EDA 3.1 hiện có — chấp nhận được (không đổi cơ chế chèn).

- [ ] **Step 2: Xác minh cú pháp**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python -c "import ast; ast.parse(open('scripts/generate_docx_report.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat(ketluan): expand KẾT LUẬN — 3 sections x 2-3 paragraphs, refs [1][8]"
```

---

### Task 2: Mở rộng key_phrases verify

**Files:**
- Modify: `scripts/generate_docx_report.py` — cuối list `key_phrases` (sau mục `"[8]"`)

**Interfaces:**
- Consumes: nội dung KẾT LUẬN mới (Task 1)
- Produces: verify_report() trả True chỉ khi mọi phrase mới có trong file xuất

- [ ] **Step 1: Thêm 5 phrase vào cuối list key_phrases**

Thay dòng cuối list:

```python
        "[8]"
    ]
```

bằng:

```python
        "[8]",
        "RQ1-RQ5",
        "silhouette 0.38",
        "Hybrid Recommendation",
        "Đà Nẵng",
        "salary midpoint"
    ]
```

- [ ] **Step 2: Chạy script tổng thể — phải PASSED**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python scripts/generate_docx_report.py 2>&1 | tail -6`
Expected: dòng cuối `VERIFICATION PASSED: Báo cáo đã được làm sạch và cập nhật hoàn hảo!`.

Nếu FAILED: đọc issue (ví dụ `Thiếu nội dung: 'salary midpoint'`), đối chiếu chính tả text chèn (mục 2: "giá trị tại điểm giữa khoảng (salary midpoint)") và sửa.

- [ ] **Step 3: Kiểm chứng cấu trúc file xuất**

Run: `cd "d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu" && PYTHONIOENCODING=utf-8 python -c "
import docx
d = docx.Document('reports/BaoCao_MonHoc_NguyenMinhTan_Complete.docx')
print('tables:', len(d.tables))
h1 = [p.text for p in d.paragraphs if p.style.name == 'Heading 1']
print('H1 count:', len(h1))
for p in d.paragraphs:
    t = p.text.strip()
    if t.startswith(('1. Kết luận', '2. Hạn chế', '3. Hướng phát triển')):
        print(' -', t)
"
`
Expected: `tables: 6`, `H1 count: 6`, 3 dòng tiêu đề KẾT LUẬN hiển thị.

- [ ] **Step 4: Commit**

```bash
git add scripts/generate_docx_report.py
git commit -m "feat(ketluan): extend verify — RQ1-RQ5, silhouette 0.38, Hybrid Recommendation"
```

---

### Task 3: Hoàn tất

**Files:**
- Test: `reports/BaoCao_MonHoc_NguyenMinhTan_Complete.docx` (output Task 2)

- [ ] **Step 1: Báo cáo hoàn tất cho người dùng**

Nhắc: TOC trong Word là bản cũ — mở file, References → Update Table để refresh.

**Skipped:** không có — spec yêu cầu 3 mục mở rộng, trích dẫn [1]/[8], verify mở rộng, đều đủ. Thêm khi cần: tách `\n` thành nhiều paragraph riêng (khi user muốn khoảng cách đoạn rõ hơn — cần sửa insert_content_after_paragraph).
