"""Fitness Function: Tenant Isolation (INV-002)

Guards:
  INV-002: Every database query on orders must filter by tenant_id

This fitness function scans all query builders in the orders module
to verify that tenant_id filtering is always present. In a real project,
this would use AST analysis or grep-based scanning.
"""

import ast
import os
from pathlib import Path

import pytest


# Modules that MUST include tenant_id filtering in all queries
SCANNED_MODULES = [
    "app/api/v1/endpoints/orders.py",
    "app/models/order.py",
]

# Patterns that indicate a query without tenant filtering
QUERY_PATTERNS = [
    "session.query(",
    "session.execute(",
    "select(",
    ".filter(",
    ".where(",
]


class TestTenantIsolation:
    """Every query on orders must filter by tenant_id."""

    def test_all_order_queries_filter_by_tenant(self):
        """INV-002: Scan order modules for queries missing tenant_id filter."""
        violations = []

        for module_path in SCANNED_MODULES:
            if not os.path.exists(module_path):
                continue

            with open(module_path) as f:
                lines = f.readlines()

            in_query_block = False
            query_start_line = 0
            has_tenant_filter = False

            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # Detect query start
                if any(p in stripped for p in QUERY_PATTERNS):
                    in_query_block = True
                    query_start_line = i
                    has_tenant_filter = "tenant_id" in stripped

                # Track tenant_id in continuation lines
                if in_query_block and "tenant_id" in stripped:
                    has_tenant_filter = True

                # Detect query end (heuristic: closing paren or blank line)
                if in_query_block and (stripped.endswith(")") or stripped == ""):
                    if not has_tenant_filter:
                        violations.append(
                            f"{module_path}:{query_start_line} — query without tenant_id filter"
                        )
                    in_query_block = False
                    has_tenant_filter = False

        assert len(violations) == 0, (
            f"Found {len(violations)} query(ies) without tenant_id filtering:\n"
            + "\n".join(f"  • {v}" for v in violations)
        )
