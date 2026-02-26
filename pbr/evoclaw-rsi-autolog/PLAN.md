# PLAN: Wire EvoClaw Tool Loop → RSI Auto-Logging

**Branch:** `feat/toolloop-rsi-autolog`
**Base:** `main`
**Repo:** `clawinfra/evoclaw`

## 1. File Structure

### New Files
- `internal/orchestrator/rsi_logger.go` — RSILogger interface, NoopRSILogger, JSONLRSILogger, RSIOutcome struct, derivation helpers
- `internal/orchestrator/rsi_logger_test.go` — all tests

### Modified Files
- `internal/orchestrator/toolloop.go` — add `rsiLogger` field, `WithRSILogger` option, wire into `Execute()`

## 2. Interface & Struct Definitions

### `internal/orchestrator/rsi_logger.go`

```go
package orchestrator

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// RSIOutcome is the JSONL record written to the RSI outcomes file.
// Field names match the OpenClaw RSI skill schema exactly.
type RSIOutcome struct {
	ID         string   `json:"id"`
	Timestamp  string   `json:"ts"`
	AgentID    string   `json:"agent_id"`
	SessionID  string   `json:"session_id,omitempty"`
	Source     string   `json:"source"`
	TaskType   string   `json:"task_type"`
	Model      string   `json:"model"`
	Success    bool     `json:"success"`
	Quality    int      `json:"quality"`
	DurationMs int64    `json:"duration_ms"`
	Issues     []string `json:"issues"`
	Tags       []string `json:"tags"`
	Notes      string   `json:"notes"`
}

// RSILogger writes RSI outcomes after tool loop execution.
type RSILogger interface {
	LogOutcome(ctx context.Context, outcome RSIOutcome) error
}

// --- NoopRSILogger ---

// NoopRSILogger silently discards all outcomes. Zero-value is ready to use.
type NoopRSILogger struct{}

func (NoopRSILogger) LogOutcome(_ context.Context, _ RSIOutcome) error { return nil }

// --- JSONLRSILogger ---

// JSONLRSILogger appends JSON lines to a file.
type JSONLRSILogger struct {
	Path string
}

// NewJSONLRSILogger creates a logger that writes to path.
// If the parent directory of path does not exist, returns NoopRSILogger (graceful degradation).
func NewJSONLRSILogger(path string) RSILogger {
	dir := filepath.Dir(path)
	info, err := os.Stat(dir)
	if err != nil || !info.IsDir() {
		return NoopRSILogger{}
	}
	return &JSONLRSILogger{Path: path}
}

func (l *JSONLRSILogger) LogOutcome(_ context.Context, outcome RSIOutcome) error {
	if outcome.ID == "" {
		b := make([]byte, 4)
		_, _ = rand.Read(b)
		outcome.ID = hex.EncodeToString(b)
	}
	if outcome.Timestamp == "" {
		outcome.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}
	if outcome.Issues == nil {
		outcome.Issues = []string{}
	}
	if outcome.Tags == nil {
		outcome.Tags = []string{}
	}

	data, err := json.Marshal(outcome)
	if err != nil {
		return fmt.Errorf("marshal RSI outcome: %w", err)
	}

	f, err := os.OpenFile(l.Path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return fmt.Errorf("open RSI outcomes file: %w", err)
	}
	defer f.Close()

	_, err = f.Write(append(data, '\n'))
	return err
}

// --- Derivation helpers ---

// DeriveQuality returns 1-5 from error rate (ErrorCount / ToolCallCount).
//
//	0 errors        → 5
//	<20% error rate → 4
//	<50%            → 3
//	<80%            → 2
//	≥80%            → 1
//
// If ToolCallCount == 0, returns 5 (no tools = no errors).
func DeriveQuality(errorCount, toolCallCount int) int {
	if toolCallCount == 0 || errorCount == 0 {
		return 5
	}
	rate := float64(errorCount) / float64(toolCallCount)
	switch {
	case rate < 0.20:
		return 4
	case rate < 0.50:
		return 3
	case rate < 0.80:
		return 2
	default:
		return 1
	}
}

// DeriveTaskType infers task_type from the set of tool names used in the loop.
// Rules (first match wins):
//
//	contains "bash","execute","shell","exec"    → "code_generation"
//	contains "read_file","list_files","glob","grep" → "file_ops"
//	contains "write_file","edit_file"           → "code_generation"
//	contains "websearch","webfetch"             → "web_search"
//	contains "git_commit","git_diff","git_log"  → "code_review"
//	contains "edge_call"                        → "infrastructure_ops"
//	otherwise                                   → "unknown"
func DeriveTaskType(toolNames []string) string {
	set := make(map[string]bool, len(toolNames))
	for _, n := range toolNames {
		set[strings.ToLower(n)] = true
	}

	// Execution tools → code_generation
	for _, t := range []string{"bash", "execute", "shell", "exec"} {
		if set[t] {
			return "code_generation"
		}
	}
	// Write/edit → code_generation
	for _, t := range []string{"write_file", "edit_file"} {
		if set[t] {
			return "code_generation"
		}
	}
	// Read-only file tools → file_ops
	for _, t := range []string{"read_file", "list_files", "glob", "grep"} {
		if set[t] {
			return "file_ops"
		}
	}
	// Web tools
	for _, t := range []string{"websearch", "webfetch"} {
		if set[t] {
			return "web_search"
		}
	}
	// Git tools
	for _, t := range []string{"git_commit", "git_diff", "git_log"} {
		if set[t] {
			return "code_review"
		}
	}
	// Edge
	if set["edge_call"] {
		return "infrastructure_ops"
	}

	return "unknown"
}

// DefaultRSILoggerPath resolves the outcomes file path:
//  1. env var RSI_OUTCOMES_FILE
//  2. ~/.openclaw/workspace/skills/rsi-loop/data/outcomes.jsonl
//
// Returns "" if neither path's parent dir exists.
func DefaultRSILoggerPath() string {
	if p := os.Getenv("RSI_OUTCOMES_FILE"); p != "" {
		dir := filepath.Dir(p)
		if info, err := os.Stat(dir); err == nil && info.IsDir() {
			return p
		}
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	p := filepath.Join(home, ".openclaw", "workspace", "skills", "rsi-loop", "data", "outcomes.jsonl")
	dir := filepath.Dir(p)
	if info, err := os.Stat(dir); err == nil && info.IsDir() {
		return p
	}

	return ""
}

// NewDefaultRSILogger creates a logger using DefaultRSILoggerPath().
// Returns NoopRSILogger if no valid path is found.
func NewDefaultRSILogger() RSILogger {
	p := DefaultRSILoggerPath()
	if p == "" {
		return NoopRSILogger{}
	}
	return &JSONLRSILogger{Path: p}
}
```

