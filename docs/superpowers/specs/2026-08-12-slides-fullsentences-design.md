# Thiết kế: Bullet thành câu diễn giải đầy đủ — 22 slide PPTX (Chuyên đề 4)

**Ngày:** 2026-08-12
**Yêu cầu:** "Nội dung đang viết vắn tắt rất khó trình bày, người đọc không hiểu."
**Phạm vi user duyệt:** Bullet thành câu diễn giải (đã duyệt thiết kế + "ok triển khai" ngày 12/08).

## Bối cảnh

- Bộ slide 22 trang hiện tại: `reports/slides/TrinhBay_ChuyenDe4.pptx`, sinh bởi `scripts/generate_pptx_slides.py`.
- Bullet hiện dạng ghi chú ngắn (8-10 từ) — người xem không đủ ngữ cảnh để hiểu.

## Nguyên tắc viết

1. Mỗi bullet = 1 câu hoàn chỉnh (15-30 từ), có chủ ngữ — đứng độc lập vẫn hiểu được.
2. Số liệu giữ nguyên, thêm ngữ cảnh giải thích ý nghĩa.
3. Tối đa ~6-7 bullet level 0/slide (font 17pt) — tránh quá tải; nếu slide nhiều bullet → giảm font level 0 còn 16pt.

## Phạm vi

Chỉ sửa chuỗi bullets (text) trong `build()` của `scripts/generate_pptx_slides.py`. Không đổi ảnh, bảng, bố cục, màu, số slide. Không đụng docx, notebook.

## Nội dung cụ thể (bullet → câu)

### Slide 2 — Giới thiệu bài toán
| Bullet cũ | Bullet mới |
|---|---|
| Nghịch lý mất cân đối cung - cầu thông tin giữa nhà tuyển dụng và ứng viên | Tin tuyển dụng phân tán trên nhiều nền tảng, định dạng tự do — ứng viên khó so sánh lương & kỹ năng giữa các nguồn |
| Dữ liệu tuyển dụng phân tán trên nhiều nền tảng (Itviec, Glints, TopCV, Careerviet) — phi cấu trúc | 4 nền tảng lớn tại Việt Nam (Itviec, Glints, TopCV, Careerviet) đăng tin ở các định dạng khác nhau, dữ liệu phi cấu trúc |
| Thu thập tự động dữ liệu tuyển dụng IT (Crawler v2) | Thu thập tự động tin tuyển dụng IT từ 4 nguồn bằng Crawler v2 |
| Dự báo mức lương bằng ML (Baseline, Linear, Decision Tree, Random Forest) | Dự báo khoảng lương thị trường bằng 4 mô hình ML và đánh giá độ chính xác |

### Slide 5 — Crawler v2
| Bullet cũ | Bullet mới |
|---|---|
| HttpClient: httpx verify=True, follow_redirects, timeout 20s | HttpClient (httpx) bật xác thực SSL, tự theo redirect, timeout 20s — hạn chế lỗi kết nối bị chặn |
| Chống chặn: xoay vòng 3 User-Agent, rate-limit 1-3s, retry 429, BLOCKED_MARKERS (cf-challenge, captcha) | Chống chặn bằng xoay vòng 3 User-Agent, rate-limit 1-3s, retry khi trả HTTP 429, nhận diện trang chặn qua BLOCKED_MARKERS (captcha, cf-challenge) |

### Slide 6 — Cleaning
| Bullet cũ | Bullet mới |
|---|---|
| SalaryParser: 8 loại cấu trúc lương, 6 regex, USD→VND ×25.000, lương năm÷12 | SalaryParser nhận diện 8 cấu trúc lương bằng 6 regex, đổi USD→VND (×25.000), quy lương năm về tháng |
| Khoảng "tới X" → 70% mức tối đa; "từ X" → 130% mức tối thiểu | Lương dạng khoảng chuẩn hóa về điểm giữa: "tới X" ≈ 70%, "từ X" ≈ 130% — phản ánh thực tế thị trường |
| Tỷ lệ ẩn lương thực tế 56% (24+ từ khóa: cạnh tranh, thỏa thuận...) | 56% tin ẩn lương (24+ từ khóa như cạnh tranh, thỏa thuận) → phải xử lý đặc biệt trước khi dùng cho ML |
| Fuzzy matching (SequenceMatcher) ngưỡng > 0.8; độ phủ thực tế 6.6% | Khớp kỹ năng mờ bằng SequenceMatcher (ngưỡng > 0.8) — chỉ 6.6% tin có phần kỹ năng chi tiết |
| ExperienceNormalizer: 6 regex TV/EN → 5 bậc (entry → lead), fallback description_raw | ExperienceNormalizer dùng 6 regex TV/EN để gán 5 bậc kinh nghiệm (entry → lead), hoặc lấy giá trị thô khi không khớp |

