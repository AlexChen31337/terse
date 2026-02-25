# EvoClaw Coverage Boost Plan

**Goal:** `internal/api` 53.2% → 85%+ | `cmd/evoclaw` 7.2% → 85%+
**Date:** 2026-02-25

---

## 1. Coverage Gap Analysis

### `internal/api` — Current 53.2%

| File | Function | Current | Priority |
|------|----------|---------|----------|
| **chat.go** | `handleChat` | 0.0% | HIGH |
| **chat.go** | `handleChatStream` | 0.0% | HIGH |
| **chat.go** | `generateMessageID` | 0.0% | LOW (trivial) |
| **scheduler.go** | ALL 9 functions | 0.0% | **CRITICAL** (273 lines, 0% = biggest gap) |
| **helpers.go** | `writeJSON` | 0.0% | MEDIUM |
| **helpers.go** | `WriteError` | 0.0% | MEDIUM |
| **terminal.go** | `handleTerminalPage` | 0.0% | MEDIUM |
| **server.go** | `handleAgentUpdate` | 0.0% | HIGH |
| **memory.go** | `handleMemoryRetrieve` | 18.8% | HIGH |
| **memory.go** | `handleMemoryStats` | 25.0% | HIGH |
| **memory.go** | `handleMemoryTree` | 30.0% | HIGH |
| **genome.go** | `handleGetBehavior` | 40.0% | MEDIUM |
| **genome.go** | `handleGetBehaviorHistory` | 41.2% | MEDIUM |
| **genome.go** | `handleSubmitFeedback` | 50.0% | MEDIUM |
| **firewall.go** | `handleFirewallRollback` | 52.4% | MEDIUM |
| **firewall.go** | `handleFirewallReset` | 60.0% | MEDIUM |
| **genome.go** | `handleUpdateSkillParams` | 64.7% | LOW |
| **genome.go** | `handleConstraintRoutes` | 64.5% | LOW |
| **dashboard.go** | `getEvolutionStrategy` | 66.7% | LOW |

### `cmd/evoclaw` — Current 7.2%

| File | Function | Current | Priority |
|------|----------|---------|----------|
| **main.go** | `run` | 0.0% | **CRITICAL** (160 lines, main entry) |
| **main.go** | `setup` | 0.0% | **CRITICAL** (130 lines) |
| **main.go** | `printVersion` | 0.0% | LOW |
| **main.go** | `registerProviders` | 0.0% | HIGH |
| **main.go** | `registerChannels` | 0.0% | HIGH |
| **main.go** | `registerProvidersToOrchestrator` | 0.0% | MEDIUM |
| **main.go** | `startServices` | 0.0% | HIGH |
| **main.go** | `waitForShutdown` | 0.0% | MEDIUM |
| **gateway.go** | ALL 11 functions | 0.0% | HIGH (249 lines) |
| **signals_unix.go** | ALL 4 functions | 0.0% | MEDIUM |
| **systemd.go** | `installSystemd`, `uninstallSystemd` | 0.0% | MEDIUM |
| **launchd.go** | `installLaunchd`, `uninstallLaunchd` | 0.0% | SKIP (darwin-only) |
| **main.go** | `initializeAgents` | 44.4% | MEDIUM |
| **main.go** | `setupChains` | 17.4% | MEDIUM |

---

## 2. New Test File Plan

### `internal/api/` — 3 new files

| File | Targets | Est. Lines |
|------|---------|-----------|
| `scheduler_test.go` | All 9 scheduler handlers (0% → 90%+) | ~350 |
| `chat_test.go` | handleChat, handleChatStream, generateMessageID | ~200 |
| `deep_coverage_test.go` | handleAgentUpdate, handleTerminalPage, writeJSON, WriteError, remaining memory/genome/firewall gaps | ~300 |

### `cmd/evoclaw/` — 2 new files

| File | Targets | Est. Lines |
|------|---------|-----------|
| `run_test.go` | `run()` subcommand dispatch, `printVersion`, `setup` error paths | ~300 |
| `gateway_test.go` | All gateway functions, fileExists, getPIDFile, checkRunning, printGatewayHelp | ~350 |

---

## 3. Per-File Test List

### `internal/api/scheduler_test.go`

Needs mock scheduler interface. All handlers follow same pattern: check method → get scheduler → do work.

