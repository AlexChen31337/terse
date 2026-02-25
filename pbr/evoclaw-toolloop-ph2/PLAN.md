# Tool Loop Phase 2: Parallel Execution — Technical Plan

> **Status:** Ready for Builder  
> **Author:** Planner (Alex Chen)  
> **Date:** 2026-02-25  
> **Branch:** `feat/toolloop-phase2-parallel`

---

## 1. Current Phase 1 Architecture Summary

### What Exists

**`internal/orchestrator/toolloop.go`** contains the full tool loop:

- **`ToolLoop`** struct — holds orchestrator ref, toolManager, config (maxIterations=10, errorLimit=3, defaultTimeout=30s)
- **`ToolCall`** struct — `{ID, Name, Arguments}` — already supports multiple calls (the LLM response `ChatResponse.ToolCalls` is `[]ToolCall`)
- **`ToolResult`** struct — `{Tool, Status, Result, Error, ErrorType, ElapsedMs, ExitCode}`
- **`ToolLoopMetrics`** struct — `{TotalIterations, ToolCalls, SuccessCount, ErrorCount, TimeoutCount, TotalDuration}`

**`Execute()` method** (the main loop):
1. Generates tool schemas, builds conversation `messages []ChatMessage`
2. Loops up to `maxIterations`:
   - Calls LLM via `callLLM()` → returns `(ChatResponse, []ToolCall, error)`
   - If `len(toolCalls) == 0` → final answer, break
   - **Sequentially** iterates `for _, toolCall := range toolCalls` — calls `executeToolCall()` one at a time
   - Each `executeToolCall()` sends MQTT command to edge agent, blocks on `waitForToolResult()`
   - Appends each tool result as a `ChatMessage{Role: "tool", ToolCallID: ..., Content: ...}`
3. If loop exhausted or no final content → makes summary LLM call

**Key insight:** The code already parses `[]ToolCall` from the LLM response. The only change is the inner `for` loop executes sequentially. Phase 2 replaces that sequential loop with concurrent execution.

### What Changes

| Component | Change |
|-----------|--------|
| `ToolLoopMetrics` | Add 3 new fields |
| `Execute()` inner loop | Replace sequential `for` with call to `executeParallel()` |
| New helper `executeParallel()` | Fan-out/fan-in with errgroup |
| `formatToolResults()` (new) | Batch-format multiple results into `[]ChatMessage` |
| No changes to | `callLLM()`, `executeToolCall()`, `waitForToolResult()`, `formatToolResult()`, `ToolCall`, `ToolResult`, `ChatMessage`, `ChatResponse`, providers, edge agent |

---

## 2. Struct & Signature Changes

### `ToolLoopMetrics` — add 3 fields

```go
type ToolLoopMetrics struct {
	TotalIterations int
	ToolCalls       int
	SuccessCount    int
	ErrorCount      int
	TimeoutCount    int
	TotalDuration   time.Duration
	// Phase 2: parallel execution metrics
	ParallelBatches int           // Number of batches with >1 tool call
	MaxConcurrency  int           // Largest single batch size seen
	WallTimeSavedMs int64         // Sum of (sequential_time - wall_time) across all parallel batches
}
```

### `Execute()` — signature unchanged

```go
func (tl *ToolLoop) Execute(agent *AgentState, msg Message, model string) (*Response, *ToolLoopMetrics, error)
```

No signature change. Internal logic changes only (see §3).

---

## 3. New Helper: `executeParallel`

### Signature

```go
// parallelToolResult pairs a ToolCall with its result for ordered fan-in.
type parallelToolResult struct {
	Index    int         // original position in the toolCalls slice
	Call     ToolCall
	Result   *ToolResult
	Err      error
}

// executeParallel executes multiple tool calls concurrently using errgroup.
// Returns results in the SAME ORDER as the input calls slice.
// Individual tool errors are captured in parallelToolResult.Err — the function
// itself only returns an error if the context is cancelled.
func (tl *ToolLoop) executeParallel(agent *AgentState, calls []ToolCall) ([]parallelToolResult, error)
```

### Algorithm

