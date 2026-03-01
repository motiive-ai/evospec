"""Fitness Function: Order Integrity (INV-001, INV-005)

Guards:
  INV-001: Every Order must have at least one LineItem
  INV-005: Order total_amount must equal sum of line item subtotals

This is an example fitness function. In a real project, this would
run against your actual database and API.
"""

import pytest


class TestOrderIntegrity:
    """Every order must have at least one line item and correct totals."""

    def test_no_empty_orders(self, db_session):
        """INV-001: Every Order must have at least one LineItem."""
        empty_orders = db_session.execute(
            """
            SELECT o.id
            FROM orders o
            LEFT JOIN line_items li ON li.order_id = o.id
            WHERE li.id IS NULL
            """
        ).fetchall()

        assert len(empty_orders) == 0, (
            f"Found {len(empty_orders)} order(s) with no line items: "
            f"{[r[0] for r in empty_orders]}"
        )

    def test_order_totals_match_line_items(self, db_session):
        """INV-005: Order total must equal sum of line item subtotals."""
        mismatched = db_session.execute(
            """
            SELECT o.id, o.total_amount, COALESCE(SUM(li.quantity * li.unit_price), 0) as computed
            FROM orders o
            LEFT JOIN line_items li ON li.order_id = o.id
            GROUP BY o.id, o.total_amount
            HAVING o.total_amount != COALESCE(SUM(li.quantity * li.unit_price), 0)
            """
        ).fetchall()

        assert len(mismatched) == 0, (
            f"Found {len(mismatched)} order(s) with mismatched totals: "
            f"{[(r[0], f'stored={r[1]} computed={r[2]}') for r in mismatched]}"
        )
