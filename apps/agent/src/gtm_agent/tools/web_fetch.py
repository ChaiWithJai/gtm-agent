"""Web fetching tools for product URL scraping."""

import re
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool

# Timeout for web requests (10 seconds)
REQUEST_TIMEOUT = 10.0


def _validate_url(url: str) -> str | None:
    """Validate and normalize URL.

    Args:
        url: URL to validate

    Returns:
        Normalized URL or None if invalid
    """
    try:
        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)

        # Check for valid scheme and netloc
        if parsed.scheme not in ("http", "https"):
            return None
        if not parsed.netloc:
            return None

        return url
    except Exception:
        return None


def _extract_company_name(url: str, html: str) -> str | None:
    """Extract company name from URL or HTML.

    Args:
        url: The page URL
        html: Page HTML content

    Returns:
        Company name or None
    """
    # Try to get from title tag
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        # Clean up common suffixes
        for suffix in [" - Home", " | Home", " - Official", " | Official"]:
            if title.endswith(suffix):
                title = title[: -len(suffix)]
        return title.split("|")[0].split("-")[0].strip()

    # Fall back to domain name
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    company = domain.split(".")[0].title()
    return company


def _extract_description(html: str) -> str | None:
    """Extract product description from HTML.

    Args:
        html: Page HTML content

    Returns:
        Description or None
    """
    # Try meta description
    meta_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if meta_match:
        return meta_match.group(1).strip()

    # Try og:description
    og_match = re.search(
        r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if og_match:
        return og_match.group(1).strip()

    return None


def _extract_features(html: str) -> list[str]:
    """Extract key features from HTML.

    Args:
        html: Page HTML content

    Returns:
        List of extracted features (may be empty)
    """
    features = []

    # Look for common feature patterns in h2/h3 tags
    heading_matches = re.findall(r"<h[23][^>]*>([^<]+)</h[23]>", html, re.IGNORECASE)
    for heading in heading_matches[:10]:  # Limit to first 10
        text = heading.strip()
        # Filter out navigation/footer headings
        if len(text) > 5 and len(text) < 100:
            if not any(
                skip in text.lower()
                for skip in ["contact", "about us", "footer", "menu", "navigation"]
            ):
                features.append(text)

    return features[:5]  # Max 5 features


@tool
def web_fetch(url: str) -> dict:
    """Fetch and extract product information from URL.

    This tool fetches the given URL and extracts key product information
    including company name, description, and features. It has a 10-second
    timeout and handles errors gracefully.

    Args:
        url: Product/company website URL

    Returns:
        Dict with company_name, description, features, success status, and error if any
    """
    # Validate URL
    validated_url = _validate_url(url)
    if not validated_url:
        return {
            "success": False,
            "company_name": None,
            "product_description": None,
            "key_features": [],
            "source_url": url,
            "error": "Invalid URL format",
        }

    try:
        # Fetch the URL
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            response = client.get(
                validated_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; GTMAgent/1.0)",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            response.raise_for_status()

        html = response.text

        # Extract information
        company_name = _extract_company_name(validated_url, html)
        description = _extract_description(html)
        features = _extract_features(html)

        return {
            "success": True,
            "company_name": company_name,
            "product_description": description,
            "key_features": features,
            "source_url": validated_url,
            "error": None,
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "company_name": None,
            "product_description": None,
            "key_features": [],
            "source_url": validated_url,
            "error": f"Timeout after {REQUEST_TIMEOUT} seconds",
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "company_name": None,
            "product_description": None,
            "key_features": [],
            "source_url": validated_url,
            "error": f"HTTP error: {e.response.status_code}",
        }
    except Exception as e:
        return {
            "success": False,
            "company_name": None,
            "product_description": None,
            "key_features": [],
            "source_url": validated_url,
            "error": f"Fetch failed: {str(e)}",
        }
