"""
Vendor Scanner - Orchestrates keyword expansion, exhibitor search, and AI scoring
"""

from typing import Any

from app.vendor.llm import VendorLLM
from app.vendor.exhibitions import ElectronicaClient


class VendorScanner:
    def __init__(self, timeout: int = 15) -> None:
        self.llm = VendorLLM()
        self.electronica = ElectronicaClient(timeout=timeout)

    async def search(self, keyword: str, country: str = "") -> list[dict[str, Any]]:
        print(f"\n=== Exhibitor Search: '{keyword}' ===")

        # Step 1: Expand keyword to multilingual variants
        print("  Step 1: Expanding keywords...")
        expansion = await self.llm.expand_keywords(keyword, [country] if country else [])
        expanded = expansion.get("expanded_keywords", [keyword])
        print(f"    {len(expanded)} variants")

        # Step 2: Search electronica exhibitors
        print("  Step 2: Searching electronica 2024...")
        exhibitors = await self.electronica.search(keyword, expanded)

        if not exhibitors:
            return []

        # Step 3: AI relevance scoring
        print("  Step 3: Scoring relevance...")
        exhibitors = await self.llm.score_vendors(keyword, exhibitors)

        # Fallback rule-based score for any unscored entries
        for ex in exhibitors:
            if ex.get("match_score", 0) == 0:
                ex["match_score"] = self._rule_score(ex, keyword)

        # Step 4: Apply country filter if specified
        if country:
            country_lower = country.lower()
            filtered = [
                ex for ex in exhibitors
                if country_lower in ex.get("address", "").lower()
                or country_lower in ex.get("name", "").lower()
            ]
            if len(filtered) >= 3:
                exhibitors = filtered

        exhibitors.sort(key=lambda x: x["match_score"], reverse=True)
        result = [ex for ex in exhibitors if ex["match_score"] >= 50][:50]
        print(f"  Final results: {len(result)}")
        return result

    def _rule_score(self, ex: dict[str, Any], keyword: str) -> int:
        score = 65
        kw = keyword.lower()
        name_lower = ex.get("name", "").lower()
        desc_lower = ex.get("description", "").lower()
        products_text = " ".join(ex.get("products", [])).lower()

        if kw in name_lower:
            score += 20
        if kw in desc_lower or kw in products_text:
            score += 10
        if ex.get("email"):
            score += 5
        if ex.get("website"):
            score += 5

        return min(95, score)
