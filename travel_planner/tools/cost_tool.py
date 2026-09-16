"""
Travel cost lookup tool for the Budget Estimator Agent.

Reads the offline COST_DB table — no network access needed.
"""

from langchain_core.tools import tool

from travel_planner.data.cost_db import COST_DB


@tool
def lookup_travel_costs(destination: str) -> str:
    """Look up mid-range daily travel cost estimates for a destination."""
    key = destination.lower().strip()
    found = key in COST_DB
    costs = COST_DB[key] if found else COST_DB["default"]
    daily = costs["hotel"] + costs["food"] + costs["transport"] + costs["activities"]
    note = "(exact city data)" if found else "(global average — city not in database)"
    return (
        f"Destination: {destination} {note} | "
        f"Hotel: ${costs['hotel']}/day | Food: ${costs['food']}/day | "
        f"Transport: ${costs['transport']}/day | Activities: ${costs['activities']}/day | "
        f"Daily total: ${daily} | Local currency: {costs['currency']} | "
        f"FX: 1 USD = {costs['fx']} {costs['currency']}"
    )