```
TestHandleSchedulerStatus_OK
TestHandleSchedulerStatus_NoScheduler
TestHandleSchedulerStatus_MethodNotAllowed
TestHandleSchedulerJobs_ListGET
TestHandleSchedulerJobs_AddPOST
TestHandleSchedulerJobs_MethodNotAllowed
TestHandleSchedulerAddJob_InvalidBody
TestHandleSchedulerAddJob_NoScheduler
TestHandleSchedulerAddJob_AddError
TestHandleSchedulerListJobs_NoScheduler
TestHandleSchedulerListJobs_OK
TestHandleSchedulerJobRoutes_GetJob
TestHandleSchedulerJobRoutes_RunJob
TestHandleSchedulerJobRoutes_UpdateJob
TestHandleSchedulerJobRoutes_DeleteJob
TestHandleSchedulerJobRoutes_MethodNotAllowed
TestHandleSchedulerGetJob_NotFound
TestHandleSchedulerGetJob_NoScheduler
TestHandleSchedulerGetJob_EmptyID
TestHandleSchedulerRunJob_OK
TestHandleSchedulerRunJob_NotFound
TestHandleSchedulerRunJob_NoScheduler
TestHandleSchedulerRunJob_MethodNotAllowed
TestHandleSchedulerUpdateJob_OK
TestHandleSchedulerUpdateJob_InvalidBody
TestHandleSchedulerUpdateJob_NotFound
TestHandleSchedulerUpdateJob_NoScheduler
TestHandleSchedulerUpdateJob_UpdateError
TestHandleSchedulerRemoveJob_OK
TestHandleSchedulerRemoveJob_NotFound
TestHandleSchedulerRemoveJob_NoScheduler
```

### `internal/api/chat_test.go`

Needs mock orchestrator with `GetInbox()` returning a channel, and mock httpChannel with `WaitForResponse()`.

```
TestHandleChat_OK
TestHandleChat_MethodNotAllowed
TestHandleChat_InvalidJSON
TestHandleChat_MissingAgent
TestHandleChat_MissingMessage
TestHandleChat_DefaultFrom
TestHandleChat_OrchestratorNotReady (nil inbox)
TestHandleChat_Timeout (blocked inbox)
TestHandleChat_ResponseError
TestHandleChatStream_OK
TestHandleChatStream_MethodNotAllowed
TestHandleChatStream_InvalidJSON
TestHandleChatStream_MissingFields
TestGenerateMessageID_Format
TestGenerateMessageID_Unique
```

### `internal/api/deep_coverage_test.go`

Uses existing mock setup from server_test.go.

```
TestHandleAgentUpdate_OK
TestHandleAgentUpdate_InvalidJSON
TestHandleAgentUpdate_InvalidModel
TestHandleAgentUpdate_PartialUpdate (name only, type only)
TestHandleAgentUpdate_RegistryError
TestHandleTerminalPage_WithWebFS
TestHandleTerminalPage_WithoutWebFS (fallback HTML)
TestHandleTerminalPage_MethodNotAllowed
TestWriteJSON_OK
TestWriteJSON_NilData
TestWriteError_OK
TestHandleMemoryRetrieve_Success (with working memory)
TestHandleMemoryRetrieve_EmptyQuery
TestHandleMemoryRetrieve_BadLimit
TestHandleMemoryStats_Success (with working memory)
TestHandleMemoryTree_Success (with working memory)
TestHandleGetBehavior_Success
TestHandleGetBehavior_NotFound
TestHandleGetBehaviorHistory_Success
TestHandleGetBehaviorHistory_NotFound
TestHandleSubmitFeedback_Success
TestHandleSubmitFeedback_InvalidJSON
TestHandleFirewallRollback_AllBranches
TestHandleFirewallReset_AllBranches
```

### `cmd/evoclaw/run_test.go`

Tests `run()` by manipulating `os.Args`. Uses temp dirs for config/data.

```
TestRun_HelpSubcommand
TestRun_VersionSubcommand
TestRun_UnknownSubcommand
TestRun_HelpFlag
TestRun_VersionFlag
TestRun_ConfigFlag
TestRun_HelpWithTarget
TestRun_StartSubcommand_NoConfig (setup fails gracefully)
TestPrintVersion_Output
TestSetup_DefaultConfig (creates default when missing)
TestSetup_InvalidConfig
TestSetup_ValidConfig
TestRegisterProviders_Empty
TestRegisterProviders_OllamaProvider
TestRegisterChannels_Empty
TestRegisterChannels_MQTTChannel
TestRegisterProvidersToOrchestrator
TestStartServices_APIOnly
TestInitializeAgents_CreateNew
TestInitializeAgents_UpdateExisting
TestSetupChains_NoChains
TestSetupChains_InvalidChain
TestGetShutdownSignals
TestHandlePlatformSignal
TestSetActiveConfig
TestReloadConfig
```

### `cmd/evoclaw/gateway_test.go`

