"""Sinh bộ slide thuyết trình 15 trang (PPTX) — Chuyên đề 4: Phân tích thị trường việc làm IT & Gợi ý ứng viên bằng ML.

Phong cách: nền tối hiện đại (#1E1E2E), chữ trắng, accent cyan (#00BCD4), 16:9, font Calibri.
Dùng python-pptx (>=1.0).
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PPTX = PROJECT_ROOT / "reports" / "slides" / "TrinhBay_ChuyenDe4.pptx"

# --- Màu sắc ---
BG = RGBColor(0x1E, 0x1E, 0x2E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CYAN = RGBColor(0x00, 0xBC, 0xD4)
GRAY = RGBColor(0xB0, 0xB0, 0xC0)
TABLE_ALT = RGBColor(0x2A, 0x2A, 0x3E)

# --- Dữ liệu bảng (đồng bộ generate_docx_report.py) ---
ML_RESULTS_TABLE = [
    ["Mô hình", "RMSE (Triệu VND)", "MAE (Triệu VND)", "R² Score"],
    ["Baseline (Dummy Mean)", "8.97", "7.36", "-0.010"],
    ["Linear Regression", "4.17", "2.94", "0.783"],
    ["Decision Tree", "0.60", "0.18", "0.996"],
    ["Random Forest", "~0.00", "~0.00", "~1.000"],
]

CH2_STATS_TABLE = [
    ["Thuộc tính", "Giá trị"],
    ["Tổng bản ghi việc làm", "1.193"],
    ["Số thuộc tính (cột)", "44"],
    ["Nguồn dữ liệu", "Itviec, Glints, TopCV, Careerviet"],
    ["Tỷ lệ ẩn lương", "56%"],
    ["Độ phủ kỹ năng chi tiết", "6.6%"],
    ["Bản ghi trùng đã loại", "70"],
]

CH3_CLUSTER_TABLE = [
    ["Cluster", "Tỷ lệ", "Lương TB", "Kinh nghiệm TB", "Đặc điểm"],
    ["0", "21%", "15.1M", "2.6y", "Junior-Mid, Hà Nội"],
    ["1", "14%", "27.1M", "2.6y", "Mid-Senior, TP.HCM"],
    ["4", "10%", "41.9M", "4.8y", "Senior, thu nhập cao"],
    ["8", "21%", "20.8M", "2.1y", "Mid, đa dạng"],
    ["9", "4%", "31.6M", "2.7y", "Việc làm Remote"],
]

CH3_REC_TABLE = [
    ["Việc làm", "Similarity", "Kỹ năng khớp", "Kỹ năng thiếu"],
    ["Data Scientist", "1.0", "Python, SQL, Machine Learning", "—"],
    ["ML Engineer", "0.67", "Python, Machine Learning", "Docker, Spark"],
    ["Data Engineer", "0.67", "Python, SQL", "Spark, Airflow"],
]


def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG
    return slide


def _set_text(tf, text, size, color, bold=False, align=PP_ALIGN.LEFT):
    tf.text = text
    for p in tf.paragraphs:
        p.alignment = align
        for run in p.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.bold = bold
    return tf


def add_title_bar(slide, title, num=None):
    # Thanh accent trên cùng
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN
    bar.line.fill.background()
    # Tiêu đề
    label = f"{num}. {title}" if num else title
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.35), Inches(12.3), Inches(0.9))
    _set_text(tb.text_frame, label, 28, CYAN, bold=True)
    return tb


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
        for run in p.runs:  # xóa mặc định
            run.text = ""
        r = p.add_run()
        r.text = ("• " if level == 0 else "– ") + text
        r.font.name = "Calibri"
        r.font.size = Pt(size if level == 0 else size - 2)
        r.font.color.rgb = WHITE if level == 0 else GRAY
        p.space_after = Pt(8 if level == 0 else 4)
    return tb


def add_table_slide(prs, title, data, num=None, col_widths=None, note=None):
    slide = new_slide(prs)
    add_title_bar(slide, title, num)
    rows, cols = len(data), len(data[0])
    tbl_shape = slide.shapes.add_table(
        rows, cols, Inches(0.6), Inches(1.5), Inches(12.1), Inches(0.45 * rows + 0.2))
    tbl = tbl_shape.table
    if col_widths:
        total = sum(col_widths)
        for i, w in enumerate(col_widths):
            tbl.columns[i].width = Inches(12.1 * w / total)
    for r_i, row in enumerate(data):
        for c_i, val in enumerate(row):
            cell = tbl.cell(r_i, c_i)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CYAN if r_i == 0 else (TABLE_ALT if r_i % 2 else BG)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.name = "Calibri"
            r.font.size = Pt(13)
            r.font.color.rgb = WHITE
            r.font.bold = (r_i == 0)
    if note:
        tb = slide.shapes.add_textbox(Inches(0.6), Inches(6.6), Inches(12.1), Inches(0.6))
        _set_text(tb.text_frame, note, 14, GRAY)
    return slide


def add_content_slide(prs, title, bullets, num=None):
    slide = new_slide(prs)
    add_title_bar(slide, title, num)
    add_bullets(slide, bullets)
    return slide


def add_title_slide(prs):
    slide = new_slide(prs)
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(0.12))
    bar.fill.solid(); bar.fill.fore_color.rgb = CYAN; bar.line.fill.background()
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(1.8))
    _set_text(tb.text_frame,
              "PHÂN TÍCH THỊ TRƯỜNG VIỆC LÀM IT &\nGỢI Ý ỨNG VIÊN BẰNG MACHINE LEARNING",
              34, WHITE, bold=True, align=PP_ALIGN.CENTER)
    tb2 = slide.shapes.add_textbox(Inches(1.0), Inches(4.2), Inches(11.3), Inches(1.5))
    _set_text(tb2.text_frame,
              "Chuyên đề 4 — Lập trình cho Khoa học Dữ liệu\n"
              "Học viên: Nguyễn Minh Tan — GVHD: TS. Hoàng Văn Quý\n"
              "Tháng 8 năm 2026",
              18, GRAY, align=PP_ALIGN.CENTER)
    return slide


def add_thanks_slide(prs):
    slide = new_slide(prs)
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.5))
    _set_text(tb.text_frame, "CẢM ƠN THẦY CÔ VÀ CÁC BẠN\nĐÃ LẮNG NGHE!", 40, CYAN, bold=True,
              align=PP_ALIGN.CENTER)
    tb2 = slide.shapes.add_textbox(Inches(1.0), Inches(4.6), Inches(11.3), Inches(0.8))
    _set_text(tb2.text_frame, "Q&A", 20, GRAY, align=PP_ALIGN.CENTER)
    return slide


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    # 1. Bìa
    add_title_slide(prs)

    # 2. Giới thiệu bài toán
    add_content_slide(prs, "Giới thiệu bài toán", [
        ("Thị trường IT Việt Nam tăng trưởng nhanh, nhu cầu nhân lực lớn tại Hà Nội, TP.HCM, Đà Nẵng", 0),
        ("Nghịch lý mất cân đối cung - cầu thông tin giữa nhà tuyển dụng và ứng viên", 0),
        ("Dữ liệu tuyển dụng phân tán trên nhiều nền tảng (Itviec, Glints, TopCV, Careerviet) — phi cấu trúc", 0),
        ("Mục tiêu:", 0),
        ("Thu thập tự động dữ liệu tuyển dụng IT (Crawler v2)", 1),
        ("Làm sạch, chuẩn hóa lương - kỹ năng - kinh nghiệm", 1),
        ("Dự báo mức lương bằng ML (Baseline, Linear, Decision Tree, Random Forest)", 1),
        ("Phân cụm thị trường (K-Means) & Gợi ý việc làm (Content-based)", 1),
    ], num=2)

    # 3. Câu hỏi nghiên cứu
    add_table_slide(prs, "Câu hỏi nghiên cứu RQ1-RQ5", [
        ["Câu hỏi", "Phương pháp"],
        ["RQ1: Kỹ năng nào được yêu cầu nhiều nhất?", "EDA — top skills"],
        ["RQ2: Lương biến động theo kinh nghiệm, thành phố?", "EDA — groupby, boxplot"],
        ["RQ3: Có thể dự báo mức lương không, sai số bao nhiêu?", "ML — RMSE, MAE, R²"],
        ["RQ4: Thị trường phân khúc thành những nhóm nào?", "K-Means — silhouette"],
        ["RQ5: Việc nào phù hợp với hồ sơ kỹ năng?", "Content-based — cosine"],
    ], num=3, col_widths=[8, 4.1])

    # 4. Kiến trúc hệ thống
    add_content_slide(prs, "Kiến trúc hệ thống — Pipeline end-to-end", [
        ("Thu thập dữ liệu (Crawler v2)", 0),
        ("4 nguồn: Itviec, Glints, TopCV, Careerviet — 22 keyword, 1.193 tin", 1),
        ("Làm sạch & Chuẩn hóa", 0),
        ("SalaryParser, SkillNormalizer, ExperienceNormalizer, Deduplicator", 1),
        ("Feature Engineering", 0),
        ("ColumnTransformer: numeric / categorical / ordinal — target salary_mid", 1),
        ("Học máy & Gợi ý", 0),
        ("Hồi quy (Linear, DT, RF) → Phân cụm (K-Means) → Gợi ý (Cosine similarity)", 1),
    ], num=4)

    # 5. Crawler v2
    add_content_slide(prs, "Crawler v2 — Thu thập dữ liệu", [
        ("Vòng lặp site × keyword (22 keyword), ngưỡng min_total_jobs, crawl_history JSON", 0),
        ("HttpClient: httpx verify=True, follow_redirects, timeout 20s", 0),
        ("Chống chặn: xoay vòng 3 User-Agent, rate-limit 1-3s, retry 429, BLOCKED_MARKERS (cf-challenge, captcha)", 0),
        ("4 kỹ thuật trích xuất:", 0),
        ("JSON-LD Parsing — dữ liệu nhúng <script type=\"application/ld+json\">", 1),
        ("__NEXT_DATA__ Extraction — JSON state của trang Next.js", 1),
        ("HTML Parsing (BeautifulSoup) cho trang tĩnh", 1),
        ("API JSON — gọi endpoint trả dữ liệu", 1),
        ("Lưu raw CSV + JSON theo nguồn vào data/raw/, kèm log source_metadata", 0),
    ], num=5)

    # 6. Cleaning
    add_content_slide(prs, "Làm sạch & Chuẩn hóa dữ liệu", [
        ("SalaryParser: 8 loại cấu trúc lương, 6 regex, USD→VND ×25.000, lương năm÷12", 0),
        ("Khoảng \"tới X\" → 70% mức tối đa; \"từ X\" → 130% mức tối thiểu", 1),
        ("Tỷ lệ ẩn lương thực tế 56% (24+ từ khóa: cạnh tranh, thỏa thuận...)", 1),
        ("SkillNormalizer: 188 quy tắc đồng nghĩa → 45 kỹ năng chuẩn, 12 nhóm", 0),
        ("Fuzzy matching (SequenceMatcher) ngưỡng > 0.8; độ phủ thực tế 6.6%", 1),
        ("ExperienceNormalizer: 6 regex TV/EN → 5 bậc (entry → lead), fallback description_raw", 0),
        ("Deduplicator: 4 pha (job_id, title+company, fuzzy title ≥0.8, fuzzy desc ≥0.7)", 0),
        ("Kết quả: loại 70 bản ghi trùng lặp", 1),
    ], num=6)

    # 7. Feature engineering
    add_content_slide(prs, "Feature Engineering", [
        ("3 nhóm đặc trưng trong ColumnTransformer [3]:", 0),
        ("Numeric: experience_years → SimpleImputer(median) + StandardScaler", 1),
        ("Categorical: city, job_type, remote_option, education_level, industry, company_size → SimpleImputer(\"Unknown\") + OneHotEncoder(handle_unknown=\"ignore\")", 1),
        ("Ordinal: experience_bin (entry→lead) → SimpleImputer(\"unknown\") + OrdinalEncoder(unknown_value=-1)", 1),
        ("Biến mục tiêu: salary_mid (triệu VND/tháng)", 0),
        ("Loại cột thô (job_id, description, source_url...); ColumnTransformer(remainder=\"drop\")", 0),
        ("Chia dữ liệu 80/20 + đánh giá 5-fold cross-validation", 0),
    ], num=7)

    # 8. Dữ liệu tổng quan
    add_table_slide(prs, "Dữ liệu sau xử lý", CH2_STATS_TABLE, num=8, col_widths=[7, 5.1],
                    note="1.193 tin tuyển dụng · 44 thuộc tính · 4 nguồn tuyển dụng chính tại Việt Nam")

    # 9. EDA
    add_content_slide(prs, "Phân tích khám phá dữ liệu (EDA)", [
        ("F1 — Phân bố kỹ năng: nhóm Data Science & Lập trình dẫn đầu", 0),
        ("Top kỹ năng: JavaScript, React, Kafka, Python, SQL, Docker, Spring Boot, TensorFlow", 1),
        ("F2 — Lương tăng theo bậc kinh nghiệm: Entry ~10M → Lead ~35M+", 0),
        ("TP.HCM & Hà Nội có lương trung bình cao hơn rõ rệt", 1),
        ("F3 — Yêu cầu tiếng Anh: lương trung bình cao hơn 30%", 0),
        ("F4 — Vị trí cấp cao (Senior, Manager, Lead): tỷ lệ ẩn lương >50%", 0),
    ], num=9)

    # 10. Kết quả Supervised
    add_table_slide(prs, "Kết quả mô hình dự báo lương", ML_RESULTS_TABLE, num=10,
                    col_widths=[4.5, 2.5, 2.5, 2.6],
                    note="Error Analysis: 12 trường hợp sai lớn nhất < 2.1M · residual mean ≈ 0, std ≈ 0.6M · DT/RF có dấu hiệu overfit")

    # 11. K-Means
    add_table_slide(prs, "Phân cụm thị trường (K-Means)", CH3_CLUSTER_TABLE, num=11,
                    col_widths=[1.5, 1.5, 1.8, 2.2, 5.1],
                    note="Khảo sát k = 2..10 · chọn k = 10 với Silhouette Score = 0.38 · StandardScaler + PCA(2D)")

    # 12. Recommendation
    add_table_slide(prs, "Hệ thống gợi ý việc làm (Content-based)", CH3_REC_TABLE, num=12,
                    col_widths=[3.2, 1.8, 4.1, 3.0],
                    note="MultiLabelBinarizer → ma trận 1500 việc × 45 kỹ năng · Cosine similarity · lọc thành phố + kinh nghiệm ±0.5 năm · demo user_skills = [Python, SQL, Machine Learning]")

    # 13. Kết luận
    add_content_slide(prs, "Kết luận", [
        ("Xây dựng hoàn chỉnh pipeline Khoa học Dữ liệu end-to-end, đáp ứng 100% tiêu chí học phần", 0),
        ("Hồi quy: Baseline RMSE 8.97 → Linear 4.17 (R² 0.783, +53.5%) → Decision Tree 0.60 (R² 0.996, +93.3%)", 0),
        ("K-Means k=10, Silhouette 0.38 — 5 phân khúc thị trường rõ rệt", 0),
        ("Content-based: Top-3 phù hợp (Data Scientist, ML Engineer, Data Engineer) kèm kỹ năng còn thiếu", 0),
        ("RQ1-RQ5 đều được trả lời qua EDA (F1-F4) và hệ gợi ý", 0),
    ], num=13)

    # 14. Hạn chế & Hướng phát triển
    add_content_slide(prs, "Hạn chế & Hướng phát triển", [
        ("Hạn chế:", 0),
        ("Độ phủ kỹ năng chi tiết chỉ 6.6% (giới hạn hiển thị nguồn)", 1),
        ("Thiên lệch phân bố: TP.HCM ~50%, Đà Nẵng ~4%", 1),
        ("DT/RF overfit trên tập dữ liệu hiện tại; salary midpoint thay lương thực tế", 1),
        ("Hướng phát triển:", 0),
        ("Crawler truy cập sâu trang chi tiết, đa nguồn, cập nhật theo thời gian", 1),
        ("NLP/BERT trích xuất đặc trưng từ mô tả công việc", 1),
        ("DBSCAN / Hierarchical Clustering; Hybrid Recommendation (collaborative + content-based)", 1),
    ], num=14)

    # 15. Cảm ơn
    add_thanks_slide(prs)

    prs.save(OUTPUT_PPTX)
    print(f"Saved: {OUTPUT_PPTX} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


def verify():
    from pptx import Presentation
    prs = Presentation(OUTPUT_PPTX)
    slides = list(prs.slides)
    n = len(slides)
    issues = []
    if n != 15:
        issues.append(f"Số slide = {n}, mong đợi 15")
    # Mỗi slide có text
    for i, s in enumerate(slides, 1):
        texts = []
        for shape in s.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                texts.append(shape.text_frame.text.strip())
        if not texts:
            issues.append(f"Slide {i} không có nội dung")
    # Bảng ML 5×4 ở slide 10
    slide10 = slides[9]
    tbls = [sh.table for sh in slide10.shapes if sh.has_table]
    if not tbls or len(tbls[0].rows) != 5 or len(tbls[0].columns) != 4:
        issues.append("Slide 10 thiếu bảng ML 5×4")
    # Bảng thống kê 7×2 ở slide 8
    slide8 = slides[7]
    tbls8 = [sh.table for sh in slide8.shapes if sh.has_table]
    if not tbls8 or len(tbls8[0].rows) != 7 or len(tbls8[0].columns) != 2:
        issues.append("Slide 8 thiếu bảng thống kê 7×2")
    # Bảng cluster 6×5 ở slide 11
    slide11 = slides[10]
    tbls11 = [sh.table for sh in slide11.shapes if sh.has_table]
    if not tbls11 or len(tbls11[0].rows) != 6 or len(tbls11[0].columns) != 5:
        issues.append("Slide 11 thiếu bảng cluster 6×5")
    # Số liệu chính
    all_text = " ".join(
        sh.text_frame.text for s in slides for sh in s.shapes if sh.has_text_frame).lower()
    for phrase in ["1.193", "4.17", "0.38", "1500", "56%", "6.6%"]:
        if phrase not in all_text:
            issues.append(f"Thiếu số liệu: '{phrase}'")
    if issues:
        print("VERIFICATION FAILED:")
        for i in issues:
            print(f"  - {i}")
        return False
    print(f"VERIFICATION PASSED: {n} slides, bảng đúng kích thước, số liệu đầy đủ!")
    return True


if __name__ == "__main__":
    build()
    verify()
