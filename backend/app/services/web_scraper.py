"""
Web scraping service for extracting main content from web pages.
Optimized for speed and better content extraction.
"""
from typing import Tuple, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re


class WebScraperService:
    """
    Service for scraping and extracting text content from web pages.
    Optimized with:
    - Faster HTML parsing (html.parser instead of lxml for speed)
    - Better content extraction using readability heuristics
    - Shorter timeout for faster failures
    - More aggressive junk removal
    """

    def __init__(self, timeout: int = 10):  # Reduced from 30s to 10s
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def scrape_url(self, url: str) -> Tuple[str, dict]:
        """
        Scrape content from a URL with optimized extraction.

        Args:
            url: Web page URL to scrape

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # Fetch the page with streaming disabled for faster response
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True,
                stream=False  # Load entire response at once (faster for small pages)
            )
            response.raise_for_status()

            # Use html.parser (built-in, faster than lxml for most cases)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title = self._extract_title(soup, url)

            # Remove junk elements BEFORE extracting text (more efficient)
            self._remove_junk_elements(soup)

            # Extract main content using multiple strategies
            text = self._extract_main_content(soup)

            # Clean and normalize text
            cleaned_text = self._clean_text(text)

            # Validate we got meaningful content
            if len(cleaned_text.strip()) < 50:
                raise ValueError(f"Extracted content too short ({len(cleaned_text)} chars). Page might be behind login/paywall or require JavaScript.")

            metadata = {
                "url": url,
                "title": title,
                "domain": parsed.netloc,
                "file_type": "webpage",
                "char_count": len(cleaned_text),
                "word_count": len(cleaned_text.split())
            }

            return cleaned_text, metadata

        except requests.Timeout:
            raise ValueError(f"Timeout fetching URL (>{self.timeout}s): {url}")
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse webpage: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title from various sources."""
        # Try <title> tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Try <h1> tag
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)

        # Fall back to domain
        return urlparse(url).netloc

    def _remove_junk_elements(self, soup: BeautifulSoup) -> None:
        """Remove non-content elements from the page."""
        # Remove scripts, styles, and other junk
        junk_tags = [
            "script", "style", "noscript", "iframe", "embed", "object",
            "nav", "footer", "header", "aside", "form", "button",
            "svg", "canvas", "video", "audio"
        ]
        for tag in soup(junk_tags):
            tag.decompose()

        # Remove elements with common junk class/id patterns
        junk_patterns = [
            "ad", "advertisement", "promo", "sponsor", "sidebar",
            "related", "comment", "social", "share", "cookie",
            "popup", "modal", "banner", "widget", "menu"
        ]

        for pattern in junk_patterns:
            # Remove by class
            for elem in soup.find_all(class_=lambda x: x and pattern in x.lower()):
                elem.decompose()
            # Remove by id
            for elem in soup.find_all(id=lambda x: x and pattern in x.lower()):
                elem.decompose()

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content using readability-style heuristics.
        Tries multiple strategies in order of preference.
        """
        # Strategy 1: Look for article/main semantic tags
        for selector in ['article', 'main', '[role="main"]']:
            content = soup.select_one(selector)
            if content:
                text = content.get_text(separator='\n', strip=True)
                if len(text) > 200:  # Only use if substantial
                    return text

        # Strategy 2: Look for common content containers
        for selector in ['.post-content', '.article-content', '.entry-content',
                        '.content', '#content', '.post', '.article']:
            content = soup.select_one(selector)
            if content:
                text = content.get_text(separator='\n', strip=True)
                if len(text) > 200:
                    return text

        # Strategy 3: Find the div with most <p> tags (likely the article body)
        best_container = None
        max_p_count = 0

        for div in soup.find_all(['div', 'section']):
            p_count = len(div.find_all('p'))
            if p_count > max_p_count:
                max_p_count = p_count
                best_container = div

        if best_container and max_p_count >= 3:
            text = best_container.get_text(separator='\n', strip=True)
            if len(text) > 200:
                return text

        # Strategy 4: Fall back to body
        if soup.body:
            return soup.body.get_text(separator='\n', strip=True)

        # Strategy 5: Last resort - entire document
        return soup.get_text(separator='\n', strip=True)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Split into lines
        lines = text.split('\n')

        # Filter out:
        # - Empty lines
        # - Very short lines (likely navigation/junk)
        # - Lines with mostly non-alphanumeric characters
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip very short lines (< 20 chars) unless they look like headers
            if len(line) < 20 and not (line[0].isupper() and ':' not in line):
                continue

            # Skip lines that are mostly symbols/numbers (likely navigation)
            alpha_chars = sum(c.isalpha() for c in line)
            if len(line) > 0 and alpha_chars / len(line) < 0.5:
                continue

            cleaned_lines.append(line)

        # Join with double newlines (paragraph breaks)
        cleaned_text = '\n\n'.join(cleaned_lines)

        # Remove excessive whitespace
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)

        return cleaned_text.strip()


def get_web_scraper_service() -> WebScraperService:
    """
    Get web scraper service instance.

    Returns:
        WebScraperService instance
    """
    return WebScraperService()
