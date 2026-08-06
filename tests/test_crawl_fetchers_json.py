import httpx
import pytest

from src.crawl.fetchers import HttpClient, fetch_glints, fetch_itviec, fetch_vietnamworks, fetch_vieclam24h


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get_text(self, url, *, site_name, headers=None, timeout=20):
        self.calls.append((site_name, url))
        return self.pages[url]


def test_http_client_raises_on_blocked_response(monkeypatch):
    """Cloudflare/captcha challenge pages must raise, not return silently."""
    request = httpx.Request("GET", "https://example.test/jobs")
    blocked_html = '<html><body><div class="cf-challenge">Checking your browser...</div></body></html>'

    class SessionStub:
        verify = True

        def get(self, url, headers=None, timeout=None):
            return httpx.Response(200, text=blocked_html, request=request)

    client = HttpClient(session=SessionStub())
    with pytest.raises(RuntimeError, match="(?i)blocked"):
        client.get_text("https://example.test/jobs", site_name="itviec")


def test_http_client_retries_429(monkeypatch):
    request = httpx.Request("GET", "https://example.test/jobs")
    responses = [
        httpx.Response(429, headers={"Retry-After": "2"}, request=request),
        httpx.Response(200, text="<html>ok</html>", request=request),
    ]

    class SessionStub:
        verify = True

        def get(self, url, headers=None, timeout=None):
            return responses.pop(0)

    slept = []
    monkeypatch.setattr("time.sleep", lambda seconds: slept.append(seconds))

    client = HttpClient(session=SessionStub())
    assert client.get_text("https://example.test/jobs", site_name="itviec") == "<html>ok</html>"
    assert slept[0] >= 2


@pytest.mark.parametrize(
    "fetch_fn, url, html, expected_title, expected_company",
    [
        (
            fetch_itviec,
            "https://itviec.com/viec-lam-it?q=python&page=1",
            """
            <html>
              <script type='application/ld+json'>
              {"@type":"ItemList","itemListElement":[{"url":"https://itviec.com/jobs/1"}]}
              </script>
              <script type='application/ld+json'>
              {"@type":"JobPosting","title":"Backend Developer","hiringOrganization":{"name":"FPT"},"jobLocation":{"address":{"addressRegion":"HCMC"}},"baseSalary":{"value":{"value":3000,"unitText":"USD"}},"datePosted":"2026-08-04","description":"Python Django"}
              </script>
            </html>
            """,
            "Backend Developer",
            "FPT",
        ),
        (
            fetch_glints,
            "https://glints.com/vn/opportunities/jobs?keyword=python&page=1",
            """
            <html>
              <script id='__NEXT_DATA__' type='application/json'>
              {"props":{"pageProps":{"jobs":[{"title":"Data Engineer","company":{"name":"VNG"},"location":{"name":"Ho Chi Minh City"},"salary":{"minAmount":30000000,"maxAmount":45000000},"skills":[{"skill":{"name":"Python"},"mustHave":true}],"description":"Python Airflow"}]}}}
              </script>
            </html>
            """,
            "Data Engineer",
            "VNG",
        ),
        (
            fetch_vietnamworks,
            "https://www.vietnamworks.com/viec-lam?q=python&page=1",
            """
            <html>
              <script id='__NEXT_DATA__' type='application/json'>
              {"props":{"pageProps":{"outstandingJobs":[{"jobTitle":"Frontend Developer","company":{"name":"Viettel"},"location":"Hanoi","salary":"10-20 triệu","skillTags":[{"key":"React"}],"jobDescription":"React TypeScript"}]}}}
              </script>
            </html>
            """,
            "Frontend Developer",
            "Viettel",
        ),
        (
            fetch_vieclam24h,
            "https://vieclam24h.vn/viec-lam-tp-hcm-p122.html?occupation_ids[]=8&occupation_ids[]=7&sort_q=priority_max,desc&page=1",
            """
            <html>
              <script id='__NEXT_DATA__' type='application/json'>
              {"props":{"initialState":{"api":{"getJobList":{"data":[{"title":"QA Engineer","company":{"name":"FPT Software"},"city":"Ho Chi Minh","salary_raw":"Thỏa thuận","skills":["Testing"],"description":"Selenium"}]}}}}}
              </script>
            </html>
            """,
            "QA Engineer",
            "FPT Software",
        ),
    ],
)
def test_next_data_family_parsers(fetch_fn, url, html, expected_title, expected_company):
    client = FakeClient({url: html})
    jobs = fetch_fn(keyword="python", max_pages=1, client=client)
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == expected_title
    assert jobs[0]["company_name"] == expected_company
def test_fetch_vietnamworks_html_fallback():
    """HTML fallback khi __NEXT_DATA__ trống — parse cấu trúc div.job-item."""
    listing_html = """
    <html>
      <div class="job-item">
        <h3 class="job-title"><a href="/viec-lam/python-developer-123">Python Developer</a></h3>
        <span class="company-name">FPT Software</span>
        <span class="location">Hồ Chí Minh</span>
        <span class="salary">10 - 15 triệu</span>
        <span class="tag">Python</span>
        <span class="tag">Django</span>
      </div>
      <div class="job-item">
        <h3 class="job-title"><a href="/viec-lam/data-engineer-456">Data Engineer</a></h3>
        <span class="company-name">VNG</span>
        <span class="location">Hà Nội</span>
        <span class="salary">20 - 30 triệu</span>
        <span class="tag">Python</span>
        <span class="tag">SQL</span>
      </div>
    </html>
    """
    jobs = fetch_vietnamworks(
        keyword="python", max_pages=1,
        client=FakeClient({"https://www.vietnamworks.com/viec-lam?q=python&page=1": listing_html}),
    )
    assert len(jobs) == 2
    assert jobs[0]["job_title"] == "Python Developer"
    assert jobs[0]["company_name"] == "FPT Software"
    assert jobs[0]["city"] == "Hồ Chí Minh"
    assert jobs[0]["salary_raw"] == "10 - 15 triệu"
    assert set(jobs[0]["skills_raw"]) == {"Python", "Django"}
    assert jobs[0]["source_url"] == "https://www.vietnamworks.com/viec-lam/python-developer-123"


def test_fetch_itviec_follows_itemlist_to_details():
    """Listing page has only ItemList of URLs; details carry JobPosting."""
    listing_html = """
    <html>
      <script type='application/ld+json'>
      {"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":1,"url":"https://itviec.com/jobs/1"}]}
      </script>
    </html>
    """
    detail_html = """
    <html>
      <script type='application/ld+json'>
      {"@type":"JobPosting","title":"Backend Developer","hiringOrganization":{"name":"FPT"},"jobLocation":{"address":{"addressRegion":"HCMC"}},"baseSalary":{"value":{"value":3000,"unitText":"USD"}},"datePosted":"2026-08-04","description":"Python Django"}
      </script>
    </html>
    """
    pages = {
        "https://itviec.com/viec-lam-it?q=python&page=1": listing_html,
        "https://itviec.com/jobs/1": detail_html,
    }
    jobs = fetch_itviec(keyword="python", max_pages=1, client=FakeClient(pages))
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Backend Developer"
    assert jobs[0]["company_name"] == "FPT"
    assert jobs[0]["source_url"] == "https://itviec.com/jobs/1"
