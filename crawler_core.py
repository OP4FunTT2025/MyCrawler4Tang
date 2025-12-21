"""Core crawling utilities shared by the CLI and Flask entry points."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
DEFAULT_IMAGE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" 
    "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
)


@dataclass
class CrawlerConfig:
    """Runtime configuration for the forum crawler."""

    base_url: str = "https://btd5.thsf7.net"
    cookie: str | None = os.environ.get("CRAWLER_COOKIE")
    image_cookie: str | None = os.environ.get("CRAWLER_IMAGE_COOKIE") or os.environ.get(
        "CRAWLER_COOKIE"
    )
    timeout: int = 10
    image_timeout: int = 10

    def build_headers(self) -> dict[str, str]:
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def build_image_headers(self) -> dict[str, str]:
        headers = {"User-Agent": DEFAULT_IMAGE_USER_AGENT}
        # Only use the dedicated image cookie for image requests
        if self.image_cookie:
            headers["Cookie"] = self.image_cookie
        return headers


def sanitize_name(value: str, max_length: int = 80) -> str:
    """Return a filesystem-safe slug derived from value."""
    value = value.strip()
    if not value:
        return "unnamed"
    value = re.sub(r"[\\/*?:\"<>|]", "_", value)
    value = re.sub(r"\s+", "_", value)
    return value[:max_length]


def normalize_thread_path(href: str) -> str | None:
    """Normalize link targets and drop ones that do not reference a thread page."""
    if not href:
        return None
    href = href.strip()
    if href.startswith("javascript"):
        return None
    if href.startswith("#"):
        return None

    if href.startswith(("http://", "https://")):
        parsed = urlparse(href)
        href = parsed.path.lstrip("/")

    href = href.lstrip("/")
    if not href.startswith("thread-") or ".html" not in href:
        return None

    # ensure the second-to-last segment is always "1" so we only crawl the first page
    parts = href.split("-")
    if len(parts) >= 4 and parts[-1].endswith(".html"):
        parts[2] = "1"
        href = "-".join(parts)
    return href


def extract_thread_paths(html: bytes | str) -> List[str]:
    """Extract unique thread paths from forum HTML."""
    soup = BeautifulSoup(html, "lxml")
    results: list[str] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        normalized = normalize_thread_path(link["href"])
        if normalized and normalized not in seen:
            seen.add(normalized)
            results.append(normalized)
    return results


def extract_magnet_links(soup: BeautifulSoup) -> List[str]:
    """Return magnet links discovered in the thread soup."""
    magnets: list[str] = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text.startswith("magnet:?xt"):
            magnets.append(text)
    return magnets


def extract_image_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract absolute image URLs from the provided soup."""
    urls: list[str] = []
    seen: set[str] = set()
    for img in soup.find_all("img"):
        candidate = img.get("file") or img.get("src")
        if not candidate:
            continue
        candidate = candidate.strip()
        # print(candidate)
        if not candidate:
            continue
        if not candidate.startswith(("http://", "https://")):
            candidate = urljoin(base_url, candidate)
        if candidate not in seen:
            seen.add(candidate)
            urls.append(candidate)
            # print(candidate)
    return urls


