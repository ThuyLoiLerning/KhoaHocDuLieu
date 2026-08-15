# Kịch bản trình bày

## Phân tích thị trường việc làm IT và gợi ý ứng viên bằng Machine Learning

**Chuyên đề 4 — Lập trình cho Khoa học Dữ liệu**  
**Người trình bày:** Nguyễn Minh Tân  
**Thời lượng gợi ý:** 12–15 phút

> Kịch bản này bám theo bộ slide đã chốt và nội dung sinh từ `scripts/generate_pptx_slides.py`. **Các câu hỏi nghiên cứu được trình bày tập trung ở Slide 4**; Slide 3 chỉ giới thiệu bối cảnh, vấn đề và mục tiêu. Mỗi slide gồm phần nói chính, điểm nhấn và câu chuyển tiếp.

---

## Slide 1 — Trang bìa

**Thời lượng:** 20 giây

**Nội dung trình bày:**

Kính thưa thầy và các bạn. Em xin trình bày Chuyên đề 4 với chủ đề **phân tích thị trường việc làm IT và gợi ý ứng viên bằng Machine Learning**.

Mục tiêu của đề tài là xây dựng một quy trình khoa học dữ liệu hoàn chỉnh: bắt đầu từ thu thập dữ liệu tuyển dụng, làm sạch và chuẩn hóa dữ liệu, phân tích các xu hướng trên thị trường, xây dựng mô hình dự báo lương, phân cụm thị trường và cuối cùng là gợi ý việc làm phù hợp với hồ sơ kỹ năng.

---

## Slide 2 — Nội dung trình bày

**Thời lượng:** 25 giây

**Nội dung trình bày:**

Bài trình bày gồm năm phần chính.

Đầu tiên là giới thiệu bài toán và các câu hỏi nghiên cứu. Tiếp theo là phương pháp thu thập, làm sạch và chuẩn hóa dữ liệu. Phần thứ ba trình bày các kết quả phân tích khám phá dữ liệu. Sau đó là kết quả của các mô hình Machine Learning, bao gồm dự báo lương, phân cụm và hệ thống gợi ý. Cuối cùng là các kết luận, hạn chế và hướng phát triển.

Cách sắp xếp này phản ánh đúng luồng của một dự án dữ liệu từ đầu vào đến kết quả ứng dụng.

---

## Slide 3 — Giới thiệu bài toán

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Thị trường tuyển dụng IT tại Việt Nam phát triển nhanh, nhưng thông tin việc làm đang phân tán trên nhiều nền tảng. Mỗi nền tảng lại sử dụng cách mô tả khác nhau về vị trí, mức lương, kỹ năng và kinh nghiệm.

Điều này tạo ra hai khó khăn. Với ứng viên, rất khó so sánh mức lương và yêu cầu kỹ năng giữa các tin tuyển dụng. Với người phân tích, dữ liệu không đồng nhất khiến việc tổng hợp và xây dựng mô hình trở nên khó khăn.

Đề tài giải quyết vấn đề này bằng cách thu thập dữ liệu từ bốn nguồn, chuẩn hóa các trường quan trọng như lương, kỹ năng và kinh nghiệm, sau đó dùng dữ liệu đã chuẩn hóa để phân tích và xây dựng các mô hình hỗ trợ quyết định.

Bộ dữ liệu hiện có **1.193 tin tuyển dụng**, đến từ **4 nguồn**, gồm **44 thuộc tính**. Một thách thức đáng chú ý là **56% tin không công khai lương**, nên bước xử lý dữ liệu có vai trò rất quan trọng.

Từ bối cảnh và mục tiêu đó, đề tài không trình bày các kết quả rời rạc mà tập trung trả lời năm câu hỏi nghiên cứu ở slide tiếp theo. Đây là phần nên nhấn mạnh ở **Slide 4**, vì Slide 3 chỉ đóng vai trò giới thiệu vấn đề và động lực nghiên cứu.

---

## Slide 4 — Câu hỏi nghiên cứu RQ1–RQ5

**Thời lượng:** 40 giây

**Nội dung trình bày:**

Đây là slide chính dùng để trình bày các câu hỏi nghiên cứu. Em sẽ đọc và giải thích nhanh từng câu, vì toàn bộ phần sau của bài trình bày đều quay lại trả lời năm câu hỏi này.

**RQ1:** Kỹ năng nào được nhà tuyển dụng yêu cầu nhiều nhất? Câu hỏi này được trả lời bằng EDA, đặc biệt là biểu đồ nhóm kỹ năng và top kỹ năng phổ biến.

