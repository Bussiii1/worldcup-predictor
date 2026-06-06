import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter


class WorldCupCrawler:
    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            extra_args=["--disable-blink-features=AutomationControlled"],
        )
        self.run_config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            wait_until="networkidle",
            page_timeout=30000,
            content_filter=PruningContentFilter(threshold=0.45),
        )
        self.run_config_raw = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            wait_until="networkidle",
            page_timeout=30000,
        )

    async def fetch(self, url: str) -> str:
        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(url=url, config=self.run_config)
                if result.success:
                    return result.markdown.fit_markdown or result.markdown.raw_markdown or ""
                return ""
        except Exception:
            return ""

    async def fetch_raw_html(self, url: str) -> str:
        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(url=url, config=self.run_config_raw)
                if result.success:
                    return result.html or ""
                return ""
        except Exception:
            return ""

    async def fetch_many(self, urls: list) -> list:
        return await asyncio.gather(*[self.fetch(url) for url in urls])