class ForumCrawler:
    """Lightweight crawler that encapsulates HTTP sessions and parsing helpers."""

    def __init__(self, config: CrawlerConfig | None = None):
        self.config = config or CrawlerConfig()
        self.session = requests.Session()
        self.image_session = requests.Session()
        self._refresh_sessions()

    def update_config(
        self,
        *,
        cookie: str | None = None,
        image_cookie: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Update runtime config and refresh HTTP headers."""
        new_config = replace(self.config)
        if cookie is not None:
            new_config.cookie = cookie
        if image_cookie is not None:
            new_config.image_cookie = image_cookie
        if base_url:
            new_config.base_url = base_url.rstrip("/")
        self.config = new_config
        self._refresh_sessions()

    def _refresh_sessions(self) -> None:
        self.session.headers.clear()
        self.session.headers.update(self.config.build_headers())
        self.session.cookies.clear()
        if self.config.cookie:
            self._apply_cookie_string(self.session, self.config.cookie)
        self.image_session.headers.clear()
        self.image_session.headers.update(self.config.build_image_headers())
        self.image_session.cookies.clear()
        if self.config.image_cookie:
            self._apply_cookie_string(self.image_session, self.config.image_cookie)

    @staticmethod
    def _apply_cookie_string(session: requests.Session, cookie_header: str) -> None:
        """Populate a session's cookie jar from a raw Cookie header string."""
        for part in cookie_header.split(";"):
            if "=" not in part:
                continue
            name, value = part.strip().split("=", 1)
            if name:
                session.cookies.set(name, value)

    def fetch_thread_paths_from_forum_url(self, forum_url: str) -> List[str]:
        response = self.session.get(forum_url, timeout=self.config.timeout)
        response.raise_for_status()
        return extract_thread_paths(response.content)

    def fetch_thread_paths(self, forum_id: str, page: int) -> List[str]:
        forum_url = f"{self.config.base_url}/forum-{forum_id}-{page}.html"
        return self.fetch_thread_paths_from_forum_url(forum_url)

    def fetch_thread_details(
        self, thread_path_or_url: str
    ) -> tuple[list[str], list[str], BeautifulSoup]:
        thread_url = self._ensure_absolute(thread_path_or_url)
        response = self.session.get(thread_url, timeout=self.config.timeout)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.content, "lxml")
        magnets = extract_magnet_links(soup)
        images = extract_image_urls(soup, thread_url)
        return magnets, images, soup

    def download_images(
        self, image_urls: Sequence[str], destination_dir: str
    ) -> Tuple[int, List[str]]:
        """Download unique images to destination_dir using configured headers/cookies."""
        if not image_urls:
            return 0, []

        Path(destination_dir).mkdir(parents=True, exist_ok=True)
        saved = 0
        skipped: list[str] = []
        seen_urls: set[str] = set()
        seen_names: set[str] = set()

        for index, image_url in enumerate(image_urls, 1):
            if image_url in seen_urls:
                continue
            seen_urls.add(image_url)

            try:
                response = self.image_session.get(
                    image_url,
                    timeout=self.config.image_timeout,
                    allow_redirects=True,
                    stream=True,
                )
                response.raise_for_status()
            except requests.RequestException as exc:  # pragma: no cover - network failures vary
                skipped.append(f"{image_url} ({exc})")
                continue

            content_type = response.headers.get("Content-Type", "")
            if content_type and not content_type.startswith("image/"):
                response.close()
                skipped.append(f"{image_url} (content-type {content_type})")
                continue

            parsed_path = Path(urlparse(image_url).path)
            filename = sanitize_name(parsed_path.stem or f"image_{index}")
            extension = parsed_path.suffix
            if not extension and content_type.startswith("image/"):
                extension = f".{content_type.split(';')[0].split('/')[-1]}"
            if not extension:
                extension = ".jpg"

            candidate = f"{filename}{extension}"
            counter = 1
            while candidate in seen_names:
                candidate = f"{filename}_{counter}{extension}"
                counter += 1
            seen_names.add(candidate)

            target_path = Path(destination_dir) / candidate
            try:
                with response:
                    with target_path.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                handle.write(chunk)
                saved += 1
            except OSError as exc:  # pragma: no cover - filesystem errors vary
                skipped.append(f"{image_url} ({exc})")
        return saved, skipped

    def _ensure_absolute(self, thread_path_or_url: str) -> str:
        if thread_path_or_url.startswith(("http://", "https://")):
            return thread_path_or_url
        return f"{self.config.base_url.rstrip('/')}/{thread_path_or_url.lstrip('/')}"


__all__ = [
    "CrawlerConfig",
    "ForumCrawler",
    "extract_magnet_links",
    "extract_thread_paths",
    "sanitize_name",
]
