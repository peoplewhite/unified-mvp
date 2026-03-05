"""
Credit Analyzer Module - Analyzes SME credit risk
"""

import random
from typing import Dict, Any
from datetime import datetime


class CreditAnalyzer:
    """Analyzes company credit risk and financial health"""
    
    # Mock data templates for different risk levels
    RISK_PROFILES = {
        "low": {
            "credit_score": random.randint(750, 850),
            "risk_level": "Low Risk",
            "risk_color": "green",
            "payment_history": "Excellent",
            "financial_stability": "Strong",
            "recommendation": "Approved - proceed with standard terms"
        },
        "medium": {
            "credit_score": random.randint(650, 749),
            "risk_level": "Medium Risk",
            "risk_color": "yellow",
            "payment_history": "Good",
            "financial_stability": "Moderate",
            "recommendation": "Approved - consider shorter payment terms"
        },
        "high": {
            "credit_score": random.randint(500, 649),
            "risk_level": "High Risk",
            "risk_color": "red",
            "payment_history": "Fair",
            "financial_stability": "Weak",
            "recommendation": "Conditional - require advance payment or collateral"
        }
    }
    
    async def analyze(self, company_name: str) -> Dict[str, Any]:
        """
        Analyze company credit risk
        
        In mock mode, generates realistic-looking credit report data
        """
        # Seed random based on company name for consistent results
        random.seed(hash(company_name) % 10000)
        
        # Determine risk profile based on company name hash
        risk_key = random.choice(["low", "medium", "high"])
        profile = self.RISK_PROFILES[risk_key].copy()
        
        # Generate company details
        year_established = random.randint(1980, 2020)
        years_in_business = datetime.now().year - year_established
        
        # Financial metrics
        annual_revenue = round(random.uniform(1, 100), 2)  # in millions
        employees = random.randint(10, 5000)
        
        # Credit metrics
        credit_limit = round(annual_revenue * random.uniform(0.1, 0.3), 2)
        existing_debt = round(annual_revenue * random.uniform(0.05, 0.4), 2)
        debt_ratio = round(existing_debt / annual_revenue * 100, 1)
        
        # Build report
        report = {
            "company_name": company_name,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "company_info": {
                "year_established": year_established,
                "years_in_business": years_in_business,
                "annual_revenue_millions": annual_revenue,
                "employee_count": employees,
                "industry": random.choice([
                    "Manufacturing", "Technology", "Retail", 
                    "Healthcare", "Construction", "Finance"
                ]),
                "business_type": random.choice([
                    "Corporation", "LLC", "Partnership", "Sole Proprietorship"
                ])
            },
            "credit_assessment": {
                "credit_score": profile["credit_score"],
                "risk_level": profile["risk_level"],
                "risk_color": profile["risk_color"],
                "credit_limit_millions": credit_limit,
                "recommended_credit_period": random.choice(["30 days", "60 days", "90 days"])
            },
            "financial_health": {
                "existing_debt_millions": existing_debt,
                "debt_to_revenue_ratio": f"{debt_ratio}%",
                "financial_stability": profile["financial_stability"],
                "payment_history": profile["payment_history"],
                "cash_flow": random.choice(["Positive", "Stable", "Fluctuating"]),
                "profitability": random.choice(["Profitable", "Break-even", "Growing"])
            },
            "risk_factors": self._generate_risk_factors(risk_key),
            "recommendation": profile["recommendation"],
            "confidence_score": random.randint(75, 95)
        }
        
        return report
    
    def _generate_risk_factors(self, risk_level: str) -> list:
        """Generate relevant risk factors based on risk level"""
        all_factors = {
            "low": [
                "Strong financial track record",
                "Consistent payment history",
                "Diversified customer base",
                "Stable management team"
            ],
            "medium": [
                "Moderate leverage levels",
                "Some seasonal fluctuations",
                "Industry competition pressure",
                "Adequate cash reserves"
            ],
            "high": [
                "Higher than average leverage",
                "Limited credit history",
                "Concentrated customer base",
                "Market volatility exposure"
            ]
        }
        
        factors = all_factors.get(risk_level, all_factors["medium"])
        # Return 2-3 random factors
        return random.sample(factors, min(3, len(factors)))