**RQ2:** Lương thay đổi như thế nào theo kinh nghiệm và thành phố? Câu hỏi này giúp xác định các yếu tố thị trường có liên hệ rõ với mức lương.

**RQ3:** Có thể dự báo mức lương từ thông tin tuyển dụng không, và sai số là bao nhiêu? Câu hỏi này được đánh giá bằng các mô hình hồi quy với RMSE, MAE và R².

**RQ4:** Thị trường có thể chia thành những phân khúc việc làm nào? Câu hỏi này được xử lý bằng K-Means và Silhouette Score.

**RQ5:** Với một hồ sơ kỹ năng cụ thể, hệ thống có thể gợi ý việc làm phù hợp không? Câu hỏi này được trả lời bằng Content-based Recommendation và Cosine Similarity.

Như vậy, Slide 4 là bản đồ nghiên cứu của toàn bộ bài. Các slide sau lần lượt đi qua dữ liệu, phương pháp và kết quả để trả lời từng RQ.

---

## Slide 5 — Kiến trúc hệ thống

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Pipeline của đề tài gồm bốn giai đoạn.

Giai đoạn thứ nhất là thu thập dữ liệu từ bốn nguồn và 22 từ khóa liên quan đến việc làm IT. Giai đoạn thứ hai làm sạch và chuẩn hóa dữ liệu, bao gồm phân tích lương, chuẩn hóa kỹ năng, chuẩn hóa kinh nghiệm và loại bỏ bản ghi trùng.

Giai đoạn thứ ba là Feature Engineering. Ở bước này, dữ liệu số, dữ liệu phân loại và dữ liệu có thứ tự được xử lý bằng các phương pháp khác nhau thông qua `ColumnTransformer`.

Giai đoạn cuối cùng gồm ba hướng phân tích: dự báo lương bằng hồi quy, phân cụm thị trường bằng K-Means và gợi ý việc làm bằng Cosine Similarity.

Điểm quan trọng của kiến trúc này là dữ liệu được xử lý theo một luồng thống nhất, có thể tái chạy và kiểm tra ở từng bước.

---

## Slide 6 — Crawler v2: Thu thập dữ liệu

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Crawler v2 chạy theo vòng lặp qua từng nguồn và từng từ khóa. Mỗi lượt thu thập đều được ghi nhận trong lịch sử để có thể theo dõi tiến trình và tránh xử lý lặp không cần thiết.

Về kỹ thuật kết nối, hệ thống sử dụng `httpx`, đặt timeout và cho phép redirect. Để hạn chế bị chặn, crawler xoay vòng ba User-Agent, giới hạn tốc độ truy cập trong khoảng một đến ba giây và thử lại khi máy chủ trả về lỗi HTTP 429.

Hệ thống nhận diện trang bị chặn thông qua các dấu hiệu như captcha hoặc `cf-challenge`. Sau khi tải được nội dung, dữ liệu được trích xuất bằng bốn phương pháp: JSON-LD, `__NEXT_DATA__`, HTML Parsing và API JSON.

Dữ liệu thô được lưu theo từng nguồn dưới dạng CSV và JSON, kèm metadata để phục vụ việc kiểm tra và làm sạch ở các bước sau.

---

## Slide 7 — Làm sạch và chuẩn hóa dữ liệu

**Thời lượng:** 55 giây

**Nội dung trình bày:**

Dữ liệu tuyển dụng ban đầu có nhiều vấn đề không đồng nhất.

Thứ nhất, phần lương có thể bị ẩn hoặc được viết dưới nhiều dạng như khoảng lương, mức lương tối đa, mức lương tối thiểu, lương theo năm hoặc lương bằng USD. Thứ hai, cùng một kỹ năng có thể xuất hiện với nhiều tên gọi khác nhau, ví dụ `react`, `react.js` và `reactjs`. Thứ ba, kinh nghiệm thường được mô tả bằng văn bản tự do. Cuối cùng, một tin có thể được đăng lại trên nhiều nguồn hoặc ở nhiều thời điểm.

Để xử lý, `SalaryParser` dùng các biểu thức chính quy để nhận diện nhiều cấu trúc lương và quy đổi về triệu VND mỗi tháng. `SkillNormalizer` ánh xạ các tên đồng nghĩa về 45 kỹ năng chuẩn. `ExperienceNormalizer` chuyển mô tả kinh nghiệm về số năm và năm nhóm kinh nghiệm. `Deduplicator` loại bản ghi trùng qua nhiều pha kiểm tra.

