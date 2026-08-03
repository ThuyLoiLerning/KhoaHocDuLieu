import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.data.playwright_crawler import PlaywrightCrawler

def test_extract_sections():
    pc = PlaywrightCrawler()
    html = """<html><body>
        <div class="job-description"><h3>Mô tả</h3><p>Develop software</p></div>
        <div class="job-requirement"><h3>Yêu cầu</h3><p>Python 3+</p></div>
        <div class="benefits"><p>Health insurance</p></div>
    </body></html>"""
    sections = pc.extract_sections(html)
    assert "mo_ta" in sections or "job-description" in sections
    pc.close()
