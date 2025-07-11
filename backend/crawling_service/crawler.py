"""
Web crawling service for Blog SEO Analyzer.

This module provides a platform-agnostic crawling system that can adapt to
different blog platforms while respecting robots.txt and rate limiting.
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from backend.shared.config import crawling_settings, settings
from backend.shared.models import CrawlResult


logger = logging.getLogger(__name__)


class PlatformDetector:
    """Detects blog platform from URL."""
    
    PLATFORM_PATTERNS = {
        "naver": [
            r"blog\.naver\.com",
            r"m\.blog\.naver\.com"
        ],
        "tistory": [
            r"\.tistory\.com",
            r"tistory\.com"
        ],
        "wordpress": [
            r"wordpress\.com",
            r"wp\.com",
            r"/wp-content/",
            r"/wp-includes/"
        ],
        "medium": [
            r"medium\.com",
            r"\.medium\.com"
        ],
        "brunch": [
            r"brunch\.co\.kr"
        ]
    }
    
    @classmethod
    def detect_platform(cls, url: str) -> Optional[str]:
        """
        Detect blog platform from URL.
        
        Args:
            url: Blog URL to analyze
            
        Returns:
            Platform name or None if not detected
        """
        url_lower = url.lower()
        
        for platform, patterns in cls.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform
        
        return None


class RateLimiter:
    """Rate limiter for respectful crawling."""
    
    def __init__(self):
        self.last_requests: Dict[str, float] = {}
        self.request_counts: Dict[str, int] = {}
    
    async def wait_if_needed(self, domain: str, platform: Optional[str] = None) -> None:
        """
        Wait if necessary to respect rate limits.
        
        Args:
            domain: Domain to rate limit
            platform: Platform type for specific limits
        """
        now = time.time()
        
        # Get platform-specific or default delay
        if platform and platform in crawling_settings.RATE_LIMITS:
            delay = crawling_settings.RATE_LIMITS[platform]["delay"]
        else:
            delay = settings.REQUEST_DELAY
        
        # Check if we need to wait
        if domain in self.last_requests:
            time_since_last = now - self.last_requests[domain]
            if time_since_last < delay:
                wait_time = delay - time_since_last
                logger.info(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                await asyncio.sleep(wait_time)
        
        self.last_requests[domain] = time.time()


class ContentExtractor:
    """Extracts content from different blog platforms."""
    
    def __init__(self, platform: Optional[str] = None):
        self.platform = platform
        self.selectors = self._get_selectors()
    
    def _get_selectors(self) -> Dict[str, str]:
        """Get platform-specific CSS selectors."""
        if self.platform and self.platform in crawling_settings.PLATFORM_SELECTORS:
            return crawling_settings.PLATFORM_SELECTORS[self.platform]
        
        # Default selectors for unknown platforms
        return {
            "title": "h1, title",
            "content": "article, .content, .post, .entry",
            "meta_description": "meta[name='description']",
            "author": ".author, .writer, .by",
            "date": ".date, .published, time"
        }
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
        """
        Extract content from parsed HTML.
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Original URL for context
            
        Returns:
            Dictionary with extracted content
        """
        result = {
            "title": self._extract_title(soup),
            "content": self._extract_content(soup),
            "meta_description": self._extract_meta_description(soup),
            "meta_keywords": self._extract_meta_keywords(soup),
            "author": self._extract_author(soup),
            "published_date": self._extract_date(soup),
            "links": self._extract_links(soup, url),
            "images": self._extract_images(soup, url)
        }
        
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        # Try platform-specific selector first
        title_elem = soup.select_one(self.selectors["title"])
        if title_elem:
            return title_elem.get_text(strip=True)
        
        # Fallback to HTML title
        title_elem = soup.find("title")
        if title_elem:
            return title_elem.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main content."""
        content_elem = soup.select_one(self.selectors["content"])
        if content_elem:
            # Remove script and style elements
            for script in content_elem(["script", "style", "nav", "footer"]):
                script.decompose()
            
            return content_elem.get_text(separator="\n", strip=True)
        
        return None
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        meta_elem = soup.find("meta", attrs={"name": "description"})
        if meta_elem:
            return meta_elem.get("content")
        
        # Try Open Graph description
        og_elem = soup.find("meta", attrs={"property": "og:description"})
        if og_elem:
            return og_elem.get("content")
        
        return None
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta keywords."""
        meta_elem = soup.find("meta", attrs={"name": "keywords"})
        if meta_elem:
            return meta_elem.get("content")
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author information."""
        author_elem = soup.select_one(self.selectors["author"])
        if author_elem:
            return author_elem.get_text(strip=True)
        
        # Try meta author
        meta_elem = soup.find("meta", attrs={"name": "author"})
        if meta_elem:
            return meta_elem.get("content")
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date."""
        date_elem = soup.select_one(self.selectors["date"])
        if date_elem:
            date_str = date_elem.get("datetime") or date_elem.get_text(strip=True)
            return self._parse_date(date_str)
        
        # Try meta date
        meta_elem = soup.find("meta", attrs={"name": "date"})
        if meta_elem:
            return self._parse_date(meta_elem.get("content"))
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y.%m.%d",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:len(fmt)], fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page."""
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith(("http://", "https://")):
                links.append(href)
            elif href.startswith("/"):
                links.append(urljoin(base_url, href))
        
        return list(set(links))  # Remove duplicates
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all images from the page."""
        images = []
        for img in soup.find_all("img", src=True):
            src = img["src"]
            if src.startswith(("http://", "https://")):
                images.append(src)
            elif src.startswith("/"):
                images.append(urljoin(base_url, src))
        
        return list(set(images))  # Remove duplicates


class BlogCrawler:
    """Main crawler class for blog content extraction."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=settings.CONCURRENT_REQUESTS)
        timeout = aiohttp.ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
        
        self.session = aiohttp.ClientSession(
            headers=crawling_settings.HEADERS,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def crawl_url(self, url: str, use_browser: bool = False) -> CrawlResult:
        """
        Crawl a single URL and extract content.
        
        Args:
            url: URL to crawl
            use_browser: Whether to use browser for JavaScript rendering
            
        Returns:
            CrawlResult with extracted data
        """
        start_time = time.time()
        
        try:
            # Detect platform
            platform = PlatformDetector.detect_platform(url)
            logger.info(f"Crawling {url} (platform: {platform})")
            
            # Rate limiting
            domain = urlparse(url).netloc
            await self.rate_limiter.wait_if_needed(domain, platform)
            
            # Choose crawling method
            if use_browser or self._needs_browser(platform):
                html_content, status_code = await self._crawl_with_browser(url)
            else:
                html_content, status_code = await self._crawl_with_http(url)
            
            # Parse content
            soup = BeautifulSoup(html_content, "html.parser")
            extractor = ContentExtractor(platform)
            content_data = extractor.extract_content(soup, url)
            
            response_time = time.time() - start_time
            
            return CrawlResult(
                url=url,
                success=True,
                status_code=status_code,
                platform=platform,
                response_time=response_time,
                **content_data
            )
        
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            response_time = time.time() - start_time
            
            return CrawlResult(
                url=url,
                success=False,
                error_message=str(e),
                response_time=response_time
            )
    
    async def _crawl_with_http(self, url: str) -> tuple[str, int]:
        """Crawl URL using HTTP client."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        async with self.session.get(url) as response:
            status_code = response.status
            html_content = await response.text()
            
            if status_code >= 400:
                raise Exception(f"HTTP {status_code}: {response.reason}")
            
            return html_content, status_code
    
    async def _crawl_with_browser(self, url: str) -> tuple[str, int]:
        """Crawl URL using headless browser (for JavaScript-heavy sites)."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                # Set user agent
                await page.set_extra_http_headers(crawling_settings.HEADERS)
                
                response = await page.goto(url, wait_until="domcontentloaded")
                
                if not response:
                    raise Exception("Failed to load page")
                
                # Wait for content to load
                await page.wait_for_timeout(2000)
                
                html_content = await page.content()
                status_code = response.status
                
                return html_content, status_code
            
            finally:
                await browser.close()
    
    def _needs_browser(self, platform: Optional[str]) -> bool:
        """Determine if platform needs browser rendering."""
        # Platforms that heavily use JavaScript
        browser_platforms = {"naver", "medium"}
        return platform in browser_platforms
    
    async def crawl_multiple(self, urls: List[str]) -> List[CrawlResult]:
        """
        Crawl multiple URLs concurrently.
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            List of CrawlResult objects
        """
        semaphore = asyncio.Semaphore(settings.CONCURRENT_REQUESTS)
        
        async def crawl_with_semaphore(url: str) -> CrawlResult:
            async with semaphore:
                return await self.crawl_url(url)
        
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        crawl_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                crawl_results.append(
                    CrawlResult(
                        url=urls[i],
                        success=False,
                        error_message=str(result)
                    )
                )
            else:
                crawl_results.append(result)
        
        return crawl_results


# Convenience function for single URL crawling
async def crawl_blog_url(url: str, use_browser: bool = False) -> CrawlResult:
    """
    Crawl a single blog URL.
    
    Args:
        url: Blog URL to crawl
        use_browser: Whether to use browser for JavaScript rendering
        
    Returns:
        CrawlResult with extracted data
    """
    async with BlogCrawler() as crawler:
        return await crawler.crawl_url(url, use_browser)


# Convenience function for multiple URLs
async def crawl_blog_urls(urls: List[str]) -> List[CrawlResult]:
    """
    Crawl multiple blog URLs concurrently.
    
    Args:
        urls: List of blog URLs to crawl
        
    Returns:
        List of CrawlResult objects
    """
    async with BlogCrawler() as crawler:
        return await crawler.crawl_multiple(urls) 