## 3. Quality Derivation Logic

| ErrorCount / ToolCallCount | Quality |
|---|---|
| 0 (or no tools) | 5 |
| (0, 0.20) | 4 |
| [0.20, 0.50) | 3 |
| [0.50, 0.80) | 2 |
| [0.80, 1.0] | 1 |

`success` = `metrics.ErrorCount == 0`

## 4. Task Type Inference

Priority order (first match):
1. `bash/execute/shell/exec` → `code_generation`
2. `write_file/edit_file` → `code_generation`
3. `read_file/list_files/glob/grep` → `file_ops`
4. `websearch/webfetch` → `web_search`
5. `git_commit/git_diff/git_log` → `code_review`
6. `edge_call` → `infrastructure_ops`
7. fallback → `unknown`

Tool names are collected from all `ToolCall.Name` values across all iterations.

## 5. Wire-Up in `Execute()`

### Changes to `toolloop.go`

**Add field to ToolLoop struct:**
```go
type ToolLoop struct {
	// ... existing fields ...
	rsiLogger  RSILogger
}
```

**Add functional option:**
```go
// ToolLoopOption configures a ToolLoop.
type ToolLoopOption func(*ToolLoop)

// WithRSILogger sets the RSI logger for outcome recording.
func WithRSILogger(logger RSILogger) ToolLoopOption {
	return func(tl *ToolLoop) {
		tl.rsiLogger = logger
	}
}
```

**Update NewToolLoop signature:**
```go
func NewToolLoop(orch *Orchestrator, tm *ToolManager, opts ...ToolLoopOption) *ToolLoop {
	tl := &ToolLoop{
		orchestrator:   orch,
		toolManager:    tm,
		logger:         orch.logger.With("component", "tool_loop"),
		maxIterations:  10,
		errorLimit:     3,
		defaultTimeout: 30 * time.Second,
		maxParallel:    5,
		rsiLogger:      NoopRSILogger{}, // default
	}
	for _, opt := range opts {
		opt(tl)
	}
	return tl
}
```

**Wire into Execute() — at the top, add wall-time measurement and tool name collection; at the end, defer the log call:**

