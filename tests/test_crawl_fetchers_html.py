import pytest

from src.crawl.fetchers import fetch_careerviet, fetch_site, fetch_timviecnhanh, fetch_topcv


class FakeClient:
    def __init__(self, pages):
        self.pages = pages

    def get_text(self, url, *, site_name, headers=None, timeout=20):
        return self.pages[url]


def test_fetch_topcv_parses_cards():
    url = "https://www.topcv.vn/tim-viec-lam-backend-developer-tai-ho-chi-minh-kl2cr257cb258"
    html = """
    <html>
      <div class='job-item-search-result' data-job-id='123'>
        <h3 class='title'><a href='/viec-lam/backend-developer-123.html'>Backend Developer</a></h3>
        <a class='company'><span class='company-name'>FPT</span></a>
        <label class='title-salary'>Thỏa thuận</label>
        <span class='city-text'>Hồ Chí Minh & 2 nơi khác</span>
        <label class='exp'><span>1 năm</span></label>
      </div>
    </html>
    """
    jobs = fetch_topcv(keyword="backend-developer", max_pages=1, client=FakeClient({url: html}))
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Backend Developer"
    assert jobs[0]["company_name"] == "FPT"
    assert jobs[0]["salary_raw"] == "Thỏa thuận"


def test_fetch_careerviet_html_fallback():
    url = "https://careerviet.vn/viec-lam/python-trang-1-vi.html"
    html = """
    <html>
      <div class='job-item'>
        <a href='/vi/tim-viec-lam/python-123-vi.html'>Python Engineer</a>
        <span class='company-name'>VNG</span>
        <span class='location'>HCMC</span>
        <span class='salary'>10 - 15 triệu</span>
        <span class='tag'>Python</span>
        <span class='tag'>Django</span>
      </div>
    </html>
    """
    jobs = fetch_careerviet(keyword="python", max_pages=1, client=FakeClient({url: html}))
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Python Engineer"
    assert jobs[0]["company_name"] == "VNG"
    assert jobs[0]["city"] == "HCMC"


def test_fetch_timviecnhanh_raises_merged():
    with pytest.raises(RuntimeError, match="merged into vieclam24h"):
        fetch_timviecnhanh(keyword="python", max_pages=1, client=FakeClient({}))


def test_fetch_site_unknown_raises():
    with pytest.raises(KeyError):
        fetch_site("unknown", "python", 1)
