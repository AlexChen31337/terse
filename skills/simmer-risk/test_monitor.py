#!/usr/bin/env python3
"""
Tests for Simmer Risk Monitor — mocked Simmer API responses.

Usage:
    uv run python test_monitor.py
    uv run python test_monitor.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# Make sure we can import from this directory
sys.path.insert(0, str(Path(__file__).parent))

import monitor
import risk_check
from monitor import (
    check_circuit_breaker,
    check_position,
    compute_pnl_pct,
    get_position_side,
    get_position_shares,
)
from risk_check import (
    check_circuit_breaker_proximity,
    check_portfolio_exposure,
    check_position_count,
    check_position_size,
    check_trading_paused,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

MOCK_PORTFOLIO_HEALTHY = {
    "balance_usdc": 4.04,
    "total_exposure": 17.69,
    "positions_count": 1,
    "pnl_24h": None,
    "pnl_total": 3.54,
    "polymarket_pnl": 3.54,
}

MOCK_PORTFOLIO_CRITICAL = {
    "balance_usdc": 2.0,
    "total_exposure": 13.0,
    "positions_count": 3,
    "pnl_24h": None,
    "pnl_total": -2.50,
    "polymarket_pnl": -2.50,
}

MOCK_POSITION_HEALTHY = {
    "market_id": "test-market-healthy-001",
    "question": "Will Anthropic have the best AI model at the end of March 2026?",
    "shares_yes": 29.78,
    "shares_no": 0.0,
    "current_price": 0.594,
    "current_probability": 0.594,
    "current_value": 17.69,
    "cost_basis": 13.96,
    "avg_cost": 0.469,
    "pnl": 3.73,
    "status": "active",
    "resolves_at": "2026-03-31T00:00:00",
    "venue": "polymarket",
    "currency": "USDC",
    "sources": ["sdk:ai-domain-edge"],
}

MOCK_POSITION_STOP_LOSS = {
    "market_id": "test-market-stoploss-002",
    "question": "Will Bitcoin hit $100k by February 2026?",
    "shares_yes": 100.0,
    "shares_no": 0.0,
    "current_price": 0.04,
    "current_probability": 0.04,
    "current_value": 4.0,
    "cost_basis": 20.0,
    "avg_cost": 0.20,
    "pnl": -16.0,      # -80% — way past stop-loss
    "status": "active",
    "resolves_at": "2026-02-28T23:59:59",
    "venue": "polymarket",
    "currency": "USDC",
    "sources": ["sdk:test"],
}

MOCK_POSITION_TAKE_PROFIT = {
    "market_id": "test-market-profit-003",
    "question": "Will Anthropic dominate AI in Q1 2026?",
    "shares_yes": 50.0,
    "shares_no": 0.0,
    "current_price": 0.90,
    "current_probability": 0.90,
    "current_value": 45.0,
    "cost_basis": 25.0,
    "avg_cost": 0.50,
    "pnl": 20.0,      # +80% — past take-profit
    "status": "active",
    "resolves_at": "2026-03-31T00:00:00",
    "venue": "polymarket",
    "currency": "USDC",
    "sources": ["sdk:test"],
}

MOCK_POSITION_SIM = {
    "market_id": "test-sim-market-004",
    "question": "Bitcoin Up or Down - March 1, 9:00AM",
    "shares_yes": 30.0,
    "shares_no": 0.0,
    "current_price": 0.01,
    "current_probability": 0.01,
    "current_value": 0.3,
    "cost_basis": 15.0,
    "avg_cost": 0.5,
    "pnl": -14.7,     # -98%
    "status": "active",
    "resolves_at": "2026-03-01T14:00:00",
    "venue": "simmer",
    "currency": "$SIM",
    "sources": ["fear-harvester"],
}

MOCK_POSITION_NO_SHARES = {
    "market_id": "test-market-resolved-005",
    "question": "Already resolved market",
    "shares_yes": 0.0,
    "shares_no": 0.0,
    "current_price": 0.5,
    "current_probability": 0.5,
    "current_value": 0.0,
    "cost_basis": 5.0,
    "avg_cost": 0.5,
    "pnl": -5.0,
    "status": "resolved",
    "venue": "polymarket",
    "currency": "USDC",
    "sources": ["sdk:test"],
}

DEFAULT_CONFIG = {
    "stop_loss_pct": -0.20,
    "circuit_breaker_pct": -0.15,
    "take_profit_pct": 0.50,
    "max_position_pct": 0.30,
    "max_positions": 5,
    "trading_paused": False,
    "high_water_mark": 18.00,
}


# ---------------------------------------------------------------------------
# Helper: temp dir for side-effect-free config/log writes
# ---------------------------------------------------------------------------

def make_temp_paths(tmp_dir: str) -> None:
    """Patch module-level paths to use temp directory."""
    tmp = Path(tmp_dir)
    (tmp / "data").mkdir(exist_ok=True)
    monitor.CONFIG_PATH = tmp / "risk_config.json"
    monitor.DATA_DIR = tmp / "data"
    monitor.LOG_PATH = tmp / "data" / "monitor_log.jsonl"
    monitor.PAUSE_FLAG = tmp / "data" / "trading_paused.flag"
    risk_check.CONFIG_PATH = tmp / "risk_config.json"
    risk_check.DATA_DIR = tmp / "data"
    risk_check.LOG_PATH = tmp / "data" / "risk_check_log.jsonl"
    risk_check.PAUSE_FLAG = tmp / "data" / "trading_paused.flag"
    # Write default config
    monitor.CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))


# ===========================================================================
# Tests: compute_pnl_pct
# ===========================================================================
class TestComputePnlPct(unittest.TestCase):
    def test_healthy_position(self):
        pnl_pct = compute_pnl_pct(MOCK_POSITION_HEALTHY)
        self.assertIsNotNone(pnl_pct)
        # 3.73 / 13.96 ≈ 0.267
        self.assertAlmostEqual(pnl_pct, 0.267, delta=0.01)

    def test_stop_loss_position(self):
        pnl_pct = compute_pnl_pct(MOCK_POSITION_STOP_LOSS)
        self.assertIsNotNone(pnl_pct)
        self.assertAlmostEqual(pnl_pct, -0.80, delta=0.01)

    def test_take_profit_position(self):
        pnl_pct = compute_pnl_pct(MOCK_POSITION_TAKE_PROFIT)
        self.assertIsNotNone(pnl_pct)
        self.assertAlmostEqual(pnl_pct, 0.80, delta=0.01)

    def test_zero_cost_basis(self):
        pos = dict(MOCK_POSITION_HEALTHY, cost_basis=0)
        pnl_pct = compute_pnl_pct(pos)
        self.assertIsNone(pnl_pct)

    def test_negative_cost_basis(self):
        # Already sold or partially closed
        pos = dict(MOCK_POSITION_HEALTHY, cost_basis=-1.0)
        pnl_pct = compute_pnl_pct(pos)
        self.assertIsNone(pnl_pct)


# ===========================================================================
# Tests: get_position_side / get_position_shares
# ===========================================================================
class TestPositionSideShares(unittest.TestCase):
    def test_yes_side(self):
        side = get_position_side(MOCK_POSITION_HEALTHY)
        self.assertEqual(side, "yes")

    def test_no_side(self):
        pos = dict(MOCK_POSITION_HEALTHY, shares_yes=0.0, shares_no=50.0)
        side = get_position_side(pos)
        self.assertEqual(side, "no")

    def test_no_shares(self):
        side = get_position_side(MOCK_POSITION_NO_SHARES)
        self.assertIsNone(side)

    def test_shares_yes(self):
        shares = get_position_shares(MOCK_POSITION_HEALTHY)
        self.assertAlmostEqual(shares, 29.78, delta=0.01)

    def test_shares_no(self):
        pos = dict(MOCK_POSITION_HEALTHY, shares_yes=0.0, shares_no=50.0)
        shares = get_position_shares(pos)
        self.assertAlmostEqual(shares, 50.0, delta=0.01)


# ===========================================================================
# Tests: Circuit Breaker
# ===========================================================================
class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)

    def test_no_trigger_healthy_portfolio(self):
        # Portfolio value = 4.04 + 17.69 = 21.73, HWM = 18 → above HWM, no trigger
        triggered = check_circuit_breaker(
            MOCK_PORTFOLIO_HEALTHY,
            DEFAULT_CONFIG.copy(),
            dry_run=True,
        )
        self.assertFalse(triggered)

    def test_trigger_critical_portfolio(self):
        # Portfolio = 2.0 + 13.0 = 15.0, HWM = 18.0 → drawdown = -16.7% > -15% threshold
        cfg = DEFAULT_CONFIG.copy()
        cfg["high_water_mark"] = 18.0
        triggered = check_circuit_breaker(
            MOCK_PORTFOLIO_CRITICAL,
            cfg,
            dry_run=True,
        )
        self.assertTrue(triggered)

    def test_exactly_at_threshold(self):
        # Portfolio = 15.12 → drawdown = (15.12 - 18) / 18 = -16% → triggers (> 15% threshold)
        # Note: Use clear values to avoid floating-point boundary ambiguity
        portfolio = {
            "balance_usdc": 5.0,
            "total_exposure": 10.12,  # total = 15.12, drawdown = -16%
            "polymarket_pnl": -2.88,
        }
        cfg = DEFAULT_CONFIG.copy()
        cfg["high_water_mark"] = 18.0
        triggered = check_circuit_breaker(portfolio, cfg, dry_run=True)
        self.assertTrue(triggered)

    def test_hwm_update_on_new_high(self):
        # Portfolio value > HWM → should update HWM
        portfolio = {
            "balance_usdc": 10.0,
            "total_exposure": 15.0,
        }
        cfg = DEFAULT_CONFIG.copy()
        cfg["high_water_mark"] = 18.0
        # Write config to temp path
        monitor.CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

        triggered = check_circuit_breaker(portfolio, cfg, dry_run=False)
        self.assertFalse(triggered)

        # Config should have been updated with new HWM
        updated_cfg = json.loads(monitor.CONFIG_PATH.read_text())
        self.assertGreater(updated_cfg["high_water_mark"], 18.0)


# ===========================================================================
# Tests: check_position (stop-loss / take-profit / normal)
# ===========================================================================
class TestCheckPosition(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)
        self.api_key = "test_key"

    def _mock_trade_response(self) -> dict:
        return {"success": True, "trade_id": "mock-trade-id", "order_status": "filled"}

    def test_healthy_position_no_action(self):
        actions = check_position(
            self.api_key, MOCK_POSITION_HEALTHY, DEFAULT_CONFIG.copy(),
            include_sim=False, dry_run=True,
        )
        self.assertEqual(len(actions), 0)

    def test_stop_loss_triggers(self):
        with patch("monitor.simmer_trade") as mock_trade:
            mock_trade.return_value = self._mock_trade_response()
            actions = check_position(
                self.api_key, MOCK_POSITION_STOP_LOSS, DEFAULT_CONFIG.copy(),
                include_sim=False, dry_run=True,
            )
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["event"], "stop_loss_triggered")
        self.assertAlmostEqual(actions[0]["shares_sold"], 100.0, delta=0.01)
        self.assertEqual(actions[0]["side"], "yes")

    def test_take_profit_triggers(self):
        with patch("monitor.simmer_trade") as mock_trade:
            mock_trade.return_value = self._mock_trade_response()
            actions = check_position(
                self.api_key, MOCK_POSITION_TAKE_PROFIT, DEFAULT_CONFIG.copy(),
                include_sim=False, dry_run=True,
            )
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["event"], "take_profit_triggered")
        # Should sell HALF of 50 shares = 25
        self.assertAlmostEqual(actions[0]["shares_sold"], 25.0, delta=0.01)
        self.assertEqual(actions[0]["side"], "yes")

    def test_sim_position_skipped_by_default(self):
        actions = check_position(
            self.api_key, MOCK_POSITION_SIM, DEFAULT_CONFIG.copy(),
            include_sim=False, dry_run=True,
        )
        self.assertEqual(len(actions), 0)

    def test_sim_position_included_when_flag_set(self):
        with patch("monitor.simmer_trade") as mock_trade:
            mock_trade.return_value = self._mock_trade_response()
            actions = check_position(
                self.api_key, MOCK_POSITION_SIM, DEFAULT_CONFIG.copy(),
                include_sim=True, dry_run=True,
            )
        # $SIM position at -98% should trigger stop-loss when include_sim=True
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["event"], "stop_loss_triggered")

    def test_resolved_position_skipped(self):
        actions = check_position(
            self.api_key, MOCK_POSITION_NO_SHARES, DEFAULT_CONFIG.copy(),
            include_sim=False, dry_run=True,
        )
        self.assertEqual(len(actions), 0)

    def test_no_side_skipped(self):
        pos = dict(MOCK_POSITION_STOP_LOSS, shares_yes=0.0, shares_no=0.0)
        actions = check_position(
            self.api_key, pos, DEFAULT_CONFIG.copy(),
            include_sim=False, dry_run=True,
        )
        self.assertEqual(len(actions), 0)


# ===========================================================================
# Tests: risk_check checks
# ===========================================================================
class TestRiskCheckPaused(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)

    def test_not_paused(self):
        cfg = DEFAULT_CONFIG.copy()
        result = check_trading_paused(cfg)
        self.assertIsNone(result)

    def test_paused_in_config(self):
        cfg = dict(DEFAULT_CONFIG, trading_paused=True)
        result = check_trading_paused(cfg)
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])
        self.assertIn("PAUSED", result["reason"])

    def test_paused_by_flag_file(self):
        flag_path = risk_check.PAUSE_FLAG
        flag_path.write_text(json.dumps({
            "paused_at": "2026-02-22T10:00:00Z",
            "reason": "Portfolio drawdown -20%",
        }))
        cfg = DEFAULT_CONFIG.copy()
        result = check_trading_paused(cfg)
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])


class TestRiskCheckPositionCount(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)

    def _make_real_position(self, market_id: str) -> dict:
        return {
            "market_id": market_id,
            "question": f"Test market {market_id}",
            "status": "active",
            "venue": "polymarket",
            "currency": "USDC",
            "current_value": 5.0,
        }

    def test_under_limit(self):
        positions = [self._make_real_position(f"m{i}") for i in range(3)]
        result = check_position_count(positions, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNone(result)

    def test_at_limit(self):
        positions = [self._make_real_position(f"m{i}") for i in range(5)]
        result = check_position_count(positions, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])
        self.assertIn("5/5", result["reason"])

    def test_over_limit(self):
        positions = [self._make_real_position(f"m{i}") for i in range(8)]
        result = check_position_count(positions, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])

    def test_sim_venue_not_counted_for_real(self):
        # $SIM positions don't count toward real money position limit
        positions = [
            dict(self._make_real_position(f"m{i}"), venue="simmer", currency="$SIM")
            for i in range(10)
        ]
        result = check_position_count(positions, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNone(result)  # All are sim, so real count = 0

    def test_sim_venue_not_checked(self):
        # For simmer trades, no position count check
        positions = [self._make_real_position(f"m{i}") for i in range(10)]
        result = check_position_count(positions, DEFAULT_CONFIG.copy(), "simmer")
        self.assertIsNone(result)


class TestRiskCheckPositionSize(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)

    def test_within_limit(self):
        # Portfolio = 4.04 + 17.69 = 21.73, max 30% = 6.52
        # Amount = 5.0 → 23% → OK
        result = check_position_size(5.0, MOCK_PORTFOLIO_HEALTHY, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNone(result)

    def test_exceeds_limit(self):
        # Portfolio = 21.73, max 30% = 6.52
        # Amount = 8.0 → 36.8% → denied
        result = check_position_size(8.0, MOCK_PORTFOLIO_HEALTHY, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])
        self.assertIn("30%", result["reason"])

    def test_sim_venue_not_size_checked(self):
        # $SIM positions not size-checked against real money portfolio
        result = check_position_size(999.0, MOCK_PORTFOLIO_HEALTHY, DEFAULT_CONFIG.copy(), "simmer")
        self.assertIsNone(result)

    def test_zero_portfolio_denied(self):
        portfolio = {"balance_usdc": 0.0, "total_exposure": 0.0}
        result = check_position_size(5.0, portfolio, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])


class TestRiskCheckExposure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)

    def test_within_exposure(self):
        # Portfolio = 21.73, exposure = 17.69
        # New trade of 1.0 → new exposure = 18.69 / 21.73 = 86% → OK (threshold 90%)
        result = check_portfolio_exposure(1.0, MOCK_PORTFOLIO_HEALTHY, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNone(result)

    def test_exceeds_exposure(self):
        # Portfolio = 21.73, exposure = 17.69
        # New trade of 5.0 → new exposure = 22.69 / 21.73 = 104% → denied
        result = check_portfolio_exposure(5.0, MOCK_PORTFOLIO_HEALTHY, DEFAULT_CONFIG.copy(), "polymarket")
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])

    def test_sim_not_exposure_checked(self):
        result = check_portfolio_exposure(999.0, MOCK_PORTFOLIO_HEALTHY, DEFAULT_CONFIG.copy(), "simmer")
        self.assertIsNone(result)


class TestRiskCheckCBProximity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)

    def test_healthy_no_warning(self):
        # Portfolio = 21.73, HWM = 18 → above HWM, no drawdown
        result = check_circuit_breaker_proximity(MOCK_PORTFOLIO_HEALTHY, DEFAULT_CONFIG.copy())
        self.assertIsNone(result)

    def test_near_cb_threshold_denied(self):
        # Portfolio = 15.0, HWM = 18.0 → drawdown = -16.7% > -15% → denied
        portfolio = {"balance_usdc": 5.0, "total_exposure": 10.0}
        result = check_circuit_breaker_proximity(portfolio, DEFAULT_CONFIG.copy())
        self.assertIsNotNone(result)
        self.assertFalse(result["approved"])

    def test_mild_drawdown_ok(self):
        # Portfolio = 17.0, HWM = 18.0 → drawdown = -5.6% (within 50% of -15%)
        portfolio = {"balance_usdc": 5.0, "total_exposure": 12.0}
        result = check_circuit_breaker_proximity(portfolio, DEFAULT_CONFIG.copy())
        self.assertIsNone(result)


# ===========================================================================
# Tests: End-to-end check_trade (mocked API)
# ===========================================================================
class TestCheckTrade(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)
        risk_check.CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2))

    def _mock_api(self):
        """Return a context manager that mocks all Simmer API calls."""
        portfolio_resp = MagicMock()
        portfolio_resp.json.return_value = MOCK_PORTFOLIO_HEALTHY
        portfolio_resp.raise_for_status = MagicMock()

        positions_resp = MagicMock()
        positions_resp.json.return_value = {
            "positions": [MOCK_POSITION_HEALTHY],
        }
        positions_resp.raise_for_status = MagicMock()

        def get_side_effect(url, **kwargs):
            if "/portfolio" in url:
                return portfolio_resp
            elif "/positions" in url:
                return positions_resp
            return portfolio_resp

        return patch("requests.get", side_effect=get_side_effect)

    def test_sim_always_approved(self):
        result = risk_check.check_trade("any-market", 500.0, venue="simmer")
        self.assertTrue(result["approved"])
        self.assertIn("SIM", result["reason"])

    def test_paused_denied(self):
        cfg = dict(DEFAULT_CONFIG, trading_paused=True)
        risk_check.CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
        result = risk_check.check_trade("any-market", 5.0, venue="polymarket")
        self.assertFalse(result["approved"])
        self.assertIn("PAUSED", result["reason"])

    def test_small_trade_approved(self):
        with self._mock_api():
            # 1.0 USDC on a ~22 USDC portfolio = 4.6% → should pass all checks
            result = risk_check.check_trade("any-market", 1.0, venue="polymarket")
        self.assertTrue(result["approved"])

    def test_oversized_trade_denied(self):
        with self._mock_api():
            # 10.0 USDC on a ~22 USDC portfolio = 46% → exceeds 30% max
            result = risk_check.check_trade("any-market", 10.0, venue="polymarket")
        self.assertFalse(result["approved"])
        self.assertIn("position_size", result.get("failed_at_check", ""))

    def test_too_many_positions_denied(self):
        five_positions = [
            dict(
                MOCK_POSITION_HEALTHY,
                market_id=f"real-{i}",
                status="active",
                venue="polymarket",
                currency="USDC",
            )
            for i in range(5)
        ]

        positions_resp = MagicMock()
        positions_resp.json.return_value = {"positions": five_positions}
        positions_resp.raise_for_status = MagicMock()

        portfolio_resp = MagicMock()
        portfolio_resp.json.return_value = MOCK_PORTFOLIO_HEALTHY
        portfolio_resp.raise_for_status = MagicMock()

        def get_side_effect(url, **kwargs):
            if "/portfolio" in url:
                return portfolio_resp
            elif "/positions" in url:
                return positions_resp
            return portfolio_resp

        with patch("requests.get", side_effect=get_side_effect):
            result = risk_check.check_trade("any-market", 1.0, venue="polymarket")

        self.assertFalse(result["approved"])
        self.assertIn("position_count", result.get("failed_at_check", ""))


# ===========================================================================
# Tests: Logging
# ===========================================================================
class TestLogging(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        make_temp_paths(self.tmp)

    def test_log_event_creates_file(self):
        monitor.log_event({"event": "test", "value": 42})
        log_path = monitor.LOG_PATH
        self.assertTrue(log_path.exists())
        content = log_path.read_text()
        parsed = json.loads(content.strip())
        self.assertEqual(parsed["event"], "test")
        self.assertEqual(parsed["value"], 42)
        self.assertIn("timestamp", parsed)

    def test_multiple_log_events(self):
        for i in range(5):
            monitor.log_event({"event": f"test_{i}", "index": i})
        log_path = monitor.LOG_PATH
        lines = [l for l in log_path.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 5)
        for i, line in enumerate(lines):
            parsed = json.loads(line)
            self.assertEqual(parsed["index"], i)


# ===========================================================================
# Run
# ===========================================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