```go
func (tl *ToolLoop) Execute(agent *AgentState, msg Message, model string) (*Response, *ToolLoopMetrics, error) {
	startTime := time.Now()
	metrics := &ToolLoopMetrics{}
	var allToolNames []string // NEW: collect tool names for task_type inference

	// ... existing code ...

	// Inside the tool call loop, after building batchResults, collect names:
	// (add after the "for _, pr := range batchResults" loop)
	for _, call := range toolCalls {
		allToolNames = append(allToolNames, call.Name)  // NEW
	}

	// ... rest of existing loop code ...

	metrics.TotalDuration = time.Since(startTime)

	// --- NEW: RSI outcome logging (always runs, even on error paths) ---
	wallMs := time.Since(startTime).Milliseconds()
	rsiOutcome := RSIOutcome{
		Source:     "evoclaw",
		AgentID:    agent.ID,
		Model:      model,
		Success:    metrics.ErrorCount == 0,
		Quality:    DeriveQuality(metrics.ErrorCount, metrics.ToolCalls),
		DurationMs: wallMs,
		TaskType:   DeriveTaskType(allToolNames),
		Notes:      fmt.Sprintf("%d tool calls, %d parallel batches", metrics.ToolCalls, metrics.ParallelBatches),
		Tags:       []string{"toolloop"},
	}
	if metrics.ParallelBatches > 0 {
		rsiOutcome.Tags = append(rsiOutcome.Tags, "parallel")
	}
	if logErr := tl.rsiLogger.LogOutcome(context.Background(), rsiOutcome); logErr != nil {
		tl.logger.Warn("failed to log RSI outcome", "error", logErr)
	}
	// --- END NEW ---

	// ... existing summary + return code ...
}
```

**Exact placement:** The RSI logging block goes **after** `metrics.TotalDuration = time.Since(startTime)` and **before** the `if needsSummary || finalContent == ""` block. This ensures metrics are fully populated. We do NOT use defer because we need the populated metrics.

**For error returns** (e.g., `too many consecutive errors`): Add RSI logging before each early `return nil, nil, fmt.Errorf(...)`. Specifically:
- Before the `"generate tool schemas"` error return — skip (no metrics yet)
- Before `"call LLM"` error return — log with what we have
- Before `"too many consecutive errors"` return — log with accumulated metrics

Pattern for error paths:
```go
// Before error return:
tl.logRSIOutcome(agent.ID, model, metrics, allToolNames, time.Since(startTime))
return nil, nil, fmt.Errorf(...)
```

**Add helper method:**
```go
func (tl *ToolLoop) logRSIOutcome(agentID, model string, metrics *ToolLoopMetrics, toolNames []string, elapsed time.Duration) {
	outcome := RSIOutcome{
		Source:     "evoclaw",
		AgentID:    agentID,
		Model:      model,
		Success:    metrics.ErrorCount == 0,
		Quality:    DeriveQuality(metrics.ErrorCount, metrics.ToolCalls),
		DurationMs: elapsed.Milliseconds(),
		TaskType:   DeriveTaskType(toolNames),
		Notes:      fmt.Sprintf("%d tool calls, %d parallel batches", metrics.ToolCalls, metrics.ParallelBatches),
		Tags:       []string{"toolloop"},
	}
	if metrics.ParallelBatches > 0 {
		outcome.Tags = append(outcome.Tags, "parallel")
	}
	if err := tl.rsiLogger.LogOutcome(context.Background(), outcome); err != nil {
		tl.logger.Warn("failed to log RSI outcome", "error", err)
	}
}
```

Then replace inline RSI blocks with `tl.logRSIOutcome(agent.ID, model, metrics, allToolNames, time.Since(startTime))` at each exit point.

## 6. Path Discovery Logic

```
1. Check os.Getenv("RSI_OUTCOMES_FILE")
   → if set AND parent dir exists → use it
2. Else: ~/.openclaw/workspace/skills/rsi-loop/data/outcomes.jsonl
   → if parent dir exists → use it
3. Else: return NoopRSILogger (no error, no file created)
```

The parent dir must already exist. We never create it — that's the RSI skill's responsibility.

## 7. Test Plan

### `internal/orchestrator/rsi_logger_test.go`

```go
package orchestrator

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)
```

#### `TestJSONLRSILogger_WritesRecord`
- Create temp dir, instantiate `JSONLRSILogger{Path: tempdir/outcomes.jsonl}`
- Call `LogOutcome` with a fully populated RSIOutcome
- Read file, unmarshal JSON line, assert all fields match
- Verify `id` and `ts` are auto-populated if empty

#### `TestJSONLRSILogger_AppendsNotOverwrites`
- Create temp dir, write two outcomes via `LogOutcome`
- Read file, count lines == 2
- Parse both lines, verify both records present

#### `TestJSONLRSILogger_NoopWhenPathMissing`
- Call `NewJSONLRSILogger("/nonexistent/dir/outcomes.jsonl")`
- Assert returned type is `NoopRSILogger`
- Call `LogOutcome` — no error, no file created

