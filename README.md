# Phân Tích Thị Trường Việc Làm & Gợi Ý Ứng Viên (Chuyên Đề 4)

Dự án cuối kỳ môn **Lập trình cho Khoa học Dữ liệu** — Nhóm 2 người, 8 buổi.

## Mô tả dự án
- **Đề bài**: Cào dữ liệu thực tế từ các trang tuyển dụng Việt Nam (itviec.com, vietnamworks.com, topdev.vn, careerbuilder.vn)
- **Mục tiêu**: Chuẩn hóa lương/kỹ năng, dự đoán lương, gợi ý tin tuyển dụng theo hồ sơ ứng viên
- **Phạm vi**: Nhóm nghề **Lập trình / Data** (IT jobs)

## Cấu trúc thư mục
```
├── data/
│   ├── raw/              # Dữ liệu gốc (CSV, JSON, HTML)
│   │   └── html/         # HTML raw từ crawl
│   └── processed/        # Dữ liệu đã làm sạch (Parquet)
├── notebooks/
│   ├── 01_problem_and_data.ipynb
│   ├── 02_collection_and_cleaning.ipynb
│   ├── 03_eda.ipynb
│   └── 04_machine_learning.ipynb
├── src/
│   ├── domain/           # JobPosting, Skill, Company dataclasses
│   ├── data/             # collector.py, salary_parser.py, data_manager.py
│   ├── cleaning/         # skill_normalizer.py, experience_normalizer.py, deduplicator.py
│   ├── features/         # feature_pipeline.py
│   ├── ml/               # baseline.py, supervised.py, clustering.py, recommendation.py
│   └── visualization/    # chart_utils.py
├── logs/
│   ├── cleaning_errors.log
│   ├── source_metadata.log
│   └── model_evaluation.log
├── reports/
├── tests/
├── requirements.txt
└── README.md
```

## Thành viên nhóm
| Thành viên | Vai trò chính |
|------------|---------------|
| Member 1   | JobPosting, Company, Lương, Kinh nghiệm, Baseline, Clustering |
| Member 2   | Skill, RecommendationEngine, Kỹ năng, Trùng lặp, Supervised, Reco |

## Cài đặt
```bash
# Tạo virtual environment (khuyến nghị)
python -m venv .venv
.venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt
```

## Chạy lại toàn bộ pipeline
```bash
# Khởi động Jupyter
jupyter notebook

# Chạy lần lượt 4 notebooks:
# 1. 01_problem_and_data.ipynb       — Xác định bài toán, câu hỏi nghiên cứu, OOP classes
# 2. 02_collection_and_cleaning.ipynb — Crawl dữ liệu thật, làm sạch, ghi log
# 3. 03_eda.ipynb                    — EDA, 8+ biểu đồ, trả lời F1-F4
# 4. 04_machine_learning.ipynb       — Baseline, Linear/Tree, Clustering, Recommendation, Error analysis
```

## Kết quả kỳ vọng
- ≥ 1.000 tin tuyển dụng thực tế từ ít nhất 2 nguồn
- ≥ 12 thuộc tính (số, phân loại, thời gian)
- ≥ 20 kỹ năng chuẩn hóa (synonym map 35+ entry)
- 8+ biểu đồ có tiêu đề, nhãn trục, nhận xét
- Baseline + 2 mô hình có giám sát + 1 clustering + 1 recommendation
- 10+ trường hợp dự đoán sai phân tích chi tiết
- Báo cáo 20-30 trang + slide thuyết trình

## Lưu ý pháp lý
- Chỉ cào dữ liệu công khai, không vượt CAPTCHA, không đăng nhập
- Tôn trọng robots.txt, delay 1-3s giữa các request
- Không thu thập dữ liệu nhạy cảm (SĐT, email, CMND)
- Ghi nguồn rõ ràng trong `logs/source_metadata.log`

## AI Usage Log
Xem `reports/ai_usage_log.md` — ghi lại prompt, đầu ra AI, cách kiểm chứng, chỉnh sửa của nhóm.

## Contribution Table
Xem `contribution_table.md` — phân công chi tiết từng buổi, minh chứng đóng góp cá nhân.