"""
Synthetic HR leave database (SQLite) used by the HR Leave Agent.

One table, keyed by employee ID:

    leave_balance(employee_id PRIMARY KEY, name, department,
                  annual_leave, casual_leave, sick_leave)   ← days remaining

The five employees are made up. To (re)create the database and print it:

    uv run python -m travel_planner.data.leave_db
"""

import sqlite3
from contextlib import closing
from typing import Dict, List, Optional

from travel_planner import config

# (employee_id, name, department, annual_leave, casual_leave, sick_leave)
SAMPLE_EMPLOYEES = [
    ("E1001", "Asha Verma",  "Engineering",     18, 6, 10),
    ("E1002", "Rahul Mehta", "Finance",          4, 2,  8),
    ("E1003", "Priya Nair",  "Marketing",       12, 5,  7),
    ("E1004", "Karan Singh", "Sales",            0, 3,  5),
    ("E1005", "Neha Kapoor", "Human Resources", 25, 8, 12),
]


def _connect() -> sqlite3.Connection:
    """Open the database; rows can be read like dicts."""
    connection = sqlite3.connect(config.LEAVE_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_leave_db() -> None:
    """Create the table and insert the sample employees. Safe to run again."""
    with closing(_connect()) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leave_balance (
                employee_id  TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                department   TEXT NOT NULL,
                annual_leave INTEGER NOT NULL,
                casual_leave INTEGER NOT NULL,
                sick_leave   INTEGER NOT NULL
            )
        """)
        connection.executemany(
            "INSERT OR REPLACE INTO leave_balance VALUES (?, ?, ?, ?, ?, ?)", SAMPLE_EMPLOYEES
        )
        connection.commit()


def get_leave_balance(employee_id: str) -> Optional[Dict]:
    """Return one employee's leave record, or None if the ID is not in the database."""
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT * FROM leave_balance WHERE employee_id = ?", (employee_id.strip().upper(),)
        ).fetchone()
    return dict(row) if row else None


def get_all_employees() -> List[Dict]:
    """Return every employee's leave record, ordered by ID."""
    with closing(_connect()) as connection:
        rows = connection.execute("SELECT * FROM leave_balance ORDER BY employee_id").fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    create_leave_db()
    print(f"Leave database: {config.LEAVE_DB_PATH}\n")
    for employee in get_all_employees():
        print(employee)