### Slide 8 — Feature Engineering
| Bullet cũ | Bullet mới |
|---|---|
| Numeric: experience_years → SimpleImputer(median) + StandardScaler | Đặc trưng số (experience_years): điền thiếu bằng trung vị, chuẩn hóa về phân phối chuẩn |
| Categorical: city, job_type, remote_option, education_level, industry, company_size → SimpleImputer("Unknown") + OneHotEncoder(handle_unknown="ignore") | Đặc trưng phân loại (city, job_type, remote_option, education_level, industry, company_size): điền "Unknown" khi thiếu, OneHotEncoder bỏ qua giá trị mới lạ |
| Ordinal: experience_bin (entry→lead) → SimpleImputer("unknown") + OrdinalEncoder(unknown_value=-1) | Đặc trưng thứ bậc (experience_bin entry→lead): giữ thứ tự qua OrdinalEncoder, giá trị thiếu gán -1 |
| Chia dữ liệu 80/20 + đánh giá 5-fold cross-validation | Chia 80/20 và đánh giá 5-fold cross-validation để ước lượng độ ổn định |

### Slide 10 — EDA
| Bullet cũ | Bullet mới |
|---|---|
| F1 — Phân bố kỹ năng trên 1.193 tin: nhóm Data Science & Lập trình dẫn đầu | F1 — Nhóm kỹ năng Data Science & Lập trình xuất hiện nhiều nhất trong 1.193 tin — phần lớn vị trí tuyển dụng tập trung vào 2 mảng này |
| F2 — Lương tăng theo bậc kinh nghiệm: Entry ~10M → Mid ~17M → Senior ~28M → Lead ~35M+ | F2 — Lương tăng dần theo bậc: Entry ~10M → Mid ~17M → Senior ~28M → Lead ~35M+, xác nhận kinh nghiệm là nhân tố chính |
| F3 — Yêu cầu tiếng Anh: lương trung bình cao hơn 30% | F3 — Tin yêu cầu tiếng Anh trả lương trung bình cao hơn ~30% — kỹ năng ngoại ngữ tăng giá trị vị trí |
| F4 — Vị trí cấp cao (Senior, Manager, Lead): tỷ lệ ẩn lương >50% | F4 — Vị trí cấp cao (Senior, Manager, Lead) thường ẩn lương (>50%) — thị trường có xu hướng không công khai mức lương cao |

### Slide 12 — note
| Note cũ | Note mới |
|---|---|
| Giảm RMSE 53.5% (Linear) và 93.3% (DT) so Baseline · 12 sai số lớn nhất < 2.1M · residual mean ≈ 0, std ≈ 0.6M · RF overfit trên tập hiện tại | Linear giảm RMSE 53.5%, Decision Tree giảm 93.3% so với Baseline trung bình · 12 sai số lớn nhất đều < 2.1M · Residual phân bố xung quanh 0 (std ≈ 0.6M) · RF học vẹt trên tập hiện tại (overfit) |

### Slide 13/17 — SHAP
| Bullet cũ | Bullet mới |
|---|---|
| (4 bullets hiện tại đã dài) | Giữ nguyên — chỉ tinh chỉnh từ ngữ: thêm ngữ cảnh "Dựa trên 105 tin kiểm thử (test 20%)" |

### Slide 15 — note
| Note cũ | Note mới |
|---|---|
| Khảo sát k = 2..10 · chọn k = 10 với Silhouette Score = 0.38 · 5 phân khúc đặc trưng: Junior-Mid HN 15.1M · Mid-Senior TP.HCM 27.1M · Senior 41.9M · Mid đa dạng 20.8M · Remote 31.6M · StandardScaler + PCA(2D) | Khảo sát k = 2..10, chọn k = 10 với Silhouette Score 0.38 — 5 phân khúc đặc trưng: Junior-Mid HN 15.1M · Mid-Senior TP.HCM 27.1M · Senior 41.9M · Mid đa dạng 20.8M · Remote 31.6M |