```
func executeParallel(agent, calls):
    results = make([]parallelToolResult, len(calls))
    
    // Short-circuit: single call → no goroutine overhead
    if len(calls) == 1:
        result, err = tl.executeToolCall(agent, calls[0])
        results[0] = {Index: 0, Call: calls[0], Result: result, Err: err}
        return results, nil
    
    g, ctx = errgroup.WithContext(tl.orchestrator.ctx)
    
    // Optional: limit concurrency to prevent MQTT flooding
    g.SetLimit(5)  // max 5 concurrent tool calls
    
    for i, call := range calls:
        i, call := i, call  // capture loop vars
        g.Go(func() error:
            // Check context before starting
            if ctx.Err() != nil:
                results[i] = {Index: i, Call: call, Err: ctx.Err()}
                return nil  // don't abort group for individual failures
            
            result, err := tl.executeToolCall(agent, call)
            results[i] = {Index: i, Call: call, Result: result, Err: err}
            return nil  // never return error — we want all goroutines to complete
        )
    
    _ = g.Wait()  // always nil since goroutines never return errors
    return results, ctx.Err()
```

**Key design decisions:**
1. **Never return error from goroutine** — we want ALL tool calls to complete even if some fail (the LLM needs all results to reason about errors)
2. **Concurrency limit = 5** — prevents MQTT channel flooding; configurable via `ToolLoop.maxParallel` (new field, default 5)
3. **Results indexed by position** — maintains deterministic ordering for LLM context assembly
4. **Single-call fast path** — no goroutine overhead when Ph.1 behavior suffices

### New field on `ToolLoop`

```go
type ToolLoop struct {
	// ... existing fields ...
	maxParallel int // max concurrent tool calls per batch (default: 5)
}
```

Set in `NewToolLoop()`: `maxParallel: 5`

---

## 4. Changes to `Execute()` Inner Loop

Replace the existing sequential tool execution block (lines ~120-155 in current code) with:

### Current (Phase 1):
```go
// Execute each tool call
for _, toolCall := range toolCalls {
    metrics.ToolCalls++
    toolResult, err := tl.executeToolCall(agent, toolCall)
    if err != nil {
        consecutiveErrors++
        metrics.ErrorCount++
        errorMsg := fmt.Sprintf("Error executing %s: %v", toolCall.Name, err)
        messages = append(messages, ChatMessage{
            Role:       "tool",
            ToolCallID: toolCall.ID,
            Content:    errorMsg,
        })
        if consecutiveErrors >= tl.errorLimit {
            return nil, nil, fmt.Errorf("too many consecutive errors (%d)", consecutiveErrors)
        }
        continue
    }
    consecutiveErrors = 0
    if toolResult.Status == "success" {
        metrics.SuccessCount++
    } else {
        metrics.ErrorCount++
        if toolResult.ErrorType == "timeout" {
            metrics.TimeoutCount++
        }
    }
    toolMsg := tl.formatToolResult(toolCall, toolResult)
    messages = append(messages, toolMsg)
}
```

### New (Phase 2):
```go
// Execute tool calls (parallel when multiple)
batchStart := time.Now()
parallelResults, err := tl.executeParallel(agent, toolCalls)
if err != nil {
    return nil, nil, fmt.Errorf("parallel execution cancelled: %w", err)
}
batchWall := time.Since(batchStart)

// Track parallel metrics
if len(toolCalls) > 1 {
    metrics.ParallelBatches++
    if len(toolCalls) > metrics.MaxConcurrency {
        metrics.MaxConcurrency = len(toolCalls)
    }
}

// Fan-in: process results in original order
var sumSequentialMs int64
allErrors := true // track if ALL calls in this batch errored

for _, pr := range parallelResults {
    metrics.ToolCalls++
    
    if pr.Err != nil {
        consecutiveErrors++
        metrics.ErrorCount++
        errorMsg := fmt.Sprintf("Error executing %s: %v", pr.Call.Name, pr.Err)
        messages = append(messages, ChatMessage{
            Role:       "tool",
            ToolCallID: pr.Call.ID,
            Content:    errorMsg,
        })
        continue
    }
    
    allErrors = false
    
    if pr.Result.Status == "success" {
        consecutiveErrors = 0
        metrics.SuccessCount++
    } else {
        metrics.ErrorCount++
        if pr.Result.ErrorType == "timeout" {
            metrics.TimeoutCount++
        }
    }
    
    sumSequentialMs += pr.Result.ElapsedMs
    toolMsg := tl.formatToolResult(pr.Call, pr.Result)
    messages = append(messages, toolMsg)
}

// Calculate wall time saved (only meaningful for parallel batches)
if len(toolCalls) > 1 {
    wallMs := batchWall.Milliseconds()
    saved := sumSequentialMs - wallMs
    if saved > 0 {
        metrics.WallTimeSavedMs += saved
    }
}

// Check error limit: only if ALL calls in batch failed
if allErrors && len(toolCalls) > 0 {
    consecutiveErrors += len(toolCalls)
}
if consecutiveErrors >= tl.errorLimit {
    return nil, nil, fmt.Errorf("too many consecutive errors (%d)", consecutiveErrors)
}
```

