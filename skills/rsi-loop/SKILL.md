
---

## Doom Loop Detector — Pre-Flight Tool-Call Guard

The Doom Loop Detector (`scripts/doom_loop_detector.py`) is a pre-flight guard that
detects pathological agent patterns before each tool call and issues corrective guidance.

### Detection Patterns

| Pattern | Trigger | Severity |
|---------|---------|----------|
| `loop` | Same tool + **identical** args ≥ 3× in window | `abort` |
| `soft_loop` | Same tool + **similar** args (Jaccard > 0.85) ≥ 4× | `warning` |
| `flailing` | ≥ 3 **consecutive errors** from same tool | `abort` |
| `emergency_abort` | Context < 20% remaining **AND** last 5 calls all errored | `abort` |

After `abort_after_k_detections` (default: 2) total detections in a session, any
subsequent detection is escalated to `abort` regardless of pattern severity.

### Quick Start

```python
from scripts.doom_loop_detector import check_before_tool_call, reset_session_counter

# Before each tool call:
result = check_before_tool_call(
    session_id="sess-abc123",
    planned_tool="read_file",
    planned_args={"path": "/tmp/data.txt"},
    recent_history=recent_tool_calls,      # list of dicts or ToolCallRecord objects
    context_used_tokens=8500,
    context_total_tokens=10000,
)

if result["should_abort"]:
    raise RuntimeError(result["corrective_message"])
elif result["detected"]:
    print(f"Warning: {result['corrective_message']}")
```

**Return shape** (`DetectionResult`):
```json
{
  "detected": true,
  "pattern": "loop",
  "severity": "abort",
  "corrective_message": "🔁 Doom Loop detected — you've called `read_file` with identical args 3 times...",
  "should_abort": true
}
```

### History Record Format

Each entry in `recent_history` can be a dict with any of these key aliases:

```json
{
  "tool": "exec",            // or "tool_name"
  "args": {"cmd": "ls"},     // or "arguments", "input"
  "errored": false,          // or "error", "is_error"
  "timestamp": 1714000000.0  // optional
}
```

### Configuration (`memory/doom-loop-config.json`)

```json
{
  "window_size": 10,
  "identical_threshold": 3,
  "similar_threshold": 4,
  "jaccard_threshold": 0.85,
  "consecutive_error_threshold": 3,
  "context_emergency_pct": 0.20,
  "abort_after_k_detections": 2
}
```

Set env var `DOOM_LOOP_CONFIG=/path/to/config.json` to use a custom path.

### WAL Integration

If `recent_history=None`, the detector reads from agent-self-governance WAL automatically,
searching: `memory/wal-<session_id>.jsonl`, `memory/wal.jsonl`, `memory/wal/<session_id>.jsonl`.

### Telemetry

Every detection emits a `doom_loop_detected` fact to clawmemory:
```
POST http://localhost:7437/api/v1/facts
{"content": "doom_loop_detected: session=<id> pattern=<p> tool=<t> count=<n> ts=<unix>",
 "tags": ["doom_loop", "rsi", "pattern:<p>", "tool:<t>"]}
```

Query: `curl -s "http://localhost:7437/api/v1/facts?q=doom_loop_detected&limit=20"`

### Running Tests

```bash
uv run python -m pytest skills/rsi-loop/tests/test_doom_loop_detector.py -v
```
