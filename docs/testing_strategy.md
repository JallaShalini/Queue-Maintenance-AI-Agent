# Testing Strategy

## Overview
Our testing strategy targets verification of the structural integrity of the safety mechanisms before execution scenarios are scaled out. 

## Automated Test Suites (`tests/`)

- **Database Tests** (`test_database.py`): Validates schema integrity, checking all components required for reversible state logic are fully constructed on init.
- **Operations Tests** (`test_operations.py`): Verifies the undo logging happens transactionally and captures raw JSON data precisely matching the original state.
- **Restoration Tests** (`test_restore.py`): Reverts actions dynamically from the action ID log and guarantees full restoration from accidental purges or malformed data mutations.
- **Trust Tests** (`test_trust_engine.py`): Confirms that action types increment their successful execution independently of other actions.
- **Graph Routing Tests** (`test_graph.py`): Demonstrates simulated node traversal based strictly on valid human interrupt logic for low-trust operations (e.g. Reject triggers 0 mutations, Approve maps correctly).

## Container Execution
These tests use `pytest` running isolated instances with mocked test DB files via `tempfile` fixtures.

## Adversarial Simulation
The simulation file `tests/simulate_failure.py` specifically mirrors the Replit vibe coding mishap. It skips standard LLM generation and manually overrides the state with a massive deletion request of a queued database. 
- The script asserts that the LangGraph routing engine overrides the plan, captures the pause request, and halts.
- Once explicitly allowed, it reverses the payload locally to ensure identical queue states.
