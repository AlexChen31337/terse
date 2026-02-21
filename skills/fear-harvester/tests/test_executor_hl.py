"""Tests for FearHarvester executor with Hyperliquid spot integration."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import executor
from executor import (
    UBTC_PAIR,
    UBTC_SZ_DECIMALS,
    HLSpotExecutor,
    decide,
    execute_dca_buy,
    execute_rebalance,
    get_btc_price,
    get_fear_greed,
    get_position_summary,
    load_hl_credentials,
    load_state,
    main,
    save_state,
    show_status,
)


# ===========================================================================
# Credential loading
# ===========================================================================

class TestLoadCredentials:
    """Tests for load_hl_credentials()."""

    def test_load_credentials_from_env_vars(self, monkeypatch):
        """Credentials from environment variables are returned."""
        monkeypatch.setenv("HL_PRIVATE_KEY", "0xtest_key")
        monkeypatch.setenv("HL_WALLET_ADDRESS", "0xtest_wallet")
        # Ensure .env file doesn't interfere
        monkeypatch.setattr(executor, "HL_ENV_PATH", Path("/nonexistent/.env"))

        pk, wa = load_hl_credentials()
        assert pk == "0xtest_key"
        assert wa == "0xtest_wallet"

    def test_load_credentials_fallback_names(self, monkeypatch):
        """Fallback env var names (PRIVATE_KEY, WALLET_ADDRESS) work."""
        monkeypatch.delenv("HL_PRIVATE_KEY", raising=False)
        monkeypatch.delenv("HL_WALLET_ADDRESS", raising=False)
        monkeypatch.setenv("PRIVATE_KEY", "0xfallback_key")
        monkeypatch.setenv("WALLET_ADDRESS", "0xfallback_wallet")
        monkeypatch.setattr(executor, "HL_ENV_PATH", Path("/nonexistent/.env"))

        pk, wa = load_hl_credentials()
        assert pk == "0xfallback_key"
        assert wa == "0xfallback_wallet"

    def test_load_credentials_from_env_file(self, tmp_path, monkeypatch):
        """Credentials from .env file are loaded into environment."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# Hyperliquid credentials\n"
            "HL_PRIVATE_KEY=0xfile_key\n"
            "HL_WALLET_ADDRESS=0xfile_wallet\n"
        )
        monkeypatch.delenv("HL_PRIVATE_KEY", raising=False)
        monkeypatch.delenv("HL_WALLET_ADDRESS", raising=False)
        monkeypatch.delenv("PRIVATE_KEY", raising=False)
        monkeypatch.delenv("WALLET_ADDRESS", raising=False)
        monkeypatch.setattr(executor, "HL_ENV_PATH", env_file)

        pk, wa = load_hl_credentials()
        assert pk == "0xfile_key"
        assert wa == "0xfile_wallet"

    def test_load_credentials_missing(self, monkeypatch):
        """Missing credentials return None."""
        monkeypatch.delenv("HL_PRIVATE_KEY", raising=False)
        monkeypatch.delenv("HL_WALLET_ADDRESS", raising=False)
        monkeypatch.delenv("PRIVATE_KEY", raising=False)
        monkeypatch.delenv("WALLET_ADDRESS", raising=False)
        monkeypatch.setattr(executor, "HL_ENV_PATH", Path("/nonexistent/.env"))

        pk, wa = load_hl_credentials()
        assert pk is None
        assert wa is None

    def test_env_file_skips_comments_and_blanks(self, tmp_path, monkeypatch):
        """Comments and blank lines in .env are ignored."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# comment\n"
            "\n"
            "HL_PRIVATE_KEY=0xkey\n"
            "  # another comment\n"
        )
        monkeypatch.delenv("HL_PRIVATE_KEY", raising=False)
        monkeypatch.delenv("HL_WALLET_ADDRESS", raising=False)
        monkeypatch.delenv("PRIVATE_KEY", raising=False)
        monkeypatch.delenv("WALLET_ADDRESS", raising=False)
        monkeypatch.setattr(executor, "HL_ENV_PATH", env_file)

        pk, wa = load_hl_credentials()
        assert pk == "0xkey"
        assert wa is None


# ===========================================================================
# UBTC size calculation
# ===========================================================================

class TestUBTCSizeCalculation:
    """Tests for BTC amount calculation from USDC."""

    def test_basic_size_calculation(self):
        """500 USDC at $67,000 → ~0.00746 BTC."""
        amount_usdc = 500.0
        price = 67000.0
        btc_size = round(amount_usdc / price, UBTC_SZ_DECIMALS)
        assert btc_size == 0.00746

    def test_size_at_100k(self):
        """500 USDC at $100,000 → 0.005 BTC."""
        btc_size = round(500.0 / 100000.0, UBTC_SZ_DECIMALS)
        assert btc_size == 0.005

    def test_small_amount_rounds_correctly(self):
        """$50 at $67,000 → 0.00075 BTC (5 decimal places)."""
        btc_size = round(50.0 / 67000.0, UBTC_SZ_DECIMALS)
        assert btc_size == 0.00075

    def test_large_amount(self):
        """$5000 at $67,000 → 0.07463 BTC."""
        btc_size = round(5000.0 / 67000.0, UBTC_SZ_DECIMALS)
        assert btc_size == 0.07463


# ===========================================================================
# HLSpotExecutor
# ===========================================================================

class TestHLSpotExecutor:
    """Tests for HLSpotExecutor class."""

    def test_spot_asset_index(self, mock_hl_executor):
        """Spot asset index = 10000 + 142 = 10142."""
        assert mock_hl_executor._get_spot_asset_index() == 10142

    def test_ubtc_pair_constant(self):
        """UBTC pair constant is @142."""
        assert UBTC_PAIR == "@142"

    def test_place_spot_market_buy(self, mock_hl_executor):
        """Market buy builds correct order structure and calls exchange."""
        mock_hl_executor._client._exchange_request.return_value = {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": [
                        {"filled": {"totalSz": "0.00746", "avgPx": "67000.0", "oid": 12345}}
                    ]
                },
            },
        }
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "67000.0"}

        result = mock_hl_executor.place_spot_market_buy(500.0)

        assert result["status"] == "ok"
        # Verify the exchange request was called
        mock_hl_executor._client._exchange_request.assert_called_once()
        call_args = mock_hl_executor._client._exchange_request.call_args[0][0]
        assert call_args["type"] == "order"
        order = call_args["orders"][0]
        assert order["a"] == 10142  # spot asset index
        assert order["b"] is True  # buy
        assert order["t"] == {"limit": {"tif": "Ioc"}}  # IOC = market

    def test_place_spot_market_buy_with_price_override(self, mock_hl_executor):
        """Price override skips mid price lookup."""
        mock_hl_executor._client._exchange_request.return_value = {"status": "ok", "response": {}}

        mock_hl_executor.place_spot_market_buy(500.0, price=70000.0)

        # get_all_mids should NOT be called when price is provided
        mock_hl_executor._client.get_all_mids.assert_not_called()
        call_args = mock_hl_executor._client._exchange_request.call_args[0][0]
        order = call_args["orders"][0]
        # limit price = 70000 * 1.01 = 70700.0
        assert order["p"] == "70700.0"
        # size = 500 / 70000 = 0.00714
        assert order["s"] == "0.00714"

    def test_place_spot_market_sell(self, mock_hl_executor):
        """Market sell builds correct order with is_buy=False."""
        mock_hl_executor._client._exchange_request.return_value = {"status": "ok", "response": {}}
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "67000.0"}

        mock_hl_executor.place_spot_market_sell(0.01)

        call_args = mock_hl_executor._client._exchange_request.call_args[0][0]
        order = call_args["orders"][0]
        assert order["b"] is False  # sell
        assert order["a"] == 10142
        assert order["s"] == "0.01"

    def test_buy_raises_on_zero_size(self, mock_hl_executor):
        """Buy with tiny amount that rounds to 0 raises ValueError."""
        with pytest.raises(ValueError, match="too small"):
            mock_hl_executor.place_spot_market_buy(0.001, price=67000.0)

    def test_sell_raises_on_zero_size(self, mock_hl_executor):
        """Sell with 0 BTC raises ValueError."""
        with pytest.raises(ValueError, match="too small"):
            mock_hl_executor.place_spot_market_sell(0.0)

    def test_get_spot_balances(self, mock_hl_executor):
        """get_spot_balances calls client.get_spot_user_state."""
        mock_hl_executor._client.get_spot_user_state.return_value = {"balances": []}
        result = mock_hl_executor.get_spot_balances()
        mock_hl_executor._client.get_spot_user_state.assert_called_once_with("0xfake_wallet")
        assert result == {"balances": []}

    def test_get_spot_balances_no_wallet_raises(self):
        """get_spot_balances without wallet address raises ValueError."""
        ex = HLSpotExecutor.__new__(HLSpotExecutor)
        ex.wallet_address = None
        ex._client = MagicMock()
        with pytest.raises(ValueError, match="Wallet address required"):
            ex.get_spot_balances()

    def test_get_user_fills_no_wallet_raises(self):
        """get_user_fills without wallet address raises ValueError."""
        ex = HLSpotExecutor.__new__(HLSpotExecutor)
        ex.wallet_address = None
        ex._client = MagicMock()
        with pytest.raises(ValueError, match="Wallet address required"):
            ex.get_user_fills()

    def test_close_cleans_up_client(self, mock_hl_executor):
        """close() calls client.close() and sets _client to None."""
        mock_hl_executor.close()
        assert mock_hl_executor._client is None

    def test_client_lazy_load_requires_private_key(self):
        """Accessing .client without private key raises ValueError."""
        ex = HLSpotExecutor(private_key=None)
        with pytest.raises(ValueError, match="HL_PRIVATE_KEY required"):
            _ = ex.client


# ===========================================================================
# Decision engine
# ===========================================================================

class TestDecide:
    """Tests for the decide() function."""

    def test_dca_buy_below_threshold(self, empty_state, default_config):
        """F&G below threshold triggers DCA_BUY."""
        assert decide(5, empty_state, default_config) == "DCA_BUY"
        assert decide(20, empty_state, default_config) == "DCA_BUY"

    def test_hold_above_buy_below_sell(self, empty_state, default_config):
        """F&G between thresholds returns HOLD."""
        assert decide(30, empty_state, default_config) == "HOLD"
        assert decide(49, empty_state, default_config) == "HOLD"

    def test_hold_when_maxed_out(self, empty_state, default_config):
        """F&G below threshold but max capital reached → HOLD."""
        empty_state["total_invested"] = 5000.0
        assert decide(5, empty_state, default_config) == "HOLD"

    def test_rebalance_above_sell_threshold_with_old_positions(self, state_with_positions, default_config):
        """F&G above sell threshold with positions past hold_days → REBALANCE."""
        default_config["hold_days"] = 120
        # Make positions old enough (>120 days)
        old_date = (datetime.now() - timedelta(days=130)).isoformat()
        for p in state_with_positions["positions"]:
            p["timestamp"] = old_date
        assert decide(55, state_with_positions, default_config) == "REBALANCE_YIELD"

    def test_hold_above_sell_but_positions_too_new(self, state_with_positions, default_config):
        """F&G above sell threshold but positions not past hold_days → HOLD."""
        # Positions are recent (timestamps from fixture are 2025-10)
        # Hold days = 120, and positions are < 120 days from now in the fixture
        default_config["hold_days"] = 9999  # Very long hold period
        assert decide(55, state_with_positions, default_config) == "HOLD"

    def test_hold_no_positions_above_sell(self, empty_state, default_config):
        """F&G above sell threshold with no positions → HOLD."""
        assert decide(60, empty_state, default_config) == "HOLD"

    def test_boundary_buy_threshold(self, empty_state, default_config):
        """Exactly at buy threshold triggers buy."""
        assert decide(20, empty_state, default_config) == "DCA_BUY"
        assert decide(21, empty_state, default_config) == "HOLD"

    def test_boundary_sell_threshold(self, state_with_positions, default_config):
        """Exactly at sell threshold with old positions triggers rebalance."""
        old_date = (datetime.now() - timedelta(days=130)).isoformat()
        for p in state_with_positions["positions"]:
            p["timestamp"] = old_date
        assert decide(50, state_with_positions, default_config) == "REBALANCE_YIELD"


# ===========================================================================
# DCA buy execution
# ===========================================================================

class TestExecuteDCABuy:
    """Tests for execute_dca_buy() in all modes."""

    def test_dry_run_no_state_change(self, empty_state, default_config, tmp_state_file):
        """Dry-run mode does not modify state or write to disk."""
        result = execute_dca_buy(67000.0, 8, empty_state, default_config, mode="dry-run")
        assert "[DRY RUN]" in result
        assert empty_state["positions"] == []
        assert empty_state["total_invested"] == 0.0
        assert not tmp_state_file.exists()

    def test_dry_run_no_exchange_call(self, empty_state, default_config, mock_hl_executor, tmp_state_file):
        """Dry-run mode never calls HL API even with executor provided."""
        result = execute_dca_buy(
            67000.0, 8, empty_state, default_config,
            mode="dry-run", hl_executor=mock_hl_executor,
        )
        assert "[DRY RUN]" in result
        mock_hl_executor._client._exchange_request.assert_not_called()

    def test_paper_mode_writes_state(self, empty_state, default_config, tmp_state_file):
        """Paper mode updates local state and saves to disk."""
        result = execute_dca_buy(67000.0, 8, empty_state, default_config, mode="paper")
        assert "[PAPER]" in result
        assert len(empty_state["positions"]) == 1
        assert empty_state["total_invested"] == 500.0
        assert tmp_state_file.exists()

        saved = json.loads(tmp_state_file.read_text())
        assert saved["total_invested"] == 500.0
        assert saved["positions"][0]["entry_price"] == 67000.0

    def test_paper_mode_no_exchange_call(self, empty_state, default_config, tmp_state_file):
        """Paper mode does not call HL API."""
        result = execute_dca_buy(67000.0, 8, empty_state, default_config, mode="paper")
        assert "[PAPER]" in result
        # No HL executor passed, so no API calls possible

    def test_live_mode_calls_exchange(self, empty_state, default_config, mock_hl_executor, tmp_state_file):
        """Live mode calls HL exchange and updates state."""
        mock_hl_executor._client._exchange_request.return_value = {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": [
                        {"filled": {"totalSz": "0.00746", "avgPx": "67050.0", "oid": 99999}}
                    ]
                },
            },
        }
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "67000.0"}

        result = execute_dca_buy(
            67000.0, 8, empty_state, default_config,
            mode="live", hl_executor=mock_hl_executor,
        )
        assert "[DRY RUN]" not in result
        assert "[PAPER]" not in result
        assert "oid=99999" in result
        mock_hl_executor._client._exchange_request.assert_called_once()
        assert len(empty_state["positions"]) == 1
        # avgPx from fill used as entry price
        assert empty_state["positions"][0]["entry_price"] == 67050.0

    def test_live_mode_handles_error(self, empty_state, default_config, mock_hl_executor, tmp_state_file):
        """Live mode returns error message on API failure."""
        mock_hl_executor._client._exchange_request.return_value = {
            "status": "err",
            "response": "Insufficient margin",
        }
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "67000.0"}

        result = execute_dca_buy(
            67000.0, 8, empty_state, default_config,
            mode="live", hl_executor=mock_hl_executor,
        )
        assert "FAILED" in result
        assert "Insufficient margin" in result
        assert len(empty_state["positions"]) == 0

    def test_live_requires_executor(self, empty_state, default_config, tmp_state_file):
        """Live mode without HL executor raises ValueError."""
        with pytest.raises(ValueError, match="HLSpotExecutor required"):
            execute_dca_buy(67000.0, 8, empty_state, default_config, mode="live")

    def test_position_records_fg_value(self, empty_state, default_config, tmp_state_file):
        """Position records the F&G value at entry."""
        execute_dca_buy(67000.0, 15, empty_state, default_config, mode="paper")
        assert empty_state["positions"][0]["fg_at_entry"] == 15


# ===========================================================================
# Rebalance execution
# ===========================================================================

class TestExecuteRebalance:
    """Tests for execute_rebalance() in all modes."""

    def _make_old_positions(self, state, days=130):
        """Helper: make all positions old enough to sell."""
        old_date = (datetime.now() - timedelta(days=days)).isoformat()
        for p in state["positions"]:
            p["timestamp"] = old_date

    def test_dry_run_no_state_change(self, state_with_positions, default_config, tmp_state_file):
        """Dry-run rebalance does not modify state."""
        self._make_old_positions(state_with_positions)
        original_positions = [p.copy() for p in state_with_positions["positions"]]
        result = execute_rebalance(
            75000.0, 55, state_with_positions, default_config, mode="dry-run"
        )
        assert "[DRY RUN]" in result
        for p in state_with_positions["positions"]:
            assert p["status"] == "open"

    def test_paper_mode_closes_positions(self, state_with_positions, default_config, tmp_state_file):
        """Paper rebalance closes eligible positions."""
        self._make_old_positions(state_with_positions)
        result = execute_rebalance(
            75000.0, 55, state_with_positions, default_config, mode="paper"
        )
        assert "[PAPER]" in result
        closed = [p for p in state_with_positions["positions"] if p["status"] == "closed"]
        assert len(closed) == 2
        for p in closed:
            assert p["exit_price"] == 75000.0
            assert "pnl_pct" in p

    def test_no_eligible_positions(self, state_with_positions, default_config, tmp_state_file):
        """Rebalance with no positions past hold_days returns info message."""
        default_config["hold_days"] = 9999
        result = execute_rebalance(
            75000.0, 55, state_with_positions, default_config, mode="paper"
        )
        assert "No positions past" in result

    def test_live_mode_calls_sell(self, state_with_positions, default_config, mock_hl_executor, tmp_state_file):
        """Live rebalance calls HL sell and updates state."""
        self._make_old_positions(state_with_positions)
        mock_hl_executor._client._exchange_request.return_value = {"status": "ok", "response": {}}
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "75000.0"}

        result = execute_rebalance(
            75000.0, 55, state_with_positions, default_config,
            mode="live", hl_executor=mock_hl_executor,
        )
        mock_hl_executor._client._exchange_request.assert_called_once()
        closed = [p for p in state_with_positions["positions"] if p["status"] == "closed"]
        assert len(closed) == 2

    def test_live_sell_failure(self, state_with_positions, default_config, mock_hl_executor, tmp_state_file):
        """Live sell failure returns error, positions stay open."""
        self._make_old_positions(state_with_positions)
        mock_hl_executor._client._exchange_request.return_value = {
            "status": "err",
            "response": "Order rejected",
        }
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "75000.0"}

        result = execute_rebalance(
            75000.0, 55, state_with_positions, default_config,
            mode="live", hl_executor=mock_hl_executor,
        )
        assert "FAILED" in result
        # Positions should remain open since the sell failed
        open_pos = [p for p in state_with_positions["positions"] if p["status"] == "open"]
        assert len(open_pos) == 2


# ===========================================================================
# Position summary
# ===========================================================================

class TestPositionSummary:
    """Tests for get_position_summary()."""

    def test_empty_state_summary(self, empty_state):
        """Empty state returns zeroed summary."""
        summary = get_position_summary(empty_state, 67000.0)
        assert summary["open_count"] == 0
        assert summary["closed_count"] == 0
        assert summary["total_btc"] == 0
        assert summary["total_cost"] == 0
        assert summary["unrealized_pnl"] == 0
        assert summary["unrealized_pnl_pct"] == 0

    def test_summary_with_open_positions(self, state_with_positions):
        """Summary reflects open position values correctly."""
        summary = get_position_summary(state_with_positions, 75000.0)
        assert summary["open_count"] == 2
        assert summary["closed_count"] == 0
        expected_btc = 0.00833 + 0.00862
        assert abs(summary["total_btc"] - expected_btc) < 0.00001
        assert summary["total_cost"] == 1000.0
        assert summary["current_value"] == pytest.approx(expected_btc * 75000.0, rel=0.01)
        assert summary["unrealized_pnl"] > 0  # Price went up

    def test_summary_structure(self, empty_state):
        """Summary has all expected keys."""
        summary = get_position_summary(empty_state, 67000.0)
        expected_keys = {
            "open_count", "closed_count", "total_btc", "avg_entry_price",
            "total_cost", "current_value", "unrealized_pnl", "unrealized_pnl_pct",
            "realized_pnl", "total_invested", "last_action", "mode",
        }
        assert set(summary.keys()) == expected_keys

    def test_summary_with_closed_positions(self):
        """Summary includes realized PnL from closed positions."""
        state = {
            "positions": [
                {
                    "btc_qty": 0.01,
                    "usd_amount": 500.0,
                    "entry_price": 50000.0,
                    "exit_price": 60000.0,
                    "status": "closed",
                },
            ],
            "total_invested": 0.0,
            "last_action": None,
            "mode": "paper",
        }
        summary = get_position_summary(state, 67000.0)
        assert summary["closed_count"] == 1
        assert summary["realized_pnl"] == pytest.approx(100.0, rel=0.01)  # 0.01 * 60000 - 500


# ===========================================================================
# State persistence
# ===========================================================================

class TestStatePersistence:
    """Tests for state load/save."""

    def test_load_default_state(self, tmp_state_file):
        """Loading non-existent state returns defaults."""
        state = load_state()
        assert state["positions"] == []
        assert state["total_invested"] == 0.0
        assert state["version"] == 2

    def test_save_and_load_roundtrip(self, tmp_state_file):
        """State survives save→load roundtrip."""
        state = {
            "positions": [{"entry_price": 67000.0, "btc_qty": 0.01, "status": "open"}],
            "total_invested": 500.0,
            "mode": "paper",
            "last_action": "test",
            "version": 2,
        }
        save_state(state)
        loaded = load_state()
        assert loaded == state

    def test_save_creates_directories(self, tmp_path):
        """save_state creates parent directories if needed."""
        nested = tmp_path / "a" / "b" / "state.json"
        executor.STATE_FILE = nested
        try:
            save_state({"positions": [], "total_invested": 0.0})
            assert nested.exists()
        finally:
            executor.STATE_FILE = Path(__file__).parent.parent / "data" / "executor_state.json"


# ===========================================================================
# Integration: full DCA flow
# ===========================================================================

class TestFullDCAFlow:
    """Integration-style tests for the complete DCA cycle."""

    def test_full_paper_dca_cycle(self, empty_state, default_config, tmp_state_file):
        """Full cycle: buy in paper mode → check summary → state persisted."""
        # 1. Buy
        result = execute_dca_buy(67000.0, 8, empty_state, default_config, mode="paper")
        assert "[PAPER]" in result
        assert empty_state["total_invested"] == 500.0

        # 2. Summary
        summary = get_position_summary(empty_state, 70000.0)
        assert summary["open_count"] == 1
        assert summary["unrealized_pnl"] > 0

        # 3. State persisted
        loaded = load_state()
        assert loaded["total_invested"] == 500.0

    def test_multiple_dca_buys(self, empty_state, default_config, tmp_state_file):
        """Multiple DCA buys accumulate correctly."""
        execute_dca_buy(67000.0, 8, empty_state, default_config, mode="paper")
        execute_dca_buy(64000.0, 5, empty_state, default_config, mode="paper")
        execute_dca_buy(62000.0, 3, empty_state, default_config, mode="paper")

        assert len(empty_state["positions"]) == 3
        assert empty_state["total_invested"] == 1500.0

    def test_dca_buy_then_rebalance(self, empty_state, default_config, tmp_state_file):
        """Buy positions, age them, then rebalance sells them."""
        # Buy
        execute_dca_buy(60000.0, 8, empty_state, default_config, mode="paper")

        # Age the position
        old_date = (datetime.now() - timedelta(days=130)).isoformat()
        empty_state["positions"][0]["timestamp"] = old_date

        # Rebalance
        result = execute_rebalance(75000.0, 55, empty_state, default_config, mode="paper")
        assert "REBALANCE" in result
        assert empty_state["positions"][0]["status"] == "closed"


# ===========================================================================
# Market data functions
# ===========================================================================

class TestMarketData:
    """Tests for market data fetching functions."""

    @patch("executor.requests.get")
    def test_get_fear_greed(self, mock_get):
        """get_fear_greed parses API response correctly."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"value": "15", "value_classification": "Extreme Fear"}]
        }
        mock_get.return_value = mock_resp

        result = get_fear_greed()
        assert result["value"] == 15
        assert result["label"] == "Extreme Fear"
        mock_resp.raise_for_status.assert_called_once()

    @patch("executor.requests.get")
    def test_get_btc_price(self, mock_get):
        """get_btc_price parses Binance API response."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"price": "67123.45"}
        mock_get.return_value = mock_resp

        result = get_btc_price()
        assert result == 67123.45
        mock_resp.raise_for_status.assert_called_once()


# ===========================================================================
# HLSpotExecutor — additional methods
# ===========================================================================

class TestHLSpotExecutorMethods:
    """Tests for HLSpotExecutor helper methods."""

    def test_get_ubtc_mid_price(self, mock_hl_executor):
        """get_ubtc_mid_price extracts price from allMids."""
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "67500.5"}
        price = mock_hl_executor.get_ubtc_mid_price()
        assert price == 67500.5

    def test_get_ubtc_mid_price_not_found(self, mock_hl_executor):
        """get_ubtc_mid_price raises when pair missing from mids."""
        mock_hl_executor._client.get_all_mids.return_value = {"BTC": "67000.0"}
        with pytest.raises(ValueError, match="not found"):
            mock_hl_executor.get_ubtc_mid_price()

    def test_get_ubtc_best_ask(self, mock_hl_executor):
        """get_ubtc_best_ask returns the top ask price."""
        mock_hl_executor._client.get_l2_book.return_value = {
            "levels": [
                [{"px": "66900.0", "sz": "1.0", "n": 1}],
                [{"px": "67100.0", "sz": "0.5", "n": 2}],
            ]
        }
        ask = mock_hl_executor.get_ubtc_best_ask()
        assert ask == 67100.0

    def test_get_ubtc_best_ask_empty_book(self, mock_hl_executor):
        """get_ubtc_best_ask raises on empty asks."""
        mock_hl_executor._client.get_l2_book.return_value = {"levels": [[], []]}
        with pytest.raises(ValueError, match="No asks"):
            mock_hl_executor.get_ubtc_best_ask()

    def test_get_spot_meta(self, mock_hl_executor):
        """get_spot_meta delegates to client."""
        mock_hl_executor._client.get_spot_meta.return_value = {"tokens": []}
        result = mock_hl_executor.get_spot_meta()
        assert result == {"tokens": []}

    def test_get_user_fills_with_start_time(self, mock_hl_executor):
        """get_user_fills with start_time uses time-based query."""
        mock_hl_executor._client.get_user_fills_by_time.return_value = [{"fill": 1}]
        result = mock_hl_executor.get_user_fills(start_time=1000000)
        mock_hl_executor._client.get_user_fills_by_time.assert_called_once_with(
            "0xfake_wallet", 1000000
        )
        assert result == [{"fill": 1}]

    def test_get_user_fills_without_start_time(self, mock_hl_executor):
        """get_user_fills without start_time uses default query."""
        mock_hl_executor._client.get_user_fills.return_value = [{"fill": 2}]
        result = mock_hl_executor.get_user_fills()
        mock_hl_executor._client.get_user_fills.assert_called_once_with("0xfake_wallet")
        assert result == [{"fill": 2}]

    def test_close_when_no_client(self):
        """close() is safe when _client is None."""
        ex = HLSpotExecutor.__new__(HLSpotExecutor)
        ex._client = None
        ex.close()  # Should not raise
        assert ex._client is None


# ===========================================================================
# show_status
# ===========================================================================

class TestShowStatus:
    """Tests for show_status()."""

    @patch("executor.get_fear_greed")
    @patch("executor.get_btc_price")
    def test_show_status_empty(self, mock_price, mock_fg, empty_state, capsys):
        """show_status displays info for empty state."""
        mock_price.return_value = 67000.0
        mock_fg.return_value = {"value": 25, "label": "Extreme Fear"}

        show_status(empty_state)
        captured = capsys.readouterr()
        assert "FearHarvester Status" in captured.out
        assert "Open positions: 0" in captured.out
        assert "F&G: 25" in captured.out

    @patch("executor.get_fear_greed")
    @patch("executor.get_btc_price")
    def test_show_status_with_positions(self, mock_price, mock_fg, state_with_positions, capsys):
        """show_status displays open position info."""
        mock_price.return_value = 75000.0
        mock_fg.return_value = {"value": 45, "label": "Fear"}

        show_status(state_with_positions)
        captured = capsys.readouterr()
        assert "Open positions: 2" in captured.out
        assert "Total UBTC:" in captured.out
        assert "Avg entry:" in captured.out
        assert "Unrealized PnL:" in captured.out

    @patch("executor.get_fear_greed")
    @patch("executor.get_btc_price")
    def test_show_status_with_closed_positions(self, mock_price, mock_fg, capsys):
        """show_status displays realized PnL from closed positions."""
        mock_price.return_value = 67000.0
        mock_fg.return_value = {"value": 30, "label": "Fear"}
        state = {
            "positions": [
                {
                    "btc_qty": 0.01,
                    "usd_amount": 500.0,
                    "entry_price": 50000.0,
                    "exit_price": 60000.0,
                    "status": "closed",
                }
            ],
            "total_invested": 0.0,
            "last_action": "test",
            "mode": "paper",
        }
        show_status(state)
        captured = capsys.readouterr()
        assert "Closed positions: 1" in captured.out
        assert "Realized PnL:" in captured.out

    @patch("executor.get_fear_greed", side_effect=Exception("API down"))
    @patch("executor.get_btc_price", side_effect=Exception("API down"))
    def test_show_status_handles_api_errors(self, mock_price, mock_fg, empty_state, capsys):
        """show_status gracefully handles API failures."""
        show_status(empty_state)
        captured = capsys.readouterr()
        assert "FearHarvester Status" in captured.out
        assert "F&G: -1" in captured.out


# ===========================================================================
# main() CLI
# ===========================================================================

class TestMain:
    """Tests for the main() CLI entrypoint."""

    @patch("executor.get_fear_greed")
    @patch("executor.get_btc_price")
    def test_main_dry_run_hold(self, mock_price, mock_fg, tmp_state_file, capsys):
        """main() in dry-run mode with HOLD action."""
        mock_price.return_value = 67000.0
        mock_fg.return_value = {"value": 35, "label": "Fear"}

        with patch("sys.argv", ["executor.py", "--dry-run"]):
            main()

        captured = capsys.readouterr()
        assert "HOLD" in captured.out
        assert "Mode=dry-run" in captured.out

    @patch("executor.get_fear_greed")
    @patch("executor.get_btc_price")
    def test_main_dry_run_buy(self, mock_price, mock_fg, tmp_state_file, capsys):
        """main() in dry-run mode with DCA_BUY action."""
        mock_price.return_value = 67000.0
        mock_fg.return_value = {"value": 8, "label": "Extreme Fear"}

        with patch("sys.argv", ["executor.py", "--dry-run"]):
            main()

        captured = capsys.readouterr()
        assert "DCA_BUY" in captured.out
        assert "DRY RUN" in captured.out

    @patch("executor.get_fear_greed")
    @patch("executor.get_btc_price")
    def test_main_paper_buy(self, mock_price, mock_fg, tmp_state_file, capsys):
        """main() in paper mode with DCA_BUY."""
        mock_price.return_value = 67000.0
        mock_fg.return_value = {"value": 10, "label": "Extreme Fear"}

        with patch("sys.argv", ["executor.py", "--paper"]):
            main()

        captured = capsys.readouterr()
        assert "PAPER" in captured.out

    @patch("executor.show_status")
    def test_main_status(self, mock_show, tmp_state_file):
        """main() --status calls show_status."""
        with patch("sys.argv", ["executor.py", "--status"]):
            main()
        mock_show.assert_called_once()

    @patch("executor.get_fear_greed", side_effect=Exception("API error"))
    def test_main_api_error_exits(self, mock_fg, tmp_state_file):
        """main() exits on market data fetch failure."""
        with patch("sys.argv", ["executor.py", "--dry-run"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("executor.load_hl_credentials", return_value=(None, None))
    def test_main_live_no_credentials_exits(self, mock_creds, tmp_state_file):
        """main() --live exits when no credentials found."""
        with patch("sys.argv", ["executor.py", "--live"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("executor.get_fear_greed")
    @patch("executor.get_btc_price")
    def test_main_rebalance(self, mock_price, mock_fg, tmp_state_file, capsys):
        """main() in paper mode triggers REBALANCE_YIELD when conditions met."""
        mock_price.return_value = 75000.0
        mock_fg.return_value = {"value": 55, "label": "Greed"}

        # Set up state with old positions
        old_date = (datetime.now() - timedelta(days=130)).isoformat()
        state = {
            "positions": [
                {
                    "timestamp": old_date,
                    "entry_price": 60000.0,
                    "btc_qty": 0.00833,
                    "usd_amount": 500.0,
                    "fg_at_entry": 8,
                    "status": "open",
                    "mode": "paper",
                    "hl_order_id": None,
                },
            ],
            "total_invested": 500.0,
            "mode": "paper",
            "last_action": None,
            "version": 2,
        }
        save_state(state)

        with patch("sys.argv", ["executor.py", "--paper", "--hold-days", "120"]):
            main()

        captured = capsys.readouterr()
        assert "REBALANCE" in captured.out


# ===========================================================================
# Edge cases in execute_dca_buy (live resting order)
# ===========================================================================

class TestDCABuyEdgeCases:
    """Edge cases for live DCA buy responses."""

    def test_live_resting_order(self, empty_state, default_config, mock_hl_executor, tmp_state_file):
        """Live buy with resting (not filled) response records oid."""
        mock_hl_executor._client._exchange_request.return_value = {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": [
                        {"resting": {"oid": 54321}}
                    ]
                },
            },
        }
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "67000.0"}

        result = execute_dca_buy(
            67000.0, 10, empty_state, default_config,
            mode="live", hl_executor=mock_hl_executor,
        )
        assert "oid=54321" in result
        assert len(empty_state["positions"]) == 1
        assert empty_state["positions"][0]["hl_order_id"] == "54321"

    def test_live_empty_statuses(self, empty_state, default_config, mock_hl_executor, tmp_state_file):
        """Live buy with empty statuses still records position."""
        mock_hl_executor._client._exchange_request.return_value = {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": []}},
        }
        mock_hl_executor._client.get_all_mids.return_value = {UBTC_PAIR: "67000.0"}

        result = execute_dca_buy(
            67000.0, 10, empty_state, default_config,
            mode="live", hl_executor=mock_hl_executor,
        )
        assert len(empty_state["positions"]) == 1
        assert empty_state["positions"][0]["hl_order_id"] is None


# ===========================================================================
# Rebalance edge: live requires executor
# ===========================================================================

class TestRebalanceEdgeCases:
    """Edge cases for rebalance execution."""

    def test_live_rebalance_requires_executor(self, state_with_positions, default_config, tmp_state_file):
        """Live rebalance without executor raises ValueError."""
        old_date = (datetime.now() - timedelta(days=130)).isoformat()
        for p in state_with_positions["positions"]:
            p["timestamp"] = old_date

        with pytest.raises(ValueError, match="HLSpotExecutor required"):
            execute_rebalance(
                75000.0, 55, state_with_positions, default_config, mode="live"
            )
