"""Fitness Function: Order State Machine (INV-003)

Guards:
  INV-003: Order status transitions must follow:
           draft → submitted → processing → shipped → delivered (no reverse)

This is an example fitness function. In a real project, this would
test your actual Order model's state transition logic.
"""

import pytest


# Valid state transitions (from → to)
VALID_TRANSITIONS = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"processing", "cancelled"},
    "processing": {"shipped"},
    "shipped": {"delivered"},
    "delivered": set(),   # terminal state
    "cancelled": set(),   # terminal state
}

ALL_STATES = set(VALID_TRANSITIONS.keys())


class TestOrderStateMachine:
    """Order status transitions must follow the defined state machine."""

    def test_all_transitions_are_valid(self):
        """INV-003: Only valid forward transitions are allowed."""
        for from_state, allowed in VALID_TRANSITIONS.items():
            for to_state in ALL_STATES:
                if to_state in allowed:
                    # This transition should succeed
                    assert _can_transition(from_state, to_state), (
                        f"Expected {from_state} → {to_state} to be allowed"
                    )
                else:
                    # This transition should be rejected
                    assert not _can_transition(from_state, to_state), (
                        f"Expected {from_state} → {to_state} to be FORBIDDEN"
                    )

    def test_no_reverse_transitions(self):
        """No order can go backwards in the lifecycle."""
        order_sequence = ["draft", "submitted", "processing", "shipped", "delivered"]

        for i, current in enumerate(order_sequence):
            for prev in order_sequence[:i]:
                assert not _can_transition(current, prev), (
                    f"Reverse transition {current} → {prev} should be forbidden"
                )

    def test_terminal_states_have_no_exits(self):
        """Delivered and cancelled are terminal — no further transitions."""
        for terminal in ["delivered", "cancelled"]:
            for target in ALL_STATES:
                assert not _can_transition(terminal, target), (
                    f"Terminal state {terminal} should not transition to {target}"
                )

    def test_cancellation_only_from_early_states(self):
        """Orders can only be cancelled from draft or submitted."""
        assert _can_transition("draft", "cancelled")
        assert _can_transition("submitted", "cancelled")
        assert not _can_transition("processing", "cancelled")
        assert not _can_transition("shipped", "cancelled")
        assert not _can_transition("delivered", "cancelled")


def _can_transition(from_state: str, to_state: str) -> bool:
    """Check if a state transition is valid according to the state machine.

    In a real project, this would call your Order model's transition method.
    """
    return to_state in VALID_TRANSITIONS.get(from_state, set())
