"""
Tests for skills/llmfit/scripts/query.py

Run with:
    uv run python -m pytest skills/llmfit/tests/test_query.py -v
"""

import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import query  # noqa: E402


# ---------------------------------------------------------------------------
# Sample cache fixture
# ---------------------------------------------------------------------------

SAMPLE_CACHE = {
    "scanned_at": "2026-02-26T17:00:00+11:00",
    "hosts": {
        "local": {
            "system": {"cpu": "i7-10700K", "ram_gb": 15.29, "gpus": ["RTX 3070 8GB"]},
            "models": [
                {
                    "name": "Qwen/Qwen2.5-3B-Instruct",
                    "provider": "Alibaba",
                    "score": 84.8,
                    "fit": "perfect",
                    "fit_level": "Perfect",
                    "quant": "Q8_0",
                    "mem_required_gb": 4.55,
                    "mem_available_gb": 8.0,
                    "utilization_pct": 56.9,
                    "tok_s": 62.7,
                    "run_mode": "GPU",
                    "params_b": 3.09,
                    "parameter_count": "3.1B",
                    "category": "Chat",
                    "context_length": 32768,
                    "runtime": "llama.cpp",
                    "score_components": {"context": 100.0, "fit": 100.0, "quality": 62.0, "speed": 100.0},
                    "notes": ["GPU: model loaded into VRAM"],
                },
                {
                    "name": "meta-llama/Llama-3.3-70B-Instruct",
                    "provider": "Meta",
                    "score": 45.0,
                    "fit": "marginal",
                    "fit_level": "Marginal",
                    "quant": "Q4_K_M",
                    "mem_required_gb": 22.0,
                    "mem_available_gb": 8.0,
                    "utilization_pct": 100.0,
                    "tok_s": 5.1,
                    "run_mode": "CPU+GPU",
                    "params_b": 70.0,
                    "parameter_count": "70B",
                    "category": "Chat",
                    "context_length": 131072,
                    "runtime": "llama.cpp",
                    "score_components": {"context": 100.0, "fit": 25.0, "quality": 90.0, "speed": 30.0},
                    "notes": ["CPU offload required"],
                },
            ],
        },
        "gpu-server": {
            "system": {
                "cpu": "Ryzen 9",
                "ram_gb": 16.0,
                "swap_gb": 256,
                "gpus": ["RTX 3090 24GB", "RTX 3080 10GB", "RTX 2070S 8GB"],
            },
            "models": [
                {
                    "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                    "provider": "DeepSeek",
                    "score": 87.4,
                    "fit": "perfect",
                    "fit_level": "Perfect",
                    "quant": "Q8_0",
                    "mem_required_gb": 16.48,
                    "mem_available_gb": 24.0,
                    "utilization_pct": 68.7,
                    "tok_s": 25.4,
                    "run_mode": "GPU",
                    "params_b": 7.62,
                    "parameter_count": "7.6B",
                    "category": "Reasoning",
                    "context_length": 131072,
                    "runtime": "llama.cpp",
                    "score_components": {"context": 100.0, "fit": 100.0, "quality": 77.0, "speed": 100.0},
                    "notes": ["GPU: model loaded into VRAM"],
                },
                {
                    "name": "meta-llama/Llama-3.3-70B-Instruct",
                    "provider": "Meta",
                    "score": 78.0,
                    "fit": "good",
                    "fit_level": "Good",
                    "quant": "Q4_K_M",
                    "mem_required_gb": 22.0,
                    "mem_available_gb": 24.0,
                    "utilization_pct": 91.7,
                    "tok_s": 12.5,
                    "run_mode": "GPU",
                    "params_b": 70.0,
                    "parameter_count": "70B",
                    "category": "Chat",
                    "context_length": 131072,
                    "runtime": "llama.cpp",
                    "score_components": {"context": 100.0, "fit": 80.0, "quality": 90.0, "speed": 60.0},
                    "notes": [],
                },
            ],
        },
    },
}


# ---------------------------------------------------------------------------
# search_models
# ---------------------------------------------------------------------------

class TestSearchModels:
    def test_exact_substring_match(self):
        results = query.search_models(SAMPLE_CACHE, "qwen")
        assert len(results) == 2  # Qwen2.5-3B on local + DeepSeek-R1-Qwen on gpu-server
        names = [r["name"] for r in results]
        assert "Qwen/Qwen2.5-3B-Instruct" in names

    def test_case_insensitive(self):
        results = query.search_models(SAMPLE_CACHE, "LLAMA")
        # 1 Llama on local + 1 Llama on gpu-server = 2 (DeepSeek-Distill-Qwen has no "llama")
        assert len(results) == 2

    def test_filter_by_host_local(self):
        results = query.search_models(SAMPLE_CACHE, "llama", host="local")
        assert len(results) == 1
        assert results[0]["host"] == "local"

    def test_filter_by_host_gpu_server(self):
        results = query.search_models(SAMPLE_CACHE, "llama", host="gpu-server")
        assert all(r["host"] == "gpu-server" for r in results)

    def test_no_match(self):
        results = query.search_models(SAMPLE_CACHE, "does-not-exist-xyz")
        assert results == []

    def test_result_includes_host_key(self):
        results = query.search_models(SAMPLE_CACHE, "deepseek")
        assert all("host" in r for r in results)

    def test_empty_cache(self):
        empty = {"hosts": {}}
        results = query.search_models(empty, "llama")
        assert results == []

    def test_model_key_not_shared_with_name(self):
        # Confirm 'host' isn't clobbering original model keys
        results = query.search_models(SAMPLE_CACHE, "qwen2.5-3b")
        assert len(results) == 1
        r = results[0]
        assert r["fit"] == "perfect"
        assert r["score"] == 84.8


