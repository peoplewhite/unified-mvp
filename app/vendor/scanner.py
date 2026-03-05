"""
Vendor Scanner - Main orchestrator
Coordinates keyword expansion, exhibition scraping, and AI scoring
"""

from typing import List, Dict, Any

from app.vendor.llm import VendorLLM
from app.vendor.exhibitions import ExhibitionScraper


class VendorScanner:
    """Main vendor search orchestrator"""

    def __init__(self, timeout: int = 15):
        self.llm = VendorLLM()
        self.exhibition_scraper = ExhibitionScraper(timeout=timeout)

    async def search(self, keyword: str, country: str = "") -> List[Dict[str, Any]]:
        """
        Full search pipeline:
        1. LLM keyword expansion
        2. Exhibition scraping
        3. LLM relevance scoring
        4. Sort and return
        """
        print(f"\n=== Vendor Search: '{keyword}' country='{country}' ===")

        # Step 1: Keyword expansion
        target_countries = [country] if country else []
        print("  Step 1: Expanding keywords...")
        expansion = await self.llm.expand_keywords(keyword, target_countries)
        expanded = expansion.get("expanded_keywords", [keyword])
        languages = expansion.get("languages_covered", ["English"])
        print(f"    {len(expanded)} keywords in {len(languages)} languages")

        # Step 2: Search exhibitions
        print("  Step 2: Searching exhibitions...")
        vendors = await self.exhibition_scraper.search_all(
            keyword, expanded, country
        )
        print(f"    Total raw results: {len(vendors)}")

        if not vendors:
            return []

        # Apply country filter if specified
        if country:
            country_lower = country.lower()
            filtered = [
                v for v in vendors
                if country_lower in v.get("country", "").lower()
                or v.get("country", "") == "Global"
            ]
            # Keep all if filter removes too many
            if len(filtered) >= 3:
                vendors = filtered

        # Step 3: AI relevance scoring
        print("  Step 3: AI relevance scoring...")
        vendors = await self.llm.score_vendors(keyword, vendors)

        # Fallback: rule-based scoring for any vendors without LLM scores
        for v in vendors:
            if v.get("match_score", 0) == 0:
                v["match_score"] = self._rule_based_score(v, keyword, country)

        # Step 4: Sort by score, filter low relevance
        vendors.sort(key=lambda x: x["match_score"], reverse=True)
        # Remove vendors below 60 if we have enough above
        high_quality = [v for v in vendors if v["match_score"] >= 60]
        if len(high_quality) >= 10:
            vendors = high_quality

        result = vendors[:100]
        print(f"  Final results: {len(result)} vendors")
        return result

    def _rule_based_score(
        self, vendor: Dict[str, Any], keyword: str, country: str
    ) -> int:
        """Fallback rule-based scoring when LLM is unavailable"""
        score = 70
        name_lower = vendor.get("name", "").lower()
        desc_lower = vendor.get("description", "").lower()
        kw = keyword.lower()

        if kw in name_lower:
            score += 15
        if kw in desc_lower:
            score += 5

        supplier_words = [
            "supplier", "manufacturer", "factory", "producer",
            "exporter", "exhibitor", "GmbH", "Ltd", "Inc", "Corp",
        ]
        for w in supplier_words:
            if w.lower() in desc_lower or w.lower() in name_lower:
                score += 3

        if country:
            vc = vendor.get("country", "").lower()
            if country.lower() in vc or vc in country.lower():
                score += 10

        # Bonus for having real exhibition source
        exhibition = vendor.get("exhibition", "")
        if exhibition and exhibition != "Trade Show News":
            score += 5

        return min(99, score)
