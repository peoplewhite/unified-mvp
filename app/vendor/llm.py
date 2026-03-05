"""
LLM Integration - Google Gemini for keyword expansion and relevance scoring
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

import httpx


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.0-flash:generateContent"
)


class VendorLLM:
    """Gemini-powered keyword expansion and vendor relevance scoring"""

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.timeout = 30

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def expand_keywords(
        self, keyword: str, target_countries: List[str]
    ) -> Dict[str, Any]:
        """Expand product keyword into multi-language search terms"""
        if not self.available:
            return self._fallback_expand(keyword, target_countries)

        countries_str = ", ".join(target_countries) if target_countries else "global"
        prompt = (
            f"You are a trade show / supply chain keyword expert.\n"
            f"Product keyword: \"{keyword}\"\n"
            f"Target countries/regions: {countries_str}\n\n"
            f"Generate expanded search keywords for finding suppliers at "
            f"international trade exhibitions. Include:\n"
            f"1. The original keyword in English\n"
            f"2. Translations in languages relevant to target countries "
            f"(German, Japanese, Chinese, Korean, etc.)\n"
            f"3. Related technical terms and synonyms\n"
            f"4. Industry-specific variations\n\n"
            f"Return ONLY a JSON object with this format:\n"
            f'{{"expanded_keywords": ["term1", "term2", ...], '
            f'"languages_covered": ["English", "German", ...]}}\n'
            f"No markdown, no explanation, just the JSON."
        )

        result = await self._call_gemini(prompt)
        if result:
            try:
                data = json.loads(self._extract_json(result))
                return data
            except (json.JSONDecodeError, TypeError):
                pass

        return self._fallback_expand(keyword, target_countries)

    async def score_vendors(
        self, keyword: str, vendors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score vendor relevance using LLM"""
        if not self.available or not vendors:
            return vendors

        batch = vendors[:30]
        vendor_lines = []
        for i, v in enumerate(batch):
            name = v.get("name", "")
            desc = v.get("description", "")[:150]
            products = v.get("products", "")[:100]
            vendor_lines.append(f"{i}: {name} | {products} | {desc}")

        prompt = (
            f"You are a supply chain relevance analyst.\n"
            f"Product keyword: \"{keyword}\"\n\n"
            f"Score each vendor's relevance to this keyword (1-100):\n"
            f"80+ = highly relevant supplier/manufacturer\n"
            f"60-79 = moderately relevant\n"
            f"Below 60 = not relevant\n\n"
            f"Vendors:\n" + "\n".join(vendor_lines) + "\n\n"
            f"Return ONLY a JSON array of objects: "
            f'[{{"index": 0, "score": 85, "reason": "direct manufacturer"}}, ...]\n'
            f"No markdown, no explanation, just the JSON array."
        )

        result = await self._call_gemini(prompt)
        if result:
            try:
                scores = json.loads(self._extract_json(result))
                score_map = {s["index"]: s for s in scores}
                for i, v in enumerate(batch):
                    if i in score_map:
                        v["match_score"] = score_map[i]["score"]
                        if "reason" in score_map[i]:
                            v["ai_reason"] = score_map[i]["reason"]
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

        return vendors

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{GEMINI_API_URL}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.3},
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    return (
                        data["candidates"][0]["content"]["parts"][0]["text"]
                    )
                else:
                    print(f"  Gemini API error: {response.status_code} {response.text[:200]}")
        except Exception as e:
            print(f"  Gemini API failed: {e.__class__.__name__}: {e}")
        return None

    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response (strip markdown fences)"""
        text = text.strip()
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if m:
            return m.group(1).strip()
        for start, end in [("{", "}"), ("[", "]")]:
            i = text.find(start)
            j = text.rfind(end)
            if i != -1 and j != -1 and j > i:
                return text[i:j+1]
        return text

    def _fallback_expand(
        self, keyword: str, target_countries: List[str]
    ) -> Dict[str, Any]:
        """Simple keyword expansion without LLM"""
        keywords = [keyword]
        kw_lower = keyword.lower()

        synonyms = {
            "electronics": ["electronic components", "electronic parts", "Elektronik", "Elektronische Bauteile"],
            "semiconductor": ["IC", "chip", "Halbleiter", "integrated circuit"],
            "sensor": ["Sensor", "sensing", "detector", "Sensortechnik"],
            "machinery": ["machine", "Maschine", "industrial equipment", "Maschinenbau"],
            "textile": ["fabric", "Textil", "garment", "clothing material"],
            "medical device": ["Medizintechnik", "medical equipment", "healthcare device"],
            "connector": ["Steckverbinder", "cable connector", "interconnect"],
            "capacitor": ["Kondensator", "electronic capacitor"],
            "automotive": ["Automobil", "vehicle parts", "car components"],
        }

        for k, syns in synonyms.items():
            if k in kw_lower:
                keywords.extend(syns)
                break

        keywords.append(f"{keyword} supplier")
        keywords.append(f"{keyword} manufacturer")

        return {
            "expanded_keywords": keywords,
            "languages_covered": ["English"],
        }
