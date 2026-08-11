# Thiết kế: Mở rộng Chương 1 — Cơ sở lý thuyết & Tính khả dụng

**Ngày:** 2026-08-11
**Phạm vi:** `scripts/generate_docx_report.py` — cập nhật nội dung Chương 1 của báo cáo Word, thêm công thức OMML, hệ trích dẫn, và làm sạch mục TÀI LIỆU THAM KHẢO.

## 1. Vấn đề

Chương 1 ("TỔNG QUAN VỀ BÀI TOÁN VÀ CƠ SỞ LÝ THUYẾT") hiện chỉ có 2 mục sơ sài:

- `1.1. Bối cảnh, Đặt vấn đề và Tính cấp thiết của đề tài` — 1 đoạn ngắn
- `1.2. Cơ sở Lý thuyết về Phân tích Dữ liệu và Học máy` — 1 đoạn liệt kê chung chung

Yêu cầu: viết đầy đủ hơn, chi tiết phần **cơ sở lý thuyết** gắn với **tính khả dụng trong dự án này** (cấu trúc lại, công thức toán học, trích dẫn học thuật, làm sạch tài liệu tham khảo cũ).

## 2. Phương án

**Phương án A — mở rộng script hiện tại `generate_docx_report.py`** (đã được duyệt):
giữ nguyên kiến trúc 1-file, không tách module, không thêm thư viện mới. Chỉ sửa nội dung + thêm helper + mở rộng verify.

## 3. Cấu trúc nội dung Chương 1 mới

```
1.1. Bối cảnh, Đặt vấn đề và Tính cấp thiết của đề tài
      • Thị trường IT VN tăng trưởng, thiếu nhân lực chất lượng cao
      • Nghịch lý mất cân đối cung-cầu thông tin giữa nhà tuyển dụng & ứng viên
      • Dữ liệu phân tán đa nguồn (Itviec, Glints, TopCV, Careerviet), phi cấu trúc
      • Câu hỏi nghiên cứu RQ1–RQ5 liên kết với Chương 3 (F1–F4)
      • Giá trị ứng dụng: định giá năng lực, lộ trình học tập, tối ưu tuyển dụng

1.2. Cơ sở Lý thuyết (4 nhóm nhỏ, mỗi nhóm: khái niệm → công thức → tham số trong đề tài → kết quả)
      1.2.1. Tiền xử lý dữ liệu phi cấu trúc
            • Crawler v2: JSON-LD, __NEXT_DATA__, HTML parsing, anti-bot
            • SalaryParser: 6 regex, 8 SalaryType, USD→VND ×25000, lương năm→tháng ÷12,
              UP_TO→mid=70% max, FROM→mid=130% min, HIDDEN (56% thực tế)
            • SkillNormalizer: 188 quy tắc đồng nghĩa → 45 kỹ năng chuẩn, fuzzy match ngưỡng 0.8
            • ExperienceNormalizer: regex TV/EN, 5 bậc (entry..lead)
            • Deduplicator: 4 pha (exact job_id, exact title+company, fuzzy title 0.8, fuzzy desc 0.7), loại 70 bản ghi
      1.2.2. Hồi quy học có giám sát
            • Linear Regression, Decision Tree (max_depth=10, min_samples_leaf=5),
              Random Forest (n_estimators=100, max_depth=15, min_samples_leaf=4, random_state=42)
            • Công thức OMML: y = β₀ + β₁x₁ + … + βₙxₙ; MSE; RMSE; R²
            • Đặc trưng: ColumnTransformer (median imputer + StandardScaler, OneHot,
              OrdinalEncoder), 7 nhóm đặc trưng; chia 80/20; 5-fold CV
            • Kết quả: bảng 3 model (RMSE/MAE/R²), Baseline 8.97/-0.010 → RF ~0/1.0
      1.2.3. Phân cụm không giám sát (K-Means)
            • Công thức OMML: J = Σₖ Σₓ ‖x − μₖ‖²; Silhouette s(i) = (b(i) − a(i))/max(a(i), b(i))
            • Tham số: k=5 (khảo sát k=2..10), n_init=10, random_state=42, StandardScaler, PCA(2)
            • Kết quả: silhouette 0.38; 5 phân khúc (15.1M, 27.1M, 41.9M, 20.8M, 31.6M)
      1.2.4. Hệ gợi ý dựa trên nội dung (Content-based)
            • Công thức OMML: cos(A,B) = (A·B)/(|A||B|)
            • MultiLabelBinarizer → ma trận job×skill, cosine_similarity
            • Bộ lọc: thành phố (case-insensitive), kinh nghiệm ±0.5 năm / experience_bin fallback
            • Kết quả: Top-N + matched/missing skills

1.3. Tính khả dụng của các phương pháp trong đề tài
      • Đối chiếu từng kỹ thuật với đặc thù dữ liệu tuyển dụng VN
      • Lý do chọn 3 nhóm phương pháp (supervised / unsupervised / content-based)
      • Độ phù hợp & hạn chế đã biết (6.6% kỹ năng, overfitting cây)
      • Bảng/bullet tổng hợp: kỹ thuật → dữ liệu → kết quả
```