### Slide 18 — note
| Note cũ | Note mới |
|---|---|
| MultiLabelBinarizer → ma trận 1500 việc × 45 kỹ năng · lọc thành phố + phân khúc kinh nghiệm ±0.5 năm trước khi tính cosine → giảm nhiễu · demo user_skills = [Python, SQL, Machine Learning] → Top-3: DS 1.0 · ML Eng 0.67 · DE 0.67 | Mã hóa kỹ năng thành ma trận 1500 việc × 45 kỹ năng, lọc thành phố + kinh nghiệm ±0.5 năm trước khi tính cosine để giảm nhiễu · Demo hồ sơ [Python, SQL, Machine Learning] → Top-3: Data Scientist 1.0 · ML Engineer 0.67 · Data Engineer 0.67 |

### Slide 20 — Kết luận
| Bullet cũ | Bullet mới |
|---|---|
| Hồi quy: Baseline RMSE 8.97 → Linear 4.17 (R² 0.783, +53.5%) → Decision Tree 0.60 (R² 0.996, +93.3%) | Hồi quy: RMSE hạ từ 8.97 (Baseline) xuống 4.17 (Linear, R² 0.783) rồi 0.60 (DT, R² 0.996) — mô hình dự báo lương chính xác |
| SHAP xác nhận experience_years & nhóm kỹ năng là nhân tố chính của lương — nhất quán giữa 2 mô hình | SHAP xác nhận kinh nghiệm & nhóm kỹ năng là nhân tố chính quyết định lương — kết quả nhất quán giữa Decision Tree và Linear |
| K-Means k=10, Silhouette 0.38 — 5 phân khúc thị trường rõ rệt | K-Means (k=10, Silhouette 0.38) nhận diện 5 phân khúc thị trường với mức lương & kỹ năng riêng biệt |

### Slide 21 — Hạn chế & Hướng phát triển
| Bullet cũ | Bullet mới |
|---|---|
| Độ phủ kỹ năng chi tiết chỉ 6.6% (giới hạn hiển thị nguồn) | Kỹ năng chi tiết chỉ xuất hiện trong 6.6% tin — hạn chế của dữ liệu nguồn, ảnh hưởng độ chính xác feature kỹ năng |
| Thiên lệch phân bố: TP.HCM ~50%, Đà Nẵng ~4% | Dữ liệu thiên lệch địa lý: TP.HCM ~50% tin, Đà Nẵng chỉ ~4% — chưa đại diện đồng đều thị trường |
| DT/RF overfit trên tập dữ liệu hiện tại; salary midpoint thay lương thực tế | DT/RF overfit trên tập hiện tại; dùng salary midpoint (điểm giữa khoảng) thay vì lương thực tế do 56% tin ẩn lương |
| NL P/BERT trích xuất đặc trưng từ mô tả công việc | Dùng NLP/BERT trích xuất đặc trưng ngữ nghĩa từ mô tả công việc — tận dụng nguồn được ẩn kỹ năng |

## Quyết định kỹ thuật

1. **Chỉ sửa text tuple `(text, level)`** trong các lệnh `add_content_slide` / `add_table_slide` (note) của `build()` — giữ nguyên cấu trúc, level, số bullet.
2. **Không thêm slide, không đổi số, không đổi bố cục, không thêm speaker notes** — verify 22 slide giữ nguyên toàn bộ check hiện tại.
3. Bullets dài hơn → chữ wrap 2 dòng mỗi bullet; slide nhiều bullets (13/17 SHAP, 21 Hạn chế) có thể chật — nếu vượt giới hạn textbox (bottom 6.9in) thì giảm font xuống 15pt cho các slide đó hoặc bỏ bullet phụ. Kiểm tra bằng bounds check của verify.

## Verify

- `python scripts/generate_pptx_slides.py` → VERIFICATION PASSED (22 slides, bảng, pics, số liệu, bounds).
- Manual: mở PPTX kiểm tra từng slide nội dung đủ ý, không tràn chữ dưới cùng.

## Out of scope

- Không sửa ảnh, bảng, bố cục, màu sắc, số slide.
- Không đụng docx, notebook, số liệu.