Nhờ đó, dữ liệu có cấu trúc thống nhất hơn trước khi đưa vào EDA và Machine Learning.

---

## Slide 8 — Làm sạch: biểu đồ dữ liệu thực tế

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Biểu đồ bên trái cho thấy các trường liên quan đến lương và kinh nghiệm có tỷ lệ thiếu đáng kể. Nguyên nhân chính là nhiều tin tuyển dụng không công khai lương hoặc mô tả kinh nghiệm không theo một cấu trúc cố định.

Biểu đồ bên phải thể hiện phân bố số năm kinh nghiệm. Dữ liệu tập trung nhiều ở nhóm khoảng một đến ba năm, cho thấy phần lớn nhu cầu tuyển dụng thuộc nhóm Junior và Mid-level.

Hai biểu đồ giải thích vì sao đề tài không thể chỉ đưa dữ liệu thô vào mô hình. Cần có các bộ phân tích và chuẩn hóa riêng để giữ lại thông tin có thể sử dụng, đồng thời ghi nhận rõ mức độ thiếu dữ liệu.

---

## Slide 9 — Feature Engineering

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Sau khi làm sạch, dữ liệu được chuyển thành các đặc trưng phục vụ mô hình.

Nhóm numeric gồm `experience_years`; giá trị thiếu được điền bằng trung vị và sau đó chuẩn hóa. Nhóm categorical gồm thành phố, loại công việc, hình thức làm việc, trình độ học vấn, ngành nghề và quy mô công ty; các giá trị thiếu được gán là `Unknown` trước khi One-Hot Encoding.

Nhóm ordinal là `experience_bin`, được mã hóa nhưng vẫn giữ thứ tự từ entry đến lead.

Biến mục tiêu của bài toán dự báo là `salary_mid`, tính theo triệu VND mỗi tháng. Những cột thô như mã tin, mô tả dài và URL được loại bỏ để tránh đưa nhiễu trực tiếp vào mô hình.

Dữ liệu được chia theo tỷ lệ 80/20 và đánh giá bằng Cross-Validation để kiểm tra độ ổn định.

---

## Slide 10 — Dữ liệu sau xử lý

**Thời lượng:** 40 giây

**Nội dung trình bày:**

Sau quá trình thu thập và xử lý, bộ dữ liệu gồm **1.193 bản ghi**, **44 thuộc tính** và dữ liệu đến từ bốn nguồn tuyển dụng chính.

Tỷ lệ tin ẩn lương vẫn ở mức 56%, phản ánh đặc điểm thực tế của dữ liệu tuyển dụng. Độ phủ kỹ năng chi tiết là 6,6%, vì không phải tin nào cũng cung cấp danh sách kỹ năng có cấu trúc.

Các thống kê này cần được ghi nhớ khi diễn giải kết quả mô hình. Một mô hình có điểm số cao không đồng nghĩa với việc dữ liệu đã hoàn toàn đầy đủ hoặc đại diện tuyệt đối cho toàn bộ thị trường.

---

## Slide 11 — Phân tích khám phá dữ liệu

**Thời lượng:** 50 giây

**Nội dung trình bày:**

EDA cho thấy bốn phát hiện chính.

Thứ nhất, các nhóm Data Science và Programming xuất hiện với tần suất cao, cùng các kỹ năng như JavaScript, React, Kafka, Python, SQL và Docker.

Thứ hai, lương tăng theo kinh nghiệm. Mức trung bình tăng từ khoảng 10 triệu ở nhóm entry lên khoảng 35 triệu hoặc cao hơn ở nhóm lead.

Thứ ba, Hà Nội và TP.HCM có mức lương trung bình cao hơn các thành phố khác. Hình thức Remote và Hybrid cũng có xu hướng gắn với mức lương cao hơn On-site.

Thứ tư, các tin yêu cầu tiếng Anh có mức lương trung bình cao hơn khoảng 30%. Các vị trí cấp cao và vị trí quản lý cũng có tỷ lệ ẩn lương trên 50%.

Đây là các kết quả mô tả, chưa phải kết luận nhân quả; chúng giúp xác định những đặc trưng cần đưa vào các bước mô hình hóa tiếp theo.

---

## Slide 12 — EDA: biểu đồ chi tiết

**Thời lượng:** 55 giây

**Nội dung trình bày:**

