"""
Leave balance lookup tool for the HR Leave Agent.

Reads the synthetic SQLite database in travel_planner/data/hr_leave.db.
"""

from langchain_core.tools import tool

from travel_planner import config
from travel_planner.data.leave_db import get_all_employees, get_leave_balance


@tool
def lookup_leave_balance(employee_id: str) -> str:
    """Look up an employee's remaining leave (annual, casual, sick) by employee ID, e.g. E1001."""
    record = get_leave_balance(employee_id)
    if record is None:
        valid_ids = ", ".join(employee["employee_id"] for employee in get_all_employees())
        return f"{config.EMPLOYEE_NOT_FOUND} '{employee_id}'. Valid employee IDs: {valid_ids}."

    return (
        f"Employee ID: {record['employee_id']} | Name: {record['name']} | "
        f"Department: {record['department']} | "
        f"Annual leave: {record['annual_leave']} days | "
        f"Casual leave: {record['casual_leave']} days | "
        f"Sick leave: {record['sick_leave']} days"
    )