# ---------------------------------------------------------------------------
# list_all_models
# ---------------------------------------------------------------------------

class TestListAllModels:
    def test_all_hosts(self):
        results = query.list_all_models(SAMPLE_CACHE)
        assert len(results) == 4  # 2 local + 2 gpu-server

    def test_host_filter(self):
        results = query.list_all_models(SAMPLE_CACHE, host="local")
        assert len(results) == 2
        assert all(r["host"] == "local" for r in results)

    def test_gpu_server_filter(self):
        results = query.list_all_models(SAMPLE_CACHE, host="gpu-server")
        assert len(results) == 2

    def test_unknown_host_returns_empty(self):
        results = query.list_all_models(SAMPLE_CACHE, host="nonexistent")
        assert results == []


# ---------------------------------------------------------------------------
# format_result
# ---------------------------------------------------------------------------

class TestFormatResult:
    def test_perfect_fit_emoji(self):
        r = {"host": "local", "name": "SomeModel", "score": 90, "fit": "perfect",
             "fit_level": "Perfect", "quant": "Q8_0", "run_mode": "GPU",
             "mem_required_gb": 4.0, "mem_available_gb": 8.0,
             "tok_s": 50.0, "utilization_pct": 50, "parameter_count": "3B",
             "category": "Chat", "notes": []}
        text = query.format_result(r)
        assert "✅" in text
        assert "SomeModel" in text

    def test_marginal_fit_emoji(self):
        r = {"host": "local", "name": "BigModel", "score": 30, "fit": "marginal",
             "fit_level": "Marginal", "quant": "Q4_K_M", "run_mode": "CPU+GPU",
             "mem_required_gb": 22.0, "mem_available_gb": 8.0,
             "tok_s": 5.0, "utilization_pct": 100, "parameter_count": "70B",
             "category": "Chat", "notes": ["CPU offload"]}
        text = query.format_result(r)
        assert "⚠️" in text
        assert "CPU offload" in text

    def test_none_fit_emoji(self):
        r = {"host": "local", "name": "HugeModel", "score": 0, "fit": "none",
             "fit_level": "No Fit", "quant": "", "run_mode": "N/A",
             "mem_required_gb": 200, "mem_available_gb": 8,
             "tok_s": 0, "utilization_pct": None, "parameter_count": "1T",
             "category": "Chat", "notes": []}
        text = query.format_result(r)
        assert "❌" in text

    def test_notes_displayed(self):
        r = {"host": "gpu-server", "name": "M", "score": 80, "fit": "good",
             "fit_level": "Good", "quant": "Q4", "run_mode": "GPU",
             "mem_required_gb": 10, "mem_available_gb": 24,
             "tok_s": 20, "utilization_pct": 60, "parameter_count": "7B",
             "category": "Reasoning", "notes": ["note A", "note B"]}
        text = query.format_result(r)
        assert "note A" in text
        assert "note B" in text

    def test_no_notes_still_renders(self):
        r = {"host": "local", "name": "M", "score": 80, "fit": "good",
             "fit_level": "Good", "quant": "Q4", "run_mode": "GPU",
             "mem_required_gb": 8, "mem_available_gb": 8,
             "tok_s": 20, "utilization_pct": 80, "parameter_count": "7B",
             "category": "Chat", "notes": []}
        text = query.format_result(r)
        assert isinstance(text, str)
        assert len(text) > 0


# ---------------------------------------------------------------------------
# load_cache (mocked path)
# ---------------------------------------------------------------------------

class TestLoadCache:
    def test_missing_file_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr(query, "HARDWARE_FITS_FILE", tmp_path / "nope.json")
        with pytest.raises(SystemExit):
            query.load_cache()

    def test_loads_valid_json(self, tmp_path, monkeypatch):
        fits_file = tmp_path / "hardware_fits.json"
        fits_file.write_text(json.dumps(SAMPLE_CACHE))
        monkeypatch.setattr(query, "HARDWARE_FITS_FILE", fits_file)
        cache = query.load_cache()
        assert "hosts" in cache
        assert "scanned_at" in cache


# ---------------------------------------------------------------------------
# min_score and fit filters
# ---------------------------------------------------------------------------

class TestFilters:
    def test_min_score_filters(self):
        results = query.list_all_models(SAMPLE_CACHE)
        filtered = [r for r in results if (r.get("score") or 0) >= 80]
        scores = [r["score"] for r in filtered]
        assert all(s >= 80 for s in scores)

    def test_fit_filter(self):
        results = query.list_all_models(SAMPLE_CACHE)
        marginal_only = [r for r in results if r.get("fit") == "marginal"]
        assert len(marginal_only) == 1
        assert marginal_only[0]["name"] == "meta-llama/Llama-3.3-70B-Instruct"
        assert marginal_only[0]["host"] == "local"
