# Bảng Phân Công Đóng Góp (Yêu cầu B12, J4, M1-M5)

## Phân công theo buổi

| Buổi | Nội dung | Member 1 | Member 2 |
|------|----------|----------|----------|
| 1 | Thiết lập repo & Problem Definition | Tạo structure, requirements, README, .gitignore | Viết 01_problem_and_data.ipynb |
| 2 | OOP Classes | `src/domain/job_posting.py`, `company.py` | `src/domain/skill.py`, `data/data_manager.py` (skeleton) |
| 3 | Data Collection | `collector.py` (itviec + vietnamworks), `salary_parser.py` | `collector.py` (topdev fallback), verify quality |
| 4 | Cleaning Pipeline | `data_manager.py` merge/save, cleanup review | `skill_normalizer.py`, `experience_normalizer.py`, `deduplicator.py` |
| 5 | Merge + Pivot | Run merge → combined.parquet, 5 pivot tables | `chart_utils.py` |
| 6 | EDA | Commentary cho charts, cross-check data | `03_eda.ipynb` (8+ charts) |
| 7 | Machine Learning | Baseline + cross-check | `feature_pipeline.py`, `supervised.py`, error analysis |
| 8 | Clustering + Reco | `clustering.py`, K-Means | `recommendation.py`, Reco engine |

## Yêu cầu cá nhân (M1-M5)

| # | Yêu cầu | Member 1 | Member 2 |
|---|---------|----------|----------|
| M1 | ≥1 class Python chính | ✅ JobPosting + Company | ✅ Skill + RecommendationEngine |
| M2 | ≥1 phần làm sạch | ✅ SalaryParser + ExperienceNormalizer | ✅ SkillNormalizer + Deduplicator |
| M3 | ≥2 biểu đồ | ✅ Salary charts (boxplot, heatmap) | ✅ Skill charts (bar, pie) |
| M4 | ≥1 mô hình | ✅ Baseline + cross-check | ✅ Supervised + Clustering + Reco |
| M5 | Trình bày ≥7 phút | ⬜ Phần của mình | ⬜ Phần của mình |

## Thống kê đóng góp (số file)

| Hạng mục | Member 1 | Member 2 |
|----------|----------|----------|
| Số file Python trong `src/` | job_posting.py, company.py, data_manager.py, collector.py, salary_parser.py, chart_utils.py, feature_pipeline.py, baseline.py, clustering.py | skill.py, skill_normalizer.py, experience_normalizer.py, deduplicator.py, supervised.py, recommendation.py |
| Số notebook viết chính | 01_problem_and_data (đồng tác giả) | 02_collection_and_cleaning, 03_eda, 04_machine_learning |
| Số test file | test_salary_parser.py, test_deduplicator.py | test_skill_normalizer.py, test_recommendation.py |
| Số biểu đồ EDA | 4 | 4+ |

*Ghi chú: Cập nhật sau khi hoàn thành thực tế.*