#### `TestQualityDerivation`
Table-driven:
```go
{errorCount: 0, toolCount: 10, want: 5},
{errorCount: 1, toolCount: 10, want: 4},  // 10% < 20%
{errorCount: 3, toolCount: 10, want: 3},  // 30% < 50%
{errorCount: 6, toolCount: 10, want: 2},  // 60% < 80%
{errorCount: 9, toolCount: 10, want: 1},  // 90% ≥ 80%
{errorCount: 0, toolCount: 0, want: 5},   // no tools
{errorCount: 2, toolCount: 10, want: 4},  // 20% boundary → 4 (< 0.20 is strict)
```

#### `TestTaskTypeInference`
Table-driven:
```go
{tools: []string{"bash"}, want: "code_generation"},
{tools: []string{"read_file", "grep"}, want: "file_ops"},
{tools: []string{"write_file"}, want: "code_generation"},
{tools: []string{"websearch"}, want: "web_search"},
{tools: []string{"git_commit"}, want: "code_review"},
{tools: []string{"edge_call"}, want: "infrastructure_ops"},
{tools: []string{"unknown_tool"}, want: "unknown"},
{tools: []string{}, want: "unknown"},
{tools: []string{"bash", "read_file"}, want: "code_generation"}, // bash wins
```

#### `TestToolLoop_LogsOutcomeOnSuccess`
- Create a ToolLoop with a mock RSILogger that captures the outcome
- Set `execFunc` to return success results
- Call `Execute()` with a simple message
- Assert `LogOutcome` was called exactly once
- Assert `outcome.Success == true`, `outcome.Quality == 5`, `outcome.Source == "evoclaw"`

#### `TestToolLoop_LogsOutcomeOnFailure`
- Same setup but `execFunc` returns errors
- Assert `LogOutcome` was called
- Assert `outcome.Success == false`, quality < 5

**Mock RSILogger for tests:**
```go
type mockRSILogger struct {
	outcomes []RSIOutcome
}

func (m *mockRSILogger) LogOutcome(_ context.Context, o RSIOutcome) error {
	m.outcomes = append(m.outcomes, o)
	return nil
}
```

## 8. Branch & PR Instructions

```bash
cd /tmp/evoclaw-plan-rsi
git checkout -b feat/toolloop-rsi-autolog

# Create new file
# Edit: internal/orchestrator/rsi_logger.go (new)
# Edit: internal/orchestrator/rsi_logger_test.go (new)
# Edit: internal/orchestrator/toolloop.go (modifications per §5)

# Update any callers of NewToolLoop to pass options (search for NewToolLoop calls):
grep -rn "NewToolLoop" internal/ cmd/

# Run tests
go test ./internal/orchestrator/... -v -run "RSI|Quality|TaskType"

# Full test suite
go test ./...

# Commit
git add -A
git commit -m "feat(orchestrator): auto-log RSI outcomes from tool loop

- Add RSILogger interface with JSONL and Noop implementations
- Derive quality (1-5) from error rate, task_type from tool names
- Wire into ToolLoop.Execute() at all exit points
- Default path: RSI_OUTCOMES_FILE env or ~/.openclaw/.../outcomes.jsonl
- Graceful no-op when path doesn't exist"

# Push & PR
git push -u origin feat/toolloop-rsi-autolog
gh pr create --title "feat(orchestrator): auto-log RSI outcomes from tool loop" \
  --body "Closes #TBD - Wires ToolLoop.Execute() to write JSONL outcomes for the RSI skill's analysis pipeline."
```

## 9. Important Notes for Builder

1. **Do NOT touch `internal/rsi/observer.go`** — the existing per-tool-call recording stays. This new logger captures the **aggregate loop outcome** (one record per Execute() call, not per tool call).

2. **The `rsi.Outcome` struct in `internal/rsi/types.go` uses `Quality float64` (0.0-1.0)** but the OpenClaw RSI skill schema uses `quality int` (1-5). Our `RSIOutcome` struct uses int 1-5 to match the JSONL schema. These are separate structs intentionally.

3. **Find all `NewToolLoop` call sites** and update them. Currently in `orchestrator.go`. Pass `WithRSILogger(NewDefaultRSILogger())` there.

4. **`allToolNames` collection** goes inside the main for-loop, right after `toolCalls` is populated (after `callLLM`), before `executeParallel`. Collect names from that iteration's `toolCalls`.

5. **Boundary case:** `DeriveQuality(2, 10)` = 20% error rate. Since `0.20 < 0.20` is false, this returns quality 3, not 4. The test table must reflect this. (Corrected: 2/10 = 0.20, `rate < 0.20` is false → falls to `rate < 0.50` → returns 3.)
