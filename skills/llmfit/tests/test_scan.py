"""
Tests for skills/llmfit/scripts/scan.py

Run with:
    uv run python -m pytest skills/llmfit/tests/test_scan.py -v
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make sure the skill scripts are importable
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import scan  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_LLMFIT_JSON = {
    "models": [
        {
            "best_quant": "Q8_0",
            "category": "Coding",
            "context_length": 131072,
            "estimated_tps": 25.4,
            "fit_level": "Perfect",
            "is_moe": False,
            "memory_available_gb": 24.0,
            "memory_required_gb": 16.48,
            "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            "notes": ["GPU: model loaded into VRAM"],
            "parameter_count": "7.6B",
            "params_b": 7.62,
            "provider": "DeepSeek",
            "release_date": "2025-01-20",
            "run_mode": "GPU",
            "runtime": "llama.cpp",
            "runtime_label": "llama.cpp",
            "score": 87.4,
            "score_components": {"context": 100.0, "fit": 100.0, "quality": 77.0, "speed": 100.0},
            "use_case": "Reasoning",
            "utilization_pct": 68.7,
        },
        {
            "best_quant": "Q4_K_M",
            "category": "Chat",
            "context_length": 32768,
            "estimated_tps": 5.1,
            "fit_level": "Marginal",
            "is_moe": False,
            "memory_available_gb": 8.0,
            "memory_required_gb": 22.0,
            "name": "meta-llama/Llama-3.3-70B-Instruct",
            "notes": ["CPU offload required"],
            "parameter_count": "70B",
            "params_b": 70.0,
            "provider": "Meta",
            "release_date": "2024-12-01",
            "run_mode": "CPU+GPU",
            "runtime": "llama.cpp",
            "runtime_label": "llama.cpp",
            "score": 45.0,
            "score_components": {"context": 100.0, "fit": 25.0, "quality": 90.0, "speed": 30.0},
            "use_case": "Instruction following",
            "utilization_pct": 100.0,
        },
    ]
}

SAMPLE_SYSTEM_TEXT = """\
=== System Specifications ===
CPU: Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz (16 cores)
Total RAM: 15.29 GB
Available RAM: 10.71 GB
Backend: CUDA
GPU: NVIDIA GeForce RTX 3090 (24.00 GB VRAM, CUDA)
GPU: NVIDIA GeForce RTX 3080 (10.00 GB VRAM, CUDA)
"""


# ---------------------------------------------------------------------------
# parse_system_info
# ---------------------------------------------------------------------------

class TestParseSystemInfo:
    def test_basic_parse(self):
        result = scan.parse_system_info(SAMPLE_SYSTEM_TEXT)
        assert result["cpu"] == "Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz (16 cores)"
        assert result["ram_gb"] == 15.3  # round(15.29, 1) == 15.3
        assert result["ram_available_gb"] == 10.7  # round(10.71, 1) == 10.7
        assert result["backend"] == "CUDA"
        assert len(result["gpus"]) == 2
        assert "RTX 3090" in result["gpus"][0]

    def test_empty_text(self):
        result = scan.parse_system_info("")
        assert result["gpus"] == []
        assert "cpu" not in result

    def test_no_gpu(self):
        text = "CPU: Ryzen 9\nTotal RAM: 64.00 GB\nAvailable RAM: 48.00 GB\nBackend: CPU"
        result = scan.parse_system_info(text)
        assert result["gpus"] == []
        assert result["backend"] == "CPU"
        assert result["ram_gb"] == 64.0


# ---------------------------------------------------------------------------
# normalise_model
# ---------------------------------------------------------------------------

class TestNormaliseModel:
    def test_perfect_fit(self):
        raw = SAMPLE_LLMFIT_JSON["models"][0]
        m = scan.normalise_model(raw)
        assert m["fit"] == "perfect"
        assert m["fit_level"] == "Perfect"
        assert m["name"] == "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        assert m["score"] == 87.4
        assert m["tok_s"] == 25.4
        assert m["quant"] == "Q8_0"

    def test_marginal_fit(self):
        raw = SAMPLE_LLMFIT_JSON["models"][1]
        m = scan.normalise_model(raw)
        assert m["fit"] == "marginal"
        assert m["fit_level"] == "Marginal"
        assert m["params_b"] == 70.0

    def test_no_fit_mapping(self):
        raw = {"fit_level": "No Fit", "name": "giant-model", "score": 0.0}
        m = scan.normalise_model(raw)
        assert m["fit"] == "none"

    def test_nofit_compact(self):
        raw = {"fit_level": "NoFit", "name": "huge-model", "score": 0.0}
        m = scan.normalise_model(raw)
        assert m["fit"] == "none"

    def test_unknown_fit_level(self):
        raw = {"fit_level": "SomethingNew", "name": "model", "score": 50.0}
        m = scan.normalise_model(raw)
        # Falls back to lowercased version
        assert m["fit"] == "somethingnew"

    def test_missing_fields_are_none(self):
        m = scan.normalise_model({})
        assert m["name"] == ""
        assert m["score"] is None
        assert m["tok_s"] is None


# ---------------------------------------------------------------------------
# run_local_scan (mocked subprocess)
# ---------------------------------------------------------------------------

class TestRunLocalScan:
    def test_success(self, tmp_path, monkeypatch):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(SAMPLE_LLMFIT_JSON)

        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        models = scan.run_local_scan(limit=5)
        assert len(models) == 2
        assert models[0]["name"] == "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

    def test_failure_raises(self, monkeypatch):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "llmfit error"

        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        with pytest.raises(RuntimeError, match="llmfit recommend failed locally"):
            scan.run_local_scan()

    def test_empty_models(self, monkeypatch):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"models": []})

        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
        models = scan.run_local_scan()
        assert models == []


# ---------------------------------------------------------------------------
# load_existing / save
# ---------------------------------------------------------------------------

class TestLoadSave:
    def test_load_missing_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(scan, "HARDWARE_FITS_FILE", tmp_path / "nope.json")
        result = scan.load_existing()
        assert result == {"scanned_at": None, "hosts": {}}

    def test_load_existing_file(self, tmp_path, monkeypatch):
        fits_file = tmp_path / "hardware_fits.json"
        data = {"scanned_at": "2026-01-01", "hosts": {"local": {"models": []}}}
        fits_file.write_text(json.dumps(data))

        monkeypatch.setattr(scan, "HARDWARE_FITS_FILE", fits_file)
        result = scan.load_existing()
        assert result["scanned_at"] == "2026-01-01"

    def test_save_creates_file(self, tmp_path, monkeypatch):
        fits_file = tmp_path / "data" / "hardware_fits.json"
        monkeypatch.setattr(scan, "HARDWARE_FITS_FILE", fits_file)
        monkeypatch.setattr(scan, "DATA_DIR", tmp_path / "data")

        data = {"scanned_at": "2026-02-26", "hosts": {}}
        scan.save(data)

        assert fits_file.exists()
        loaded = json.loads(fits_file.read_text())
        assert loaded["scanned_at"] == "2026-02-26"


# ---------------------------------------------------------------------------
# Integration: scan_local with all mocks
# ---------------------------------------------------------------------------

class TestScanLocal:
    def test_scan_local_end_to_end(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            r = MagicMock()
            r.returncode = 0
            if "system" in cmd:
                r.stdout = SAMPLE_SYSTEM_TEXT
            else:
                r.stdout = json.dumps(SAMPLE_LLMFIT_JSON)
            return r

        monkeypatch.setattr(subprocess, "run", fake_run)
        result = scan.scan_local(limit=10, verbose=False)

        assert "system" in result
        assert "models" in result
        assert result["system"]["backend"] == "CUDA"
        assert len(result["models"]) == 2
        # Check normalisation was applied
        assert result["models"][0]["fit"] in ("perfect", "good", "marginal", "none", "unknown")


# ---------------------------------------------------------------------------
# FIT_LEVEL_MAP completeness
# ---------------------------------------------------------------------------

class TestFitLevelMap:
    def test_all_expected_levels_present(self):
        for level in ("Perfect", "Good", "Marginal", "No Fit"):
            assert level in scan.FIT_LEVEL_MAP, f"Missing fit level: {level}"

    def test_values_are_canonical(self):
        allowed = {"perfect", "good", "marginal", "none"}
        for val in scan.FIT_LEVEL_MAP.values():
            assert val in allowed, f"Non-canonical fit value: {val}"
