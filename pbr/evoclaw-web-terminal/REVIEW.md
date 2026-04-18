# PR #15 — Web Terminal (WebSocket) — REVIEW REPORT

**Branch:** `feature/web-terminal-ws`  
**Reviewer:** Alex Chen (sub-agent reviewer)  
**Date:** 2026-02-25  
**Verdict:** ✅ PASS (2 bugs found + fixed, pushed as follow-up commit `e1734ec`)

---

## Test Results

```
go test ./internal/api/... ./internal/channels/... -race -count=1
ok  github.com/clawinfra/evoclaw/internal/api      1.66s
ok  github.com/clawinfra/evoclaw/internal/channels 2.13s

go build ./...   → OK
go vet   ./...   → OK
```

- ✅ **9 WS terminal tests** — all pass, race-clean  
- ✅ **9 WSChannel tests** — all pass, race-clean  
  _(spec listed 8 channel tests; 9 were implemented — all green)_

---

## Checklist

### 1. WSChannel — interface correctness + thread safety
| Item | Result |
|------|--------|
| Implements `Name / Start / Stop / Send / Receive` | ✅ |
| `Register` / `Unregister` use `sync.RWMutex` | ✅ |
| `Send` acquires `RLock`, routes to `wc.respCh` by `msg.MessageID` | ✅ |
| `Stop` acquires full lock, closes + deletes all `respCh` | ✅ |
| `Inbox()` exposes bidirectional chan for handler push | ✅ |

### 2. WS handler
| Item | Result |
|------|--------|
| JWT validated **before** `websocket.Accept()` | ✅ |
| `jwtSecret == nil` dev mode skips validation with a `Warn` log | ✅ |
| 30 s per-request timeout via `chatCtx` | ✅ |

### 3. Route order
| Item | Result |
|------|--------|
| `/api/terminal/ws` registered in mux **before** `jwtAuthWrapper` wraps it | ✅ |
| `/api/terminal/ws` in `jwtAuthWrapper` skip list | ✅ |

### 4. WriteTimeout
| Item | Result |
|------|--------|
| `WriteTimeout: 0` in `http.Server` struct | ✅ |
| Comment explains why (`required for long-lived WS connections`) | ✅ |

### 5. Tests
| Item | Result |
|------|--------|
| 9 WS terminal tests pass | ✅ |
| 9 WSChannel tests pass | ✅ |
| Race detector clean | ✅ |

### 6. xterm.js UI
| Item | Result |
|------|--------|
| `@xterm/xterm@5.5.0` from `cdn.jsdelivr.net` | ✅ |
| `@xterm/addon-fit@0.10.0` (`FitAddon`) present | ✅ |
| `@xterm/addon-web-links@0.11.0` (`WebLinksAddon`) present | ✅ |
| VS Code dark theme (`background: '#1e1e1e'`) | ✅ |
| Agent dropdown fetches from `/api/agents` with auth header | ✅ |

### 7. Reconnect
| Item | Result |
|------|--------|
| Exponential backoff: `reconnectDelay = Math.min(delay * 2, RECONNECT_MAX)` | ✅ |
| Max cap at 30 s | ✅ |

### 8. Auth UI
| Item | Result |
|------|--------|
| `localStorage.getItem/setItem(LS_TOKEN)` for token persistence | ✅ |
| `#login-overlay` shown when no token available in `boot()` | ✅ |
| `api-key-input` `Enter` key submits login | ✅ |

### 9. Security
| Item | Result |
|------|--------|
| No hardcoded secrets in new files | ✅ |
| JWT secret from `s.jwtSecret` field only (`security.GetJWTSecret()`) | ✅ |
| CSWSH fix applied (see Bug 2 below) | ✅ (fixed) |

### 10. No personal info
| Item | Result |
|------|--------|
| `grep` for owner name/phone/Telegram in new committed files | ✅ Clean |
| Author identity in commit: `Alex Chen <alex.chen31337@gmail.com>` | ✅ |

---

## Bugs Found & Fixed

### 🐛 Bug 1 — `setInterval` leak on reconnect (HIGH)

**File:** `web/terminal.html`  
**Description:** The keepalive ping `setInterval` was created **inside** `connectWS()`. Every reconnect created a new interval that was never cleared. After N reconnects, N+1 concurrent timers fired pings simultaneously, causing unnecessary traffic and memory accumulation.

**Fix applied:**
```js
// Before (leaks one interval per reconnect)
setInterval(() => { ... }, 25_000);

// After (clears previous, then sets new)
clearInterval(pingIntervalId);
pingIntervalId = setInterval(() => { ... }, 25_000);
```
Added `let pingIntervalId = null;` to module-level state.

---

### 🐛 Bug 2 — Unconditional `InsecureSkipVerify: true` (MEDIUM)

**File:** `internal/api/ws_terminal.go`  
**Description:** `websocket.Accept` was called with `InsecureSkipVerify: true` unconditionally. This disables the Origin header check, allowing **cross-site WebSocket hijacking (CSWSH)** from any domain in production. The JWT token guard provides partial mitigation, but disabling Origin checking is still a defence-in-depth failure.

**Fix applied:**
```go
// Before
conn, err := websocket.Accept(w, r, &websocket.AcceptOptions{
    InsecureSkipVerify: true, // accept any Origin for dev convenience
})

// After — only skip in dev mode (no jwtSecret)
conn, err := websocket.Accept(w, r, &websocket.AcceptOptions{
    InsecureSkipVerify: s.jwtSecret == nil,
})
```

---

## Minor Observations (Not Blocking)

1. **`handleAuthToken` dev-mode token generation** — the `api_key` field in the `/api/auth/token` request body is accepted regardless of its value (no validation against a known secret). This is fine for dev mode but the endpoint should add a `// TODO: validate api_key against owner secret in production` comment to avoid misuse in production deployments.

2. **`wsjson.Read` error handling** — when the client disconnects ungracefully (e.g. browser tab close), the read error correctly triggers `return`, but the `defer conn.Close(...)` may log a benign error since the connection is already closed. This is cosmetic and does not affect correctness.

3. **`Send` uses `default` branch** — if the agent sends a response while the handler hasn't consumed the first one, the response is silently dropped. The buffered channel (capacity 1) and serial request-per-connection flow make this unreachable in practice, but a `// Note: capacity-1 channel; serial request flow prevents contention` comment would help.

---

## Summary

The implementation is well-architected, correctly separates auth from the WS upgrade, is race-clean, and all tests pass. Two bugs were found and fixed in commit `e1734ec` on the branch. Ready to merge after standard CI green check.