**Error counting change:** In Ph.1, `consecutiveErrors` increments per failed call. In Ph.2, a single successful call in a batch resets the counter. The error limit check uses batch-level logic: only if ALL calls in a batch fail does it count toward the limit.

---

## 5. LLM Response Parsing — No Changes Needed

The existing `callLLM()` method already handles this correctly:

```go
func (tl *ToolLoop) callLLM(...) (*ChatResponse, []ToolCall, error) {
    // ...
    if resp.ToolCalls != nil {
        toolCalls = resp.ToolCalls
    }
    return resp, toolCalls, nil
}
```

`ChatResponse.ToolCalls` is `[]ToolCall`. The OpenAI API returns `tool_calls` as an array. Single vs multiple is just `len(toolCalls)`:
- `len == 0` → no tool call, final answer
- `len == 1` → single call (fast-path in `executeParallel`, behaves like Ph.1)
- `len > 1` → parallel execution

**No parsing changes required.** The existing provider implementations must already marshal `tool_calls` array from the API response into `[]ToolCall`. If any provider only parses the first element, that's a provider bug to fix separately.

---

## 6. Context Assembly — Multiple Tool Results

Already handled by the existing `formatToolResult()` method. Each tool result becomes a separate `ChatMessage{Role: "tool", ToolCallID: call.ID, Content: ...}`. The OpenAI chat completions API expects one `tool` message per `tool_call` in the assistant message, matched by `tool_call_id`.

**Order matters:** Results MUST be appended in the same order as `toolCalls` in the assistant message. This is guaranteed by `parallelToolResult.Index` ordering (the results slice is pre-allocated by index).

**Example conversation with 2 parallel calls:**
```json
[
  {"role": "user", "content": "Check CPU temp and disk usage"},
  {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {"id": "call_1", "name": "bash", "arguments": {"command": "vcgencmd measure_temp"}},
      {"id": "call_2", "name": "bash", "arguments": {"command": "df -h /"}}
    ]
  },
  {"role": "tool", "tool_call_id": "call_1", "content": "temp=45.6°C"},
  {"role": "tool", "tool_call_id": "call_2", "content": "Filesystem  Size  Used Avail Use%\n/dev/sda1   50G   20G   30G  40%"}
]
```

No changes needed to `formatToolResult()` or `ChatMessage` struct.

---

## 7. Test Plan

### File: `internal/orchestrator/toolloop_parallel_test.go`

#### Required dependency

```go
import "golang.org/x/sync/errgroup"
```

Add to `go.mod`: `go get golang.org/x/sync`

#### Mock infrastructure

```go
// mockEdgeExecutor replaces executeToolCall for testing.
// Configurable per-call latency and results.
type mockEdgeExecutor struct {
    results  map[string]*ToolResult  // keyed by tool call ID
    latency  map[string]time.Duration
    mu       sync.Mutex
    callLog  []string  // records order of execution starts
}

func (m *mockEdgeExecutor) execute(agent *AgentState, call ToolCall) (*ToolResult, error) {
    m.mu.Lock()
    m.callLog = append(m.callLog, call.ID)
    m.mu.Unlock()
    
    if d, ok := m.latency[call.ID]; ok {
        time.Sleep(d)
    }
    
    if r, ok := m.results[call.ID]; ok {
        return r, nil
    }
    return nil, fmt.Errorf("unexpected call: %s", call.ID)
}
```

To inject the mock, extract `executeToolCall` into an interface or function field on `ToolLoop`:

```go
type ToolLoop struct {
    // ... existing ...
    // execFunc overrides executeToolCall for testing. If nil, uses the real method.
    execFunc func(agent *AgentState, call ToolCall) (*ToolResult, error)
}
```

In `executeParallel`, use: `fn := tl.execFunc; if fn == nil { fn = tl.executeToolCall }`

#### Table-driven tests

