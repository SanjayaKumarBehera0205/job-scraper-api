import hashlib
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models import JobSource


@dataclass
class ScrapedJob:
    external_key: str
    title: str
    company: str | None
    location: str | None
    url: str
    description: str | None


def _text(element) -> str | None:
    return element.get_text(" ", strip=True) if element else None


def parse_jobs(html: str, source: JobSource) -> list[ScrapedJob]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[ScrapedJob] = []
    for card in soup.select(source.job_selector):
        title = _text(card.select_one(source.title_selector))
        link = card.select_one(source.link_selector)
        href = link.get("href") if link else None
        if not title or not href:
            continue
        job_url = urljoin(source.url, href)
        company = _text(card.select_one(source.company_selector)) if source.company_selector else None
        location = _text(card.select_one(source.location_selector)) if source.location_selector else None
        description = _text(card.select_one(source.description_selector)) if source.description_selector else None
        key = hashlib.sha256(job_url.encode("utf-8")).hexdigest()
        results.append(ScrapedJob(key, title, company, location, job_url, description))
    return results


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public HTTP and HTTPS URLs are allowed")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    except socket.gaierror as exc:
        raise ValueError("Source hostname could not be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("Private or local network addresses are not allowed")


async def fetch_source(source: JobSource) -> str:
    validate_public_url(source.url)
    headers = {"User-Agent": settings.scraper_user_agent}
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True) as client:
        response = await client.get(source.url, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type:
            raise ValueError("The source did not return HTML")
        return response.text
