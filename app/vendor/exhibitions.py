"""
Electronica Exhibitor Client
Fetches real exhibitor data from electronica 2024 via sitemap + detail pages
"""

import asyncio
import re
import ssl
from typing import Any

import httpx
from bs4 import BeautifulSoup


SITEMAP_URL = (
    "https://exhibitors.electronica.de"
    "/media/807/tmp/scf/sitemap/xml-sitemap_ex_807_1.xml"
)
AUTOCOMPLETE_URL = (
    "https://exhibitors.electronica.de"
    "/_inc002/_modules/public/ajax_getValuesForSearchField.cfm"
)
DETAIL_BASE = (
    "https://exhibitors.electronica.de"
    "/exhibitor-portal/2024/list-of-exhibitors/exhibitordetails/{slug}/"
)
PROJECT_ID = "807"


def _name_to_slug(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    return re.sub(r"-+", "-", slug)


def _is_company(name: str) -> bool:
    """Filter out product category names, keep company names."""
    company_suffixes = [
        "gmbh", "ltd", "inc", "co.", "corp", "ag", "llc", "s.a.", "bv",
        "nv", "oy", "ab", "as", "srl", "spa", "sarl", "kft", "plc", "pty",
        "co.,", "technology", "technologies", "electronics", "semiconductor",
        "solutions", "systems", "group", "international",
    ]
    category_patterns = [
        r"^[a-z]",                      # starts lowercase
        r"\bfor\b|\bwith\b|\band\b",     # generic descriptions
        r"^(components?|devices?|sensors?|modules?|circuits?)$",
    ]
    name_lower = name.lower()
    if any(s in name_lower for s in company_suffixes):
        return True
    for p in category_patterns:
        if re.search(p, name_lower):
            return False
    # Short single-word lowercase-ish names are likely categories
    if len(name.split()) <= 2 and name[0].islower():
        return False
    return True


class ElectronicaClient:
    """Fetches electronica 2024 exhibitor data using sitemap + detail pages."""

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        self._sitemap_cache: dict[str, str] = {}  # slug → exhibitor_id
        self._ssl_ctx = ssl.create_default_context()
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._headers,
            follow_redirects=True,
            verify=self._ssl_ctx,
        )

    async def load_sitemap(self) -> dict[str, str]:
        """Load all exhibitor slugs and IDs from the sitemap. Cached."""
        if self._sitemap_cache:
            return self._sitemap_cache

        async with self._make_client() as client:
            response = await client.get(SITEMAP_URL)
            response.raise_for_status()

        slugs: dict[str, str] = {}
        for m in re.finditer(
            r"ausstellerdetails/([^/]+)/\?elb=807\.1100\.(\d+)", response.text
        ):
            slugs[m.group(1)] = m.group(2)

        self._sitemap_cache = slugs
        print(f"  Sitemap loaded: {len(slugs)} exhibitors")
        return slugs

    async def autocomplete(
        self, keyword: str, client: httpx.AsyncClient
    ) -> list[str]:
        """Return company names matching the keyword from autocomplete API."""
        response = await client.get(
            AUTOCOMPLETE_URL,
            params={"q": keyword, "p_id": PROJECT_ID, "lng": "2", "maxResults": "30"},
        )
        if response.status_code != 200:
            return []
        names = [
            line.split("|")[0].strip()
            for line in response.text.strip().split("\n")
            if "|" in line
        ]
        return [n for n in names if _is_company(n)]

    async def fetch_detail(
        self, slug: str, exhibitor_id: str, client: httpx.AsyncClient
    ) -> dict[str, Any] | None:
        """Fetch and parse a single exhibitor's detail page."""
        url = DETAIL_BASE.format(slug=slug)
        response = await client.get(
            url, params={"elb": f"807.1100.{exhibitor_id}.1.111", "uls": "2"}
        )
        if response.status_code != 200:
            return None

        # Verify it's actually an exhibitor page (not a redirect to homepage)
        if "list-of-exhibitors" not in response.url.path and len(response.text) > 200_000:
            return None

        return self._parse_detail(response.text, slug)

    def _parse_detail(self, html: str, slug: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        lines = [
            l.strip()
            for l in soup.get_text(separator="\n").split("\n")
            if l.strip() and len(l.strip()) > 1
        ]

        # The page structure (after navigation) is:
        #   CompanyName → Booth → ShortDesc → "Company profile" →
        #   FullDesc → "Application areas" → areas → "Products and services" →
        #   products → "Contact" → address / phone / email / website
        # Find where navigation ends and exhibitor content begins
        nav_sentinels = ("Careers", "Solutions", "Press")
        start = 0
        for sentinel in nav_sentinels:
            try:
                start = next(i for i, l in enumerate(lines) if l == sentinel) + 1
                break
            except StopIteration:
                continue

        content = lines[start:]

        name = self._extract_name(soup)
        booth = next((l for l in content if re.match(r"^[A-Z]\d+\.\d+$", l)), "")

        # Everything is parsed relative to section headers
        description = ""
        application_areas: list[str] = []
        products: list[str] = []
        address = phone = email = website = ""

        section = "header"
        for line in content:
            ll = line.lower()

            # Section transitions
            if ll == "company profile":
                section = "profile"
                continue
            elif ll == "application areas":
                section = "areas"
                continue
            elif ll in ("products and services", "products/services"):
                section = "products"
                continue
            elif ll == "contact":
                section = "contact"
                continue

            if section == "header" and not booth:
                pass  # still in booth/short-desc territory
            elif section == "profile" and not description:
                if len(line) > 40 and not line.startswith("http"):
                    description = line
            elif section == "areas":
                if not re.match(r"^\d+\s+exhibitors?$", ll) and 4 < len(line) < 100:
                    application_areas.append(line)
                    if len(application_areas) >= 5:
                        section = "areas_done"
            elif section == "products":
                if not re.match(r"^\d+\s+exhibitors?$", ll) and 3 < len(line) < 80:
                    if line not in products:
                        products.append(line)
                    if len(products) >= 8:
                        section = "products_done"
            elif section == "contact":
                if not email and re.match(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}$", line):
                    email = line
                elif not phone and re.match(r"^\+[\d\s\-().]{7,20}$", line):
                    phone = line
                elif not website and re.match(r"^www\.", line):
                    website = "https://" + line
                elif not address and re.search(r"\b\d{4,6}\b", line) and len(line) > 15:
                    address = line

        return {
            "name": name,
            "booth": booth,
            "description": description,
            "address": address,
            "phone": phone,
            "email": email,
            "website": website,
            "products": products,
            "application_areas": application_areas,
            "exhibition": "electronica 2024",
            "slug": slug,
            "match_score": 0,
        }

    def _extract_name(self, soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(strip=True)
            return re.sub(r"\s+at\s+electronica\s+\d{4}.*$", "", text, flags=re.I).strip()
        return ""

    async def search(
        self, keyword: str, expanded_keywords: list[str]
    ) -> list[dict[str, Any]]:
        """
        Full search:
        1. Load sitemap (cached after first call)
        2. Autocomplete for each keyword variant → company names
        3. Match names to sitemap slugs → get exhibitor IDs
        4. Fetch detail pages concurrently
        """
        async with self._make_client() as client:
            sitemap = await self.load_sitemap()

            # Collect candidate company names from all keyword variants
            all_names: set[str] = set()
            search_terms = [keyword] + expanded_keywords[:4]
            for term in search_terms:
                names = await self.autocomplete(term, client)
                all_names.update(names)
                await asyncio.sleep(0.5)

            print(f"  Autocomplete: {len(all_names)} unique company candidates")

            # Match to sitemap to get IDs
            candidates: list[tuple[str, str]] = []  # (slug, id)
            for name in all_names:
                slug = _name_to_slug(name)
                if slug in sitemap:
                    candidates.append((slug, sitemap[slug]))

            print(f"  Sitemap matched: {len(candidates)} exhibitors")

            if not candidates:
                return []

            # Fetch detail pages concurrently (max 5 at a time)
            semaphore = asyncio.Semaphore(5)

            async def fetch_with_limit(slug: str, eid: str) -> dict[str, Any] | None:
                async with semaphore:
                    result = await self.fetch_detail(slug, eid, client)
                    await asyncio.sleep(0.3)
                    return result

            tasks = [fetch_with_limit(slug, eid) for slug, eid in candidates]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        exhibitors = [r for r in results if isinstance(r, dict) and r.get("name")]
        print(f"  Detail pages fetched: {len(exhibitors)}")
        return exhibitors
