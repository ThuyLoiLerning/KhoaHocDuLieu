# Review Kết Quả Notebooks trên Data Thật

**Ngày:** 2026-08-03
**Data:** `combined_20260803_144312.parquet` (1050 rows, 43 cols)

## Tổng quan Data

| Chỉ tiêu | Giá trị | Yêu cầu | Đạt |
|----------|---------|---------|-----|
| Tổng jobs | 1050 | ≥1000 (A6, C5) | ✅ |
| Thuộc tính | 43 | ≥12 (C7) | ✅ |
| Nguồn | careerviet 970, itviec 37, topcv 29, glints 14 | ≥2 nguồn (A5) | ✅ |
| Salary | 494/1050 (47%) | — | ⚠️ |
| Skills | 79 jobs (itviec/topcv/glints) | F1 | ⚠️ |
| Experience | 83 (8%) | — | ⚠️ |
| Education | 1019 (97%) | — | ✅ |
| Thành phố | HCMC, Hanoi, Da Nang, Can Tho + tỉnh khác | ≥3 TP (C8) | ⚠️ |

## Notebook 1 — Problem & Data (✅)
- Problem definition, data dictionary, ER diagram, OOP classes — đầy đủ
- Chạy OK trên data thật

## Notebook 2 — Collection & Cleaning (✅)
- Load data thật (không fallback, không synthetic)
- Salary parsing: test 6+ formats hoạt động
- Skill normalization: 1181 skills, 188 synonym entries
- Experience normalization: parse "2 nam", "3-5 nam"...
- Dedup: 293 groups, giảm 1736→1050
- **Lưu ý:** salary_raw giờ được giữ xuyên suốt (fix JobPosting)

## Notebook 3 — EDA (⚠️)
- Load 1050 rows, 43 cols ✅
- **F1 Skills:** chart top skills vẽ từ 79 jobs có skills (giới hạn)
- **F2 Salary~exp/city:** 494 salary rows thật, boxplot vẽ được ✅
- **F4 Hidden rate:** salary_hidden 557 jobs ✅
- **Lưu ý:** City có tỉnh lẻ (Bình Dương 46, Đồng Nai 32, Long An 26) — chưa filter sạch

## Notebook 4 — Machine Learning (⚠️)
- **Dùng data THẬT** — "Rows with real salary: 494" (không synthetic) ✅
- Baseline: RMSE 36.9, MAE 14.5, R² -0.02
- Linear: RMSE 36.7, R² -0.12
- Decision Tree: RMSE 36.6, R² -0.007
- Random Forest: RMSE 36.7, R² -0.009
- **Vấn đề:** tất cả model R² âm — không tốt hơn baseline. Nguyên nhân:
  - Salary variance cao (std 13.5, mean 22.3 triệu)
  - Features hạn chế (chủ yếu city + experience, thiếu skills/company)
  - Data salary ít (494 rows) so với variance

## Vấn đề chính còn tồn tại

1. **Skills thấp (79/1050 = 7.5%)** — careerviet (92% data) listing không có skills, chỉ itviec/topcv/glints có. Glints skills thật (Freight Pricing...) nhưng chỉ 14 jobs vào data.
2. **Experience thấp (8%)** — hầu hết careerviet listing không có exp field.
3. **City có tỉnh lẻ** — Bình Dương, Đồng Nai, Long An xuất hiện (do careerviet listing), không phải chỉ 4 TP chính.
4. **ML R² âm** — model không dự đoán tốt hơn baseline. Đây là giới hạn data thật (thiếu feature).

## Đáp ứng yêu cầu

| Yêu cầu | Trạng thái |
|---------|-----------|
| A6 ≥1000 records | ✅ 1050 |
| A9 Baseline | ✅ |
| A10 ≥2 models | ✅ Linear, DT, RF |
| A11 Clustering/Reco | ✅ |
| A14 Không đánh giá train | ✅ |
| A15 10+ error cases | ✅ |
| F1 Top skills | ⚠️ ít data skills |
| F2 Salary theo exp/city | ⚠️ có data nhưng variance cao |
| F4 Hidden salary rate | ✅ |
| F5 ML error | ⚠️ R² âm (giới hạn data) |

## Kết luận
- **Đã chuyển hoàn toàn sang data thật** — không còn fallback/synthetic trong notebook
- Đạt đủ records, salary thật, 4 notebooks chạy end-to-end
- **Còn giới hạn:** skills/exp thấp do nguồn (careerviet listing), ML R² âm do thiếu feature
- Hướng cải thiện: tăng itviec/glints jobs (có skills/exp đầy đủ), giảm careerviet tỉ lệ