Biểu đồ thứ nhất cho thấy phân bố tin tuyển dụng theo nhóm kỹ năng. Data Science và Programming chiếm tỷ trọng lớn, tiếp theo là DevOps và Database.

Biểu đồ thứ hai xếp hạng 20 kỹ năng phổ biến nhất. JavaScript đứng đầu với 376 tin, sau đó là React và Kafka. Điều này cho thấy nhà tuyển dụng không chỉ tìm kỹ năng phân tích dữ liệu mà còn đánh giá cao nền tảng lập trình và năng lực xây dựng hệ thống.

Biểu đồ thứ ba so sánh lương giữa các tin có và không yêu cầu tiếng Anh. Nhóm có yêu cầu tiếng Anh có mức lương trung bình cao hơn khoảng 30%, cho thấy tiếng Anh là một tín hiệu quan trọng trong thị trường việc làm IT.

Các kết quả này trả lời trực tiếp RQ1 và cung cấp bằng chứng ban đầu cho RQ2.

---

## Slide 13 — Kết quả mô hình dự báo lương

**Thời lượng:** 55 giây

**Nội dung trình bày:**

Bảng kết quả so sánh bốn mô hình dự báo lương.

Baseline có RMSE 8,97 triệu VND. Linear Regression giảm RMSE xuống 4,17 và đạt R² bằng 0,783, cho thấy các đặc trưng hiện có đã giải thích được phần lớn biến động lương.

Decision Tree đạt RMSE 0,60 và R² bằng 0,996. Random Forest gần như đạt điểm tuyệt đối trên tập dữ liệu hiện tại.

Tuy nhiên, kết quả rất cao của Decision Tree và Random Forest cần được diễn giải thận trọng. Dữ liệu hiện tại có tính tổng hợp và cấu trúc dễ dự đoán, nên khả năng overfit là đáng kể. Vì vậy, Linear Regression có thể được xem là kết quả tham chiếu thực tế hơn, còn Tree và Forest cần được kiểm chứng lại trên dữ liệu crawl thật.

---

## Slide 14 — SHAP: giải thích Decision Tree

**Thời lượng:** 45 giây

**Nội dung trình bày:**

SHAP được sử dụng để giải thích đóng góp của từng đặc trưng vào dự đoán của Decision Tree.

Kết quả cho thấy `experience_years` và các nhóm kỹ năng có ảnh hưởng lớn nhất. Các điểm có màu đỏ đại diện cho giá trị đặc trưng cao, còn điểm màu xanh đại diện cho giá trị thấp. Vị trí của điểm trên trục SHAP cho biết đặc trưng đẩy dự đoán lương lên hay kéo dự đoán xuống.

Điểm mạnh của SHAP là chuyển kết quả mô hình từ một con số dự báo thành một lời giải thích có thể đọc được. Nhờ đó, người dùng biết không chỉ mô hình dự đoán bao nhiêu mà còn hiểu yếu tố nào dẫn đến dự đoán đó.

---

## Slide 15 — Kết quả ML: biểu đồ

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Biểu đồ residual cho thấy sai số dự đoán tập trung quanh mức 0. Điều này cho thấy mô hình không có xu hướng luôn dự đoán cao hơn hoặc thấp hơn thực tế trong tập kiểm thử.

Biểu đồ so sánh mô hình thể hiện sự khác biệt rõ ràng giữa Baseline, Linear Regression, Decision Tree và Random Forest. Linear Regression cải thiện đáng kể so với Baseline nhưng vẫn giữ được khả năng diễn giải. Decision Tree và Random Forest có độ chính xác cao hơn nhiều, đồng thời cũng làm tăng cảnh báo về overfit.

Vì vậy, đánh giá mô hình cần kết hợp cả chỉ số định lượng, biểu đồ sai số và hiểu biết về nguồn gốc dữ liệu.

---

## Slide 16 — Phân cụm thị trường bằng K-Means

**Thời lượng:** 55 giây

**Nội dung trình bày:**

K-Means được sử dụng để tìm các phân khúc việc làm có đặc điểm tương đồng về lương, kinh nghiệm, thành phố, hình thức làm việc và kỹ năng.

Kết quả cho thấy có một số phân khúc tiêu biểu. Cluster 0 gồm nhóm Junior–Mid ở Hà Nội, lương trung bình khoảng 15,1 triệu. Cluster 1 là nhóm Mid–Senior ở TP.HCM với mức lương khoảng 27,1 triệu. Cluster 4 là nhóm Senior có mức lương cao, khoảng 41,9 triệu. Ngoài ra còn có nhóm Mid đa dạng và nhóm việc làm Remote.