| Test Name | Calls | Expected |
|-----------|-------|----------|
| `TestParallel_SingleCall` | 1 call, 100ms | Behaves like Ph.1. `ParallelBatches=0`, `MaxConcurrency=0` |
| `TestParallel_TwoCalls` | 2 calls, each 200ms | Wall time < 300ms (proves parallelism). `ParallelBatches=1`, `MaxConcurrency=2`, `WallTimeSavedMs > 0` |
| `TestParallel_OneFailsOneSucceeds` | 2 calls, call_1 errors, call_2 succeeds | Both results returned. `SuccessCount=1`, `ErrorCount=1`. `consecutiveErrors` reset to 0 |
| `TestParallel_AllFail` | 3 calls, all error | `ErrorCount=3`. Error limit triggered if `consecutiveErrors >= errorLimit` |
| `TestParallel_OrderPreserved` | 3 calls with varying latency (300ms, 100ms, 200ms) | Results array ordered [0,1,2] regardless of completion order |
| `TestParallel_ConcurrencyLimit` | 8 calls, maxParallel=3 | At most 3 concurrent (use atomic counter in mock to track max in-flight) |
| `TestParallel_ContextCancelled` | 5 calls, cancel context after 50ms | Returns ctx.Err(), partial results |
| `TestParallel_MetricsWallTimeSaved` | 2 calls each 200ms | `WallTimeSavedMs ≈ 200` (±50ms tolerance) |
| `TestExecute_MultiToolLLMResponse` | Full Execute() with mock LLM returning 2 tool_calls | End-to-end: LLM gets 2 tool results, produces final answer. Verify message history has correct tool_call_id ordering |
| `TestExecute_BackwardCompatSingleTool` | Full Execute() with mock LLM returning 1 tool_call | Identical behavior to Ph.1. `ParallelBatches=0` |

#### Test structure (example)

```go
func TestParallel_TwoCalls(t *testing.T) {
    mock := &mockEdgeExecutor{
        results: map[string]*ToolResult{
            "call_1": {Tool: "bash", Status: "success", Result: "ok1"},
            "call_2": {Tool: "bash", Status: "success", Result: "ok2"},
        },
        latency: map[string]time.Duration{
            "call_1": 200 * time.Millisecond,
            "call_2": 200 * time.Millisecond,
        },
    }
    
    tl := &ToolLoop{
        maxParallel: 5,
        execFunc:    mock.execute,
        // ... minimal setup ...
    }
    
    calls := []ToolCall{
        {ID: "call_1", Name: "bash"},
        {ID: "call_2", Name: "bash"},
    }
    
    start := time.Now()
    results, err := tl.executeParallel(nil, calls)
    elapsed := time.Since(start)
    
    require.NoError(t, err)
    require.Len(t, results, 2)
    assert.Equal(t, "call_1", results[0].Call.ID)
    assert.Equal(t, "call_2", results[1].Call.ID)
    assert.Less(t, elapsed, 300*time.Millisecond, "should run in parallel")
}
```

---

## 8. Branch & PR Instructions

1. **Branch:** `feat/toolloop-phase2-parallel`
   ```bash
   cd /path/to/evoclaw
   git checkout -b feat/toolloop-phase2-parallel
   ```

2. **Add dependency:**
   ```bash
   go get golang.org/x/sync
   ```

3. **Files to modify:**
   - `internal/orchestrator/toolloop.go` — all changes described in §2-4
   
4. **Files to create:**
   - `internal/orchestrator/toolloop_parallel_test.go` — tests from §7

5. **Files to update:**
   - `docs/AGENTIC-TOOL-LOOP.md` — update Phase 2 section to mark as "Implemented", add parallel execution details
   - `go.mod` / `go.sum` — via `go get`

6. **Commit message:**
   ```
   feat(toolloop): Phase 2 — parallel tool execution via errgroup
   
   - Add executeParallel() for concurrent tool call fan-out/fan-in
   - Add ParallelBatches, MaxConcurrency, WallTimeSavedMs to metrics
   - Single-call fast path preserves Ph.1 behavior exactly
   - Concurrency capped at 5 (configurable via maxParallel)
   - Results ordered by original call index for deterministic LLM context
   - Table-driven tests with mock edge executor
   ```

7. **PR title:** `feat(toolloop): Phase 2 — parallel tool execution`
   - Label: `enhancement`
   - Reviewers: Bowen
   - Link to this plan in PR description

8. **CI checks:** `go test ./internal/orchestrator/... -race -count=1` (race detector critical for parallel code)

---

## Summary of All Changes

| File | Type | Description |
|------|------|-------------|
| `internal/orchestrator/toolloop.go` | Modify | Add `parallelToolResult` type, `maxParallel` field, `execFunc` field, `executeParallel()` method. Replace sequential loop in `Execute()` with parallel batch. Add 3 fields to `ToolLoopMetrics`. |
| `internal/orchestrator/toolloop_parallel_test.go` | New | 10 table-driven tests with mock edge executor |
| `go.mod` | Modify | Add `golang.org/x/sync` |
| `docs/AGENTIC-TOOL-LOOP.md` | Modify | Update Phase 2 status |

**Total estimated LoC:** ~250 (implementation) + ~300 (tests) = ~550 lines
