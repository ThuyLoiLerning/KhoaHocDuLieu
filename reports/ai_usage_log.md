# AI Usage Log (Yêu cầu B11, L1-L3)

## Prompt, đầu ra, kiểm chứng, chỉnh sửa

| # | Prompt | Đầu ra | Kiểm chứng | Chỉnh sửa nhóm |
|---|--------|--------|------------|----------------|
| 1 | "Đọc nội dung file assignment" | Toàn bộ text yêu cầu chuyên đề 4 | So sánh với PDF gốc | OK giữ nguyên |
| 2 | "Liệt kê tất cả yêu cầu chuyên đề 4" | ~70+ requirements trong 14 groups A-N | Đối chiếu với đề gốc từng mục | OK giữ nguyên |
| 3 | "Tạo plan 8 buổi" | Lộ trình chi tiết từng buổi | Xem xét khả thi với 2 member | Điều chỉnh phân công lại member |
| 4 | "Thay dữ liệu giả bằng cào thật" | Cấu trúc Crawler v2 (Fetchers, Normalizer, Pipeline) | Test thực tế trên 4 sites | Thêm xử lý JSON-LD, __NEXT_DATA__, HTML fallback |
| 5 | "Tạo JobPosting/Skill/Company OOP" | Code dataclasses | Chạy test, kiểm tra fields theo đề | Thêm __post_init__ normalization |
| 6 | "Tạo SalaryParser regex patterns" | 6 patterns + test cases | Chạy test_salary_parser.py | Thêm pattern USD/$/năm, swap min-max |
| 7 | "Tạo SkillNormalizer synonym map" | 35+ mapping entries | Chạy test_skill_normalizer.py | Thêm fuzzy match khi không exact |
| 8 | "Tạo ExperienceNormalizer" | Regex + binning | Chạy test thủ công | Thêm pattern "mới ra trường" |
| 9 | "Tạo feature pipeline" | ColumnTransformer config | Kiểm tra shape đầu ra | Thêm handle_unknown cho OHE |
| 10 | "Tạo ML models" | Baseline + Linear + Tree + RF | So sánh metrics cross-validation | Thêm error analysis |
| 11 | "Tạo RecommendationEngine" | Content-based cosine similarity | Chạy test_recommendation.py | Thêm matched/missing skills |
| 12 | "Tạo EDA charts" | 8+ charts với commentary | Review từng biểu đồ | Sửa colors, thêm heatmap |

## Nguyên tắc kiểm chứng kết quả AI (L2)

1. **Code**: Chạy test cases sau mỗi lần sinh code. Nếu test fail → sửa prompt hoặc sửa code tay.
2. **Data**: Sau khi crawl, inspect 10-20 dòng đầu, kiểm tra null rates, unique values.
3. **ML**: So sánh metrics với baseline. Nếu RMSE cao hơn baseline → tìm nguyên nhân.
4. **Chart**: Review trực quan: title, axis labels, legend, color, insight.
5. **Plan**: Đối chiếu với requirements list sau mỗi buổi.

## Phần chỉnh sửa của nhóm (L3)

- **Scraper selectors**: Mỗi site có HTML khác nhau → team phải inspect element và sửa CSS selectors phù hợp.
- **Salary patterns**: Team thêm pattern sau khi kiểm tra dữ liệu thực tế (ví dụ: "$1,500 - $2,000").
- **Synonym map**: Team bổ sung từ điển kỹ năng theo domain cụ thể (Vue.js, Flutter, etc).
- **Test thresholds**: Team điều chỉnh threshold cho dedup/dựa trên data thực.

## Prompt chi tiết (mẫu)

### Prompt: Tạo salary parser
> Tạo Python class SalaryParser để parse lương từ các định dạng thực tế ở Việt Nam:
> - "10-15 triệu" → min=10, max=15
> - "tới 20 triệu" → max=20
> - "1200-1800 USD" → *25000
> - "cạnh tranh" → hidden=True
> Xử lý cả dấu en dash, khoảng trắng, VND/năm, $/USD. Trả về dataclass ParsedSalary.

### Prompt: Tạo recommendation engine
> Tạo RecommendationEngine dùng content-based filtering (cosine similarity) để gợi ý việc làm theo hồ sơ kỹ năng. Dùng MultiLabelBinarizer từ sklearn, return list[Recommendation] có kèm skill match/missing.

---

*Note: Đây là AI Usage Log đầy đủ. Team cập nhật sau mỗi buổi làm việc.*