Các cluster không chỉ khác nhau về mức lương mà còn phản ánh sự kết hợp giữa kinh nghiệm, địa điểm và hình thức làm việc. Điều này giúp mô tả thị trường theo phân khúc thay vì chỉ nhìn vào một mức lương trung bình chung.

---

## Slide 17 — K-Means: biểu đồ phân cụm

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Biểu đồ Silhouette được dùng để so sánh chất lượng phân cụm ở các giá trị k khác nhau. Điểm Silhouette khoảng 0,38 cho thấy các cụm có mức phân tách vừa phải: có cấu trúc nhưng vẫn tồn tại vùng chồng lấn.

Biểu đồ PCA 2D minh họa các tin tuyển dụng sau khi giảm chiều dữ liệu. Các điểm cùng màu thuộc cùng một cluster, giúp quan sát sự khác biệt giữa các nhóm trên không gian trực quan.

Kết quả này nên được dùng cho mục đích phân khúc và khám phá thị trường, không nên hiểu là ranh giới tuyệt đối giữa các loại việc làm.

---

## Slide 18 — SHAP: giải thích Linear Regression

**Thời lượng:** 45 giây

**Nội dung trình bày:**

Với Linear Regression, SHAP giải thích dự đoán dựa trên hệ số của mô hình và giá trị từng đặc trưng.

So với Decision Tree, mô hình tuyến tính dễ diễn giải hơn vì tác động của đặc trưng có quan hệ trực tiếp với dự đoán. Các đặc trưng quan trọng được xác định tương đối nhất quán giữa hai mô hình, đặc biệt là kinh nghiệm và nhóm kỹ năng.

Sự nhất quán này củng cố kết luận rằng kinh nghiệm và kỹ năng là các tín hiệu chính liên quan đến mức lương trong bộ dữ liệu. Tuy nhiên, đây vẫn là mối liên hệ trong dữ liệu quan sát, không phải bằng chứng rằng một đặc trưng đơn lẻ tạo ra toàn bộ mức lương.

---

## Slide 19 — Hệ thống gợi ý việc làm

**Thời lượng:** 50 giây

**Nội dung trình bày:**

Hệ thống gợi ý sử dụng phương pháp Content-based Filtering.

Danh sách kỹ năng của mỗi tin tuyển dụng được chuyển thành vector nhị phân bằng `MultiLabelBinarizer`. Sau đó, hệ thống tính Cosine Similarity giữa vector kỹ năng của ứng viên và vector kỹ năng của từng công việc.

Trong ví dụ minh họa, hồ sơ gồm Python, SQL và Machine Learning. Công việc Data Scientist có độ tương đồng cao nhất vì khớp đầy đủ các kỹ năng. ML Engineer và Data Engineer cũng phù hợp nhưng còn thiếu một số kỹ năng như Docker, Spark hoặc Airflow.

Giá trị của hệ thống không chỉ là đưa ra Top-3 việc làm mà còn chỉ ra khoảng cách kỹ năng để ứng viên biết nên bổ sung năng lực nào.

---

## Slide 20 — Gợi ý: phân bố Similarity

**Thời lượng:** 35 giây

**Nội dung trình bày:**

Biểu đồ này thể hiện phân bố điểm tương đồng giữa hồ sơ mẫu và các tin tuyển dụng trong kho dữ liệu.

Các công việc có similarity cao là những việc có nhiều kỹ năng trùng với hồ sơ. Những công việc có điểm thấp hơn vẫn có thể hữu ích nếu ứng viên muốn mở rộng hướng tìm kiếm, nhưng cần xem thêm danh sách kỹ năng còn thiếu.

Do hệ thống hiện tại là Content-based, kết quả phụ thuộc trực tiếp vào chất lượng danh sách kỹ năng. Nếu tin tuyển dụng thiếu kỹ năng hoặc sử dụng cách viết khác với từ điển chuẩn, điểm tương đồng có thể bị đánh giá thấp.

---

## Slide 21 — Kết luận

**Thời lượng:** 55 giây

**Nội dung trình bày:**

Đề tài đã xây dựng được một pipeline khoa học dữ liệu end-to-end, từ thu thập dữ liệu đến phân tích và ứng dụng.

