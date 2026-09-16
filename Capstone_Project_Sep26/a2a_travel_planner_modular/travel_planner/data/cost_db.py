"""
Offline travel cost table used by the Budget Estimator Agent.

Values are mid-range daily costs in USD per person:
    hotel, food, transport, activities
plus the local currency code and an FX rate (1 USD = fx local units).
Cities not listed fall back to the "default" row (a global average).
"""

from typing import Dict

COST_DB: Dict[str, Dict] = {
    "paris":     {"hotel": 150, "food": 60, "transport": 20, "activities": 40, "currency": "EUR", "fx": 0.92},
    "tokyo":     {"hotel": 120, "food": 50, "transport": 25, "activities": 35, "currency": "JPY", "fx": 150},
    "new york":  {"hotel": 220, "food": 80, "transport": 15, "activities": 55, "currency": "USD", "fx": 1.0},
    "london":    {"hotel": 180, "food": 65, "transport": 20, "activities": 45, "currency": "GBP", "fx": 0.79},
    "bali":      {"hotel": 60,  "food": 25, "transport": 12, "activities": 25, "currency": "IDR", "fx": 15600},
    "dubai":     {"hotel": 160, "food": 70, "transport": 18, "activities": 50, "currency": "AED", "fx": 3.67},
    "singapore": {"hotel": 140, "food": 55, "transport": 20, "activities": 40, "currency": "SGD", "fx": 1.34},
    "rome":      {"hotel": 130, "food": 55, "transport": 15, "activities": 35, "currency": "EUR", "fx": 0.92},
    "barcelona": {"hotel": 120, "food": 50, "transport": 15, "activities": 35, "currency": "EUR", "fx": 0.92},
    "amsterdam": {"hotel": 145, "food": 60, "transport": 18, "activities": 40, "currency": "EUR", "fx": 0.92},
    "default":   {"hotel": 100, "food": 45, "transport": 18, "activities": 30, "currency": "USD", "fx": 1.0},
}
