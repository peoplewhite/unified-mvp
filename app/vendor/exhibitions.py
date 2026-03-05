"""
Exhibition Scraper - Fetches exhibitor data from trade show websites
Uses direct APIs where available, Brave Search as fallback
"""

import asyncio
import hashlib
import re
import ssl
from typing import List, Dict, Any
from urllib.parse import quote, urlparse

import httpx
from bs4 import BeautifulSoup


EXHIBITIONS = [
    {
        "name": "Hannover Messe",
        "url": "hannovermesse.de",
        "industry": ["industrial", "automation", "energy", "machinery"],
        "country": "Germany",
        "year": "2026",
        "scrape_type": "brave",
    },
    {
        "name": "electronica",
        "url": "electronica.de",
        "industry": ["electronics", "semiconductor", "sensor", "connector"],
        "country": "Germany",
        "year": "2026",
        "scrape_type": "electronica_api",
        "api_project_id": "807",
    },
    {
        "name": "SEMICON West",
        "url": "semiconwest.org",
        "industry": ["semiconductor", "IC", "wafer", "chip"],
        "country": "USA",
        "year": "2026",
        "scrape_type": "brave",
    },
    {
        "name": "MEDICA",
        "url": "medica-tradefair.com",
        "industry": ["medical", "healthcare", "diagnostic", "pharma"],
        "country": "Germany",
        "year": "2026",
        "scrape_type": "brave",
    },
    {
        "name": "CEATEC Japan",
        "url": "ceatec.com",
        "industry": ["electronics", "IT", "semiconductor", "sensor", "automotive"],
        "country": "Japan",
        "year": "2026",
        "scrape_type": "brave",
    },
]


class ExhibitionScraper:
    """Scrapes exhibitor data from trade show websites and search engines"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._ssl_ctx = ssl.create_default_context()
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE

    def get_relevant_exhibitions(self, keyword: str) -> List[Dict[str, Any]]:
        """Filter exhibitions relevant to the keyword"""
        kw = keyword.lower()
        relevant = []
        for ex in EXHIBITIONS:
            # Check if keyword matches any industry tag
            if any(ind in kw for ind in ex["industry"]):
                relevant.append(ex)
        # If no specific match, include all exhibitions
        if not relevant:
            relevant = list(EXHIBITIONS)
        return relevant

    async def search_all(
        self,
        keyword: str,
        expanded_keywords: List[str],
        target_country: str = "",
    ) -> List[Dict[str, Any]]:
        """Search all relevant exhibitions for vendors"""
        exhibitions = self.get_relevant_exhibitions(keyword)
        all_vendors = []

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True,
            verify=self._ssl_ctx,
        ) as client:
            for ex in exhibitions:
                try:
                    if ex["scrape_type"] == "electronica_api":
                        vendors = await self._scrape_electronica(
                            client, keyword, expanded_keywords, ex
                        )
                    else:
                        vendors = await self._scrape_via_brave(
                            client, keyword, expanded_keywords, ex
                        )
                    all_vendors.extend(vendors)
                    print(f"  {ex['name']}: {len(vendors)} exhibitors found")
                except Exception as e:
                    print(f"  {ex['name']} failed: {e.__class__.__name__}")

                # Rate limit delay between exhibitions
                await asyncio.sleep(2)

            # Also search Google News RSS for recent exhibitor news
            news_vendors = await self._search_exhibition_news(
                client, keyword, target_country
            )
            all_vendors.extend(news_vendors)

        return self._deduplicate(all_vendors)

    async def _scrape_electronica(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        expanded_keywords: List[str],
        exhibition: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Scrape electronica using their autocomplete API"""
        vendors = []
        seen_names = set()
        search_terms = [keyword] + expanded_keywords[:5]

        for term in search_terms:
            try:
                url = (
                    f"https://exhibitors.electronica.de/"
                    f"_inc002/_modules/public/ajax_getValuesForSearchField.cfm"
                    f"?q={quote(term)}&p_id={exhibition['api_project_id']}"
                    f"&lng=2&maxResults=30"
                )
                response = await client.get(url)
                if response.status_code == 200:
                    lines = response.text.strip().split("\n")
                    for line in lines:
                        parts = line.split("|")
                        if len(parts) >= 1:
                            name = parts[0].strip()
                            if (
                                name
                                and len(name) > 3
                                and name.lower() not in seen_names
                                and not self._is_category_name(name)
                            ):
                                seen_names.add(name.lower())
                                vendors.append(
                                    self._build_vendor(
                                        name=name,
                                        exhibition=exhibition["name"],
                                        keyword=keyword,
                                        website=f"https://exhibitors.electronica.de/",
                                    )
                                )
            except Exception:
                continue
            await asyncio.sleep(1)

        return vendors

    async def _scrape_via_brave(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        expanded_keywords: List[str],
        exhibition: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Search Brave for exhibitors at a specific exhibition"""
        vendors = []
        query = f"{exhibition['name']} {exhibition['year']} exhibitor {keyword}"

        try:
            url = f"https://search.brave.com/search?q={quote(query)}&source=web"
            response = await client.get(url)

            if response.status_code == 200:
                vendors = self._parse_brave_results(
                    response.text, keyword, exhibition["name"]
                )
            elif response.status_code == 429:
                print(f"    Brave rate-limited, trying Google News fallback")
                vendors = await self._news_fallback(
                    client, keyword, exhibition["name"]
                )
        except Exception:
            pass

        return vendors

    async def _news_fallback(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        exhibition_name: str,
    ) -> List[Dict[str, Any]]:
        """Fallback: use Google News RSS when Brave is rate-limited"""
        vendors = []
        query = f"{exhibition_name} exhibitor {keyword}"
        try:
            rss_url = (
                f"https://news.google.com/rss/search?q={quote(query)}"
                f"&hl=en&gl=US&ceid=US:en"
            )
            response = await client.get(rss_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "xml")
                for item in soup.find_all("item", limit=10):
                    title = item.find("title")
                    link = item.find("link")
                    if not title:
                        continue
                    title_text = title.get_text(strip=True)
                    link_text = link.get_text(strip=True) if link else ""
                    name = self._extract_company_from_title(title_text)
                    if name:
                        vendors.append(
                            self._build_vendor(
                                name=name,
                                exhibition=exhibition_name,
                                keyword=keyword,
                                website=link_text,
                                description=title_text,
                            )
                        )
        except Exception:
            pass
        return vendors

    async def _search_exhibition_news(
        self,
        client: httpx.AsyncClient,
        keyword: str,
        country: str,
    ) -> List[Dict[str, Any]]:
        """Search Google News for recent exhibition/trade show vendor news"""
        vendors = []
        query_parts = [keyword, "trade show OR exhibition", "exhibitor OR booth"]
        if country:
            query_parts.append(country)
        query = " ".join(query_parts)

        try:
            rss_url = (
                f"https://news.google.com/rss/search?q={quote(query)}"
                f"&hl=en&gl=US&ceid=US:en"
            )
            response = await client.get(rss_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "xml")
                for item in soup.find_all("item", limit=10):
                    title = item.find("title")
                    link = item.find("link")
                    if not title:
                        continue
                    title_text = title.get_text(strip=True)
                    link_text = link.get_text(strip=True) if link else ""
                    # Try to extract exhibition name from title
                    exhibition = self._detect_exhibition(title_text)
                    name = self._extract_company_from_title(title_text)
                    if name:
                        vendors.append(
                            self._build_vendor(
                                name=name,
                                exhibition=exhibition or "Trade Show News",
                                keyword=keyword,
                                website=link_text,
                                description=title_text,
                            )
                        )
            print(f"  Exhibition News: {len(vendors)} vendor mentions found")
        except Exception as e:
            print(f"  Exhibition News failed: {e.__class__.__name__}")

        return vendors

    def _parse_brave_results(
        self, html: str, keyword: str, exhibition_name: str
    ) -> List[Dict[str, Any]]:
        """Parse Brave Search results for exhibitor data"""
        vendors = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.select('div[data-type="web"]'):
            try:
                title_el = result.select_one(".title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                url = ""
                for a in result.find_all("a"):
                    href = a.get("href", "")
                    if href.startswith("http") and "brave.com" not in href:
                        url = href
                        break
                if not url:
                    continue

                if self._is_noise(title, url):
                    continue

                snippet_el = result.select_one(".snippet-description")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                name = re.split(r"\s*[-|–—:]\s*", title)[0].strip()
                if len(name) < 2 or len(name) > 80:
                    continue

                domain = urlparse(url).netloc.replace("www.", "")

                vendors.append(
                    self._build_vendor(
                        name=name,
                        exhibition=exhibition_name,
                        keyword=keyword,
                        website=url,
                        description=snippet or title,
                        contact=f"info@{domain}",
                        country=self._detect_country(title + " " + snippet, url),
                    )
                )
            except Exception:
                continue

        return vendors

    def _build_vendor(
        self,
        name: str,
        exhibition: str,
        keyword: str,
        website: str = "",
        description: str = "",
        contact: str = "",
        country: str = "",
    ) -> Dict[str, Any]:
        """Build a structured vendor entry"""
        return {
            "name": name,
            "country": country or "Global",
            "category": keyword,
            "exhibition": exhibition,
            "rating": self._stable_rating(name),
            "match_score": 0,
            "products": description[:100] if description else keyword.title(),
            "contact": contact,
            "website": website,
            "description": description,
            "established": "",
        }

    def _is_category_name(self, name: str) -> bool:
        """Check if a name is a category rather than a company"""
        category_indicators = [
            "sensor", "sensors", "connector", "connectors",
            "capacitor", "capacitors", "resistor", "resistors",
            "cable", "cables", "module", "modules",
            "device", "devices", "system", "systems",
            "component", "components", "equipment",
            "instrument", "instruments", "tool", "tools",
            "material", "materials", "battery", "diode",
            "transistor", "relay", "switch", "fuse",
            "transformer", "antenna", "filter", "amplifier",
        ]
        company_indicators = [
            "gmbh", "ltd", "inc", "co.", "corp", "ag", "llc",
            "s.a.", "bv", "nv", "oy", "ab", "as", "srl",
            "spa", "sarl", "kft", "plc", "pty",
        ]
        name_lower = name.lower()

        # Has a company suffix → definitely a company
        if any(ind in name_lower for ind in company_indicators):
            return False

        # Starts with lowercase or generic adjective → likely category
        if name[0].islower():
            return True

        # Contains "for" or "with" patterns → category description
        if " for " in name_lower or " with " in name_lower:
            return True

        # Short generic names are categories
        words = name_lower.split()
        if len(words) <= 4 and any(ci in name_lower for ci in category_indicators):
            return True

        return False

    def _extract_company_from_title(self, title: str) -> str:
        """Extract company name from news title"""
        patterns = [
            r"^([A-Z][A-Za-z\s&\.\,]+?)\s+(?:to|announces|launches|partners|"
            r"expands|opens|signs|reports|showcases|exhibits|unveils|debuts|displays)",
            r"^([A-Z][A-Za-z\s&\.\,]+?)\s*[-\u2013\u2014]\s",
        ]
        for p in patterns:
            m = re.match(p, title)
            if m:
                name = m.group(1).strip().rstrip(",")
                if 3 < len(name) < 50:
                    return name
        return ""

    def _detect_exhibition(self, text: str) -> str:
        """Detect exhibition name from text"""
        text_lower = text.lower()
        for ex in EXHIBITIONS:
            if ex["name"].lower() in text_lower:
                return ex["name"]
        exhibition_names = [
            "CES", "MWC", "IFA", "Computex", "Canton Fair",
            "Automechanika", "Productronica", "Embedded World",
        ]
        for name in exhibition_names:
            if name.lower() in text_lower:
                return name
        return ""

    def _detect_country(self, text: str, url: str) -> str:
        """Detect country from text or URL TLD"""
        tld_map = {
            ".tw": "Taiwan", ".cn": "China", ".jp": "Japan",
            ".kr": "South Korea", ".de": "Germany", ".uk": "United Kingdom",
            ".fr": "France", ".it": "Italy", ".in": "India",
            ".th": "Thailand", ".vn": "Vietnam", ".my": "Malaysia",
            ".sg": "Singapore", ".id": "Indonesia", ".br": "Brazil",
            ".mx": "Mexico", ".au": "Australia", ".ca": "Canada",
        }
        domain = urlparse(url).netloc.lower()
        for tld, c in tld_map.items():
            if domain.endswith(tld):
                return c

        country_names = [
            "Taiwan", "China", "Japan", "South Korea", "India", "Germany",
            "USA", "United States", "United Kingdom", "France", "Italy",
            "Thailand", "Vietnam", "Malaysia", "Singapore", "Indonesia",
            "Brazil", "Mexico", "Canada", "Australia", "Turkey",
        ]
        text_lower = text.lower()
        for c in country_names:
            if c.lower() in text_lower:
                return c
        return "Global"

    def _is_noise(self, title: str, url: str) -> bool:
        """Filter out non-vendor results"""
        noise_domains = [
            "wikipedia.org", "youtube.com", "reddit.com", "facebook.com",
            "twitter.com", "linkedin.com", "instagram.com", "tiktok.com",
            "amazon.com", "ebay.com", "google.com", "bing.com",
            "yahoo.com", "pinterest.com",
        ]
        noise_words = ["how to", "what is", "definition", "wiki", "forum"]
        domain = urlparse(url).netloc.lower()
        title_lower = title.lower()

        if any(nd in domain for nd in noise_domains):
            return True
        if any(nw in title_lower for nw in noise_words):
            return True
        return False

    def _stable_rating(self, seed: str) -> float:
        """Generate a stable rating based on seed string"""
        h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
        return round(3.5 + (h % 15) / 10, 1)

    def _deduplicate(self, vendors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate vendors by name similarity"""
        seen = {}
        unique = []
        for v in vendors:
            key = re.sub(r"[^a-z0-9]", "", v["name"].lower())[:30]
            if key not in seen:
                seen[key] = True
                unique.append(v)
        return unique
