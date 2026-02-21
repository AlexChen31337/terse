"""Shared fixtures for FearHarvester tests."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture()
def tmp_state_file(tmp_path):
    """Provide a temporary state file path and patch STATE_FILE."""
    import executor

    original = executor.STATE_FILE
    state_path = tmp_path / "executor_state.json"
    executor.STATE_FILE = state_path
    yield state_path
    executor.STATE_FILE = original


@pytest.fixture()
def empty_state():
    """Return a fresh empty state dict."""
    return {
        "positions": [],
        "total_invested": 0.0,
        "mode": "paper",
        "last_action": None,
        "version": 2,
    }


@pytest.fixture()
def state_with_positions():
    """Return a state with sample open positions."""
    return {
        "positions": [
            {
                "timestamp": "2025-10-01T10:00:00",
                "entry_price": 60000.0,
                "btc_qty": 0.00833,
                "usd_amount": 500.0,
                "fg_at_entry": 8,
                "status": "open",
                "mode": "paper",
                "hl_order_id": None,
            },
            {
                "timestamp": "2025-10-15T10:00:00",
                "entry_price": 58000.0,
                "btc_qty": 0.00862,
                "usd_amount": 500.0,
                "fg_at_entry": 12,
                "status": "open",
                "mode": "paper",
                "hl_order_id": None,
            },
        ],
        "total_invested": 1000.0,
        "mode": "paper",
        "last_action": "DCA_BUY $500 @ $58,000 (F&G=12) [paper]",
        "version": 2,
    }


@pytest.fixture()
def default_config():
    """Return default executor config."""
    return {
        "buy_threshold": 20,
        "sell_threshold": 50,
        "hold_days": 120,
        "dca_amount_usd": 500.0,
        "max_capital": 5000.0,
    }


@pytest.fixture()
def mock_hl_executor():
    """Return a mocked HLSpotExecutor that doesn't call the real API."""
    from executor import HLSpotExecutor

    executor_obj = HLSpotExecutor.__new__(HLSpotExecutor)
    executor_obj.private_key = "0xfake_private_key"
    executor_obj.wallet_address = "0xfake_wallet"
    executor_obj.testnet = False
    executor_obj._client = MagicMock()
    return executor_obj