Ở bài toán dự báo, Linear Regression đạt RMSE 4,17 và R² 0,783. Decision Tree đạt RMSE 0,60 nhưng cần thận trọng vì có dấu hiệu overfit trên dữ liệu hiện tại.

SHAP cho thấy kinh nghiệm và nhóm kỹ năng là các yếu tố quan trọng trong dự báo lương. K-Means nhận diện được các phân khúc thị trường khác nhau, với Silhouette Score khoảng 0,38. Hệ thống Content-based Recommendation có thể trả về Top-3 công việc phù hợp và chỉ ra kỹ năng còn thiếu.

Như vậy, năm câu hỏi nghiên cứu đã được trả lời bằng sự kết hợp giữa EDA, mô hình dự báo, giải thích mô hình, phân cụm và hệ thống gợi ý.

---

## Slide 22 — Hạn chế và hướng phát triển

**Thời lượng:** 55 giây

**Nội dung trình bày:**

Đề tài vẫn có một số hạn chế.

Thứ nhất, nhiều tin không công khai lương và dữ liệu kỹ năng có độ phủ thấp. Thứ hai, dữ liệu chưa phân bố đồng đều giữa các thành phố; TP.HCM chiếm tỷ trọng lớn hơn nhiều so với Đà Nẵng. Thứ ba, kết quả rất cao của Decision Tree và Random Forest cho thấy cần kiểm chứng thêm trên dữ liệu thật.

Trong tương lai, có thể mở rộng crawler để truy cập sâu hơn vào trang chi tiết, bổ sung nguồn dữ liệu và cập nhật theo thời gian. Về xử lý ngôn ngữ, có thể dùng NLP hoặc BERT để trích xuất thông tin từ mô tả công việc, thay vì chỉ phụ thuộc vào trường kỹ năng có sẵn.

Ngoài K-Means, có thể thử DBSCAN hoặc Hierarchical Clustering. Với hệ thống gợi ý, hướng phát triển phù hợp là kết hợp Content-based với Collaborative Filtering để tạo mô hình Hybrid Recommendation.

---

## Slide 23 — Cảm ơn

**Thời lượng:** 15 giây

**Nội dung trình bày:**

Trên đây là phần trình bày của em về phân tích thị trường việc làm IT và gợi ý ứng viên bằng Machine Learning.

Em xin cảm ơn thầy và các bạn đã lắng nghe. Em sẵn sàng tiếp nhận câu hỏi và trao đổi thêm về dữ liệu, quy trình xử lý, mô hình dự báo hoặc hệ thống gợi ý.

---

# Phụ lục — Câu trả lời nhanh khi được hỏi

## Vì sao Decision Tree có R² gần bằng 1?

Dữ liệu hiện tại có tính tổng hợp và các đặc trưng có thể liên hệ rất rõ với biến lương. Decision Tree vì vậy học được các quy luật gần như trực tiếp trên tập dữ liệu. Đây là dấu hiệu cần kiểm tra overfit, không nên xem là bằng chứng mô hình sẽ đạt kết quả tương tự trên dữ liệu thị trường thật.

## Vì sao không dùng luôn Random Forest?

Random Forest có điểm số rất cao trên tập hiện tại nhưng kết quả gần như hoàn hảo làm tăng nghi ngờ về overfit. Linear Regression có kết quả thấp hơn nhưng dễ diễn giải và phù hợp làm baseline thực tế hơn. Cần đánh giá lại cả hai mô hình trên dữ liệu thật, bằng Cross-Validation và tập kiểm thử độc lập.

## Vì sao tỷ lệ kỹ năng chỉ đạt 6,6%?

Không phải tin tuyển dụng nào cũng cung cấp kỹ năng dưới dạng có cấu trúc. Một số tin chỉ mô tả kỹ năng trong phần văn bản tự do hoặc không liệt kê rõ. Đây là lý do hướng phát triển cần dùng NLP để trích xuất kỹ năng từ mô tả công việc.

## Cosine Similarity hoạt động như thế nào?

Mỗi công việc và hồ sơ ứng viên được biểu diễn thành một vector kỹ năng. Cosine Similarity đo mức độ giống nhau về hướng giữa hai vector. Hai vector càng có nhiều kỹ năng chung thì điểm càng cao.

## Silhouette Score 0,38 có tốt không?

Đây là mức phân tách vừa phải. Các cluster có cấu trúc nhất định nhưng vẫn chồng lấn. Kết quả phù hợp cho mục tiêu khám phá và phân khúc thị trường, không nên diễn giải thành các nhóm hoàn toàn tách biệt.