Tests gateway subcommand functions using temp PID files and mocked processes.

```
TestRunGatewayCommand_Help
TestRunGatewayCommand_Status_NotRunning
TestRunGatewayCommand_UnknownSubcommand
TestFileExists_True
TestFileExists_False
TestGetPIDFile
TestCheckRunning_NoPIDFile
TestCheckRunning_StalePID
TestPrintGatewayHelp
TestGatewayStart_AlreadyRunning
TestGatewayStop_NotRunning
TestGatewayStatus_NotRunning
TestGatewayRestart
TestInstallSystemd_Template (verify output)
TestUninstallSystemd_NotInstalled
```

---

## 4. Mocking Strategy

### `internal/api` mocks needed:

1. **Scheduler interface** — The handlers call `s.orch.GetScheduler()` which returns a `*scheduler.Scheduler`. Create a mock that implements `GetStats()`, `ListJobs()`, `GetJob(id)`, `RunJobNow(id)`, `UpdateJob(job)`, `AddJob(job)`, `RemoveJob(id)`. Alternatively, check if existing test infra already has a `mockOrchestrator` — extend it to return a mock scheduler.

2. **HTTP Channel** — `handleChat` uses `s.httpChannel.WaitForResponse(ctx, id)`. Create `mockHTTPChannel` with controllable response/error.

3. **Orchestrator inbox** — `handleChat` calls `s.orch.GetInbox()` returning `chan orchestrator.Message`. Mock orch should return a buffered channel.

4. **fs.FS** — For `handleTerminalPage`, use `fstest.MapFS` from stdlib to provide/omit `terminal.html`.

5. **Router (ListModels)** — For `handleAgentUpdate`, the existing `mockRouter` should already work; just ensure `ListModels()` returns models for validation testing.

### `cmd/evoclaw` mocks needed:

1. **No mocks needed for most functions** — `run()`, `printVersion`, `setup`, `loadConfig` are testable by manipulating `os.Args`, temp config files, and capturing stdout/stderr.

2. **Temp directories** — Use `t.TempDir()` for config and data dirs.

3. **Gateway functions** — Use temp PID files; mock process existence via writing fake PIDs. For `daemonize`, test only error paths (can't easily test actual daemon fork in unit tests).

4. **Systemd/signals** — Test `installSystemd` by capturing output to a temp file; test `getShutdownSignals` by checking returned signal list; test `reloadConfig` with a valid config path.

---

## 5. Expected Coverage Delta

| New Test File | Statements Covered | Est. Coverage Gain |
|--------------|-------------------|-------------------|
| **api/scheduler_test.go** | ~130 of 135 stmts | +15% (0% → 95%) |
| **api/chat_test.go** | ~55 of 60 stmts | +6% (0% → 90%) |
| **api/deep_coverage_test.go** | ~100 new stmts | +12% (filling gaps in server/memory/genome/firewall/terminal/helpers) |
| **Total api** | | 53% + 33% = **~86%** |
| | | |
| **cmd/run_test.go** | ~250 of 310 stmts | +50% (covers run, setup, register*, signals) |
| **cmd/gateway_test.go** | ~120 of 140 stmts | +25% (covers gateway.go + systemd.go) |
| **Total cmd** | | 7% + 75% = **~82%** |

**Note:** `cmd/evoclaw` reaching 85% may require covering some `startServices`/`waitForShutdown` paths that involve goroutines and signal handling. If 82% is achieved, add integration-style tests for `startServices` with immediate context cancellation to push over 85%.

---

## 6. Pass Criteria

```bash
# Run coverage and verify
cd /tmp/evoclaw-plan-coverage

# API package
go test ./internal/api/... -coverprofile=/tmp/api.cov -count=1
go tool cover -func=/tmp/api.cov | tail -1
# Expected: total: (statements) ≥ 85.0%

# CMD package  
go test ./cmd/evoclaw/... -coverprofile=/tmp/cmd.cov -count=1
go tool cover -func=/tmp/cmd.cov | tail -1
# Expected: total: (statements) ≥ 85.0%

# No test failures
go test ./internal/api/... ./cmd/evoclaw/... -count=1
# Expected: all PASS

# Race detector clean
go test ./internal/api/... ./cmd/evoclaw/... -race -count=1
# Expected: no race conditions detected
```

### Definition of Done:
1. ✅ `internal/api` coverage ≥ 85%
2. ✅ `cmd/evoclaw` coverage ≥ 85%
3. ✅ All tests pass with `-race`
4. ✅ No duplicate test functions with existing files
5. ✅ Tests are deterministic (no flaky timing deps)
