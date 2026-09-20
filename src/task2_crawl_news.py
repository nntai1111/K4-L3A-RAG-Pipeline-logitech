"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium

-> Dùng Firecrawl or bất cứ công cụ nào bạn quen

CẢNH BÁO: chạy lại module này sẽ ghi đè article_01..07.json bằng nội dung mới
nhất của trang nguồn. Corpus đổi thì phải chạy lại Task 3, Task 4 và toàn bộ
evaluation, vì số liệu trong RESULT.md gắn với đúng bản crawl hiện tại.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# Thứ tự ở đây quyết định tên file: phần tử thứ n -> article_{n:02d}.json
ARTICLE_URLS = [
    "https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/sleep/art-20048379",
    "https://www.vinmec.com/vie/bai-viet/17-loi-khuyen-de-ngu-ngon-hon-vao-ban-dem-vi",
    "https://www.vinmec.com/vie/bai-viet/cac-tac-hai-cua-thuc-dem-ngu-ngay-vi",
    "https://www.ncbi.nlm.nih.gov/books/NBK20359/",
    "https://www.ncbi.nlm.nih.gov/books/NBK591812/",
    "https://bvnguyentriphuong.com.vn/tin-tu-cac-co-so-y-te/cac-giai-doan-cua-giac-ngu",
    "https://tamanhhospital.vn/giac-ngu/",
]


async def crawl_article(url: str) -> dict:
    """Crawl một URL và trả về dict đủ 4 field bắt buộc."""
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        markdown = getattr(result, "markdown", "") or ""
        # Crawl4AI có thể trả object markdown thay vì str tuỳ phiên bản.
        if not isinstance(markdown, str):
            markdown = getattr(markdown, "raw_markdown", "") or str(markdown)

        metadata = getattr(result, "metadata", None) or {}
        return {
            "url": url,
            "title": metadata.get("title") or "Unknown",
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": markdown,
        }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