**Mẫu trích dẫn:** `[1]`, `[2]`, ... đánh dấu cuối mỗi đoạn khái niệm/công thức trong 1.2 & 1.3.

## 4. Builder công thức OMML

Hàm mới `make_math_paragraph(doc, anchor_p, segments)` (không thư viện mới, dùng `docx.oxml.OxmlElement`):

- Sinh `w:p` chứa `<m:oMathPara>` + `<m:oMath>` với các `<m:r>` (text) và `<m:f>` (frac: `m:num`/`m:den`).
- Segment là tuple `(text, type)`; type ∈ `normal | italic | frac | sup/sub (chỉ số Unicode) | unicode`.
- Hỗ trợ: phân số `frac{tử}{mẫu}`, chỉ số Unicode `₀₁ᵢ`, ký tự `∑ ∈ − × ‖ ‖ √`.
- Công thức chèn (5 cái):
  1. `y = β₀ + β₁x₁ + … + βₙxₙ` — hồi quy tuyến tính
  2. `MSE = (1/n)∑(yᵢ − ŷᵢ)²`
  3. `RMSE = √MSE`
  4. `R² = 1 − (∑(yᵢ − ŷᵢ)²)/(∑(yᵢ − ȳ)²)`
  5. `J = Σₖ Σₓ ‖x − μₖ‖²` — K-Means objective
  6. `s(i) = (b(i) − a(i))/max(a(i), b(i))` — silhouette
  7. `cos(A,B) = (A·B)/(|A||B|)` — cosine
- **Fallback:** nếu segment không biểu diễn được bằng OMML → chèn run text thuần (in nghiêng). Không crash script.
- Mỗi công thức là 1 paragraph riêng, style "Normal", font Times New Roman 12pt, thụt lề trái.

## 5. Hệ trích dẫn & Mục TÀI LIỆU THAM KHẢO

- `REFERENCES` list mới (~10 mục, xem Phần 6 của design đã duyệt — Géron, ISLR, JMLR/scikit-learn, Breiman, Quinlan, MacQueen, Rousseeuw, Ricci/Rokach/Shapira, McKinney, BeautifulSoup).
- `REFERENCE_ITEMS` = `[f"[{i}] {ref}" for i, ref in enumerate(REFERENCES, 1)]`.
- `sections` list thêm `("TÀI LIỆU THAM KHẢO", REFERENCE_ITEMS)` — `clear_existing_subsections_after` xóa toàn bộ nội dung ResNet50 cũ dưới heading này trước khi chèn mới.
- Trích dẫn trong thân bài đánh số thủ công cố định (không logic tự động).

## 6. Verify mở rộng (`verify_report()`)

- Thêm key_phrases: `"tính khả dụng"`, `"1.2.3"`, `"R² = 1 −"`, `"cos(A,B)"`, `"Géron"`, `"Rousseeuw"`, `"[1]"`.
- Count mục tài liệu tham khảo ≥ 10.
- Giữ nguyên checks cũ (5 headings, "1.193 bản ghi việc làm", "44 thuộc tính chi tiết", "tỷ lệ ẩn lương ghi nhận thực tế là 56%", "188 quy tắc ánh xạ", "Content-based Recommendation", ML table, không còn resnet50/rác thải).

## 7. Không thay đổi (non-goals)

- Chương 2, Chương 3, LỜI MỞ ĐẦU, KẾT LUẬN: giữ nguyên nội dung hiện có.
- Không thêm thư viện mới (`requirements.txt` không đổi).
- Không tách module, không đổi cơ chế chèn/verify hiện tại.