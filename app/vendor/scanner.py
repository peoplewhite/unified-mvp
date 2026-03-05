"""
Vendor Scanner Module - Searches for global vendors/suppliers
"""

import random
from typing import List, Dict, Any


class VendorScanner:
    """Scans for vendors based on keyword and country"""
    
    # Mock data for demonstration
    MOCK_VENDORS = {
        "electronics": [
            {"name": "TechGlobal Solutions", "country": "Taiwan", "rating": 4.8, "products": "Semiconductors, PCBs"},
            {"name": "Silicon Valley Electronics", "country": "USA", "rating": 4.5, "products": "Microchips, Sensors"},
            {"name": "Shenzhen Tech Hub", "country": "China", "rating": 4.2, "products": "Consumer Electronics"},
            {"name": "Seoul Semiconductor", "country": "South Korea", "rating": 4.7, "products": "LED, Displays"},
            {"name": "Tokyo Components Ltd", "country": "Japan", "rating": 4.9, "products": "Precision Components"},
        ],
        "textile": [
            {"name": "Mumbai Textiles Co", "country": "India", "rating": 4.3, "products": "Cotton Fabrics"},
            {"name": "Guangzhou Garments", "country": "China", "rating": 4.1, "products": "Apparel Manufacturing"},
            {"name": "Bangkok Silk Works", "country": "Thailand", "rating": 4.6, "products": "Silk Products"},
            {"name": "Dhaka Weaving Mills", "country": "Bangladesh", "rating": 4.0, "products": "Woven Fabrics"},
            {"name": "Vietnam Fabric Plus", "country": "Vietnam", "rating": 4.4, "products": "Synthetic Fabrics"},
        ],
        "machinery": [
            {"name": "German Engineering GmbH", "country": "Germany", "rating": 4.9, "products": "Industrial Machinery"},
            {"name": "Milan Machine Works", "country": "Italy", "rating": 4.5, "products": "Precision Tools"},
            {"name": "Shanghai Heavy Industry", "country": "China", "rating": 4.2, "products": "Construction Equipment"},
            {"name": "Detroit Manufacturing", "country": "USA", "rating": 4.4, "products": "Automotive Parts"},
            {"name": "Tokyo Robotics", "country": "Japan", "rating": 4.8, "products": "Automation Systems"},
        ],
    }
    
    async def search(self, keyword: str, country: str = "") -> List[Dict[str, Any]]:
        """
        Search for vendors by keyword and optional country filter
        
        In mock mode, returns predefined vendor data
        """
        # Normalize keyword
        keyword_lower = keyword.lower()
        
        # Find matching category
        results = []
        for category, vendors in self.MOCK_VENDORS.items():
            if keyword_lower in category or category in keyword_lower:
                for vendor in vendors:
                    # Filter by country if specified
                    if country and country.lower() not in vendor["country"].lower():
                        continue
                    
                    # Add metadata
                    vendor_copy = vendor.copy()
                    vendor_copy["category"] = category
                    vendor_copy["match_score"] = random.randint(85, 98)
                    vendor_copy["contact"] = f"contact@{vendor['name'].lower().replace(' ', '')}.com"
                    vendor_copy["established"] = random.randint(1990, 2020)
                    results.append(vendor_copy)
        
        # If no exact category match, return mixed results
        if not results:
            all_vendors = []
            for category, vendors in self.MOCK_VENDORS.items():
                for vendor in vendors:
                    if country and country.lower() not in vendor["country"].lower():
                        continue
                    vendor_copy = vendor.copy()
                    vendor_copy["category"] = category
                    vendor_copy["match_score"] = random.randint(70, 85)
                    vendor_copy["contact"] = f"contact@{vendor['name'].lower().replace(' ', '')}.com"
                    vendor_copy["established"] = random.randint(1990, 2020)
                    all_vendors.append(vendor_copy)
            results = all_vendors[:8]  # Limit to 8 results
        
        # Sort by rating
        results.sort(key=lambda x: x["rating"], reverse=True)
        
        return results