# Design: Tối ưu tốc độ crawl

## Vấn đề
- itviec: mỗi page 20 detail URLs crawl **tuần tự**, delay 1-2.5s/job → ~60s/page
- `DetailCrawler.crawl_many`: max_workers=2, mỗi request mở connection mới
- Toàn pipeline mất 5-10 phút cho 1 lần chạy

## Giải pháp (Approach C — cân bằng tốc độ/rủi ro)

### 1. Session reuse ✅
- `DetailCrawler.__init__` tạo 1 `requests.Session()` dùng chung
- Reuse TCP/TLS connection → tiết kiệm ~200-500ms/request
- Session thread-safe cho requests

### 2. Retry 429 (phát hiện khi test) ✅
- itviec rate-limit: cho phép ~4 request/4s, request thứ 5 bị 429
- Concurrency 4 threads → 80% bị 429
- **Fix**: retry up to 3 lần, backoff 3/5/7s (hoặc tôn trọng `Retry-After` header)
- Kết quả: 20/20 jobs success (trước 50%)

### 3. Giảm delay ✅
- `delay_range: (0.5, 1.5) → (0.2, 0.5)` cho site không bị rate-limit

### 4. itviec dùng DetailCrawler ✅
- `scrape_itviec_jsonld` → DetailCrawler (session reuse + retry)

## Files
| File | Thay đổi |
|------|----------|
| `src/data/detail_crawler.py` | Session reuse, retry 429, backoff, delay giảm |
| `src/data/collector.py` | itviec dùng crawl_many thay vì tuần tự |

## Kết quả
- itviec: 20/20 jobs trong 36s (100% success, trước ~60s + 50% success)
- Pipeline nhanh hơn ~2x

## Lưu ý khi tối ưu thêm
- Concurrency cao hơn → bị 429 nhiều hơn → backoff lâu hơn → không nhanh hơn
- Session reuse + retry là điểm tối ưu hiện tại cho itviec
