# EvoClaw Web Terminal — Technical Plan

**Branch:** `feature/web-terminal-ws`  
**Base:** `main`  
**Author:** Builder sub-agent  
**Date:** 2026-02-25

---

## 1. Current State Assessment

### What exists
| File | Purpose | Status |
|------|---------|--------|
| `web/terminal.html` | Chat UI with marked.js, dark theme (#1e1e1e), agent dropdown | Working but uses HTTP POST `/api/chat` (no streaming) |
| `internal/api/terminal.go` | Serves `terminal.html` from embedded FS | Minimal — just file serving |
| `internal/api/server.go` | HTTP mux with JWT auth, CORS, routes | Has `/terminal` route, no WS route |
| `internal/api/chat.go` | `POST /api/chat` (sync) + `POST /api/chat/stream` (SSE stub) | SSE handler is a TODO stub |
| `internal/channels/http.go` | `HTTPChannel` — request/response pairs via pending map | No streaming support |
| `internal/orchestrator/orchestrator.go` | Orchestrator with `inbox chan Message`, `ModelProvider.Chat()` | No streaming `Chat` variant |

### Key interfaces (don't break these)
```go
// internal/orchestrator/orchestrator.go
type Channel interface {
    Name() string
    Start(ctx context.Context) error
    Stop() error
    Send(ctx context.Context, msg Response) error
    Receive() <-chan Message
}

type ModelProvider interface {
    Name() string
    Chat(ctx context.Context, req ChatRequest) (*ChatResponse, error)
    Models() []config.Model
}

// internal/types/types.go
type Message struct {
    ID, Channel, From, To, Content string
    Timestamp time.Time
    ReplyTo   string
    Metadata  map[string]string
}

type Response struct {
    AgentID, Content, Channel, To, ReplyTo, MessageID, Model string
    Metadata map[string]string
}
```

### Dependencies (go.mod)
- `github.com/golang-jwt/jwt/v5` — JWT auth
- No WebSocket library yet

---

## 2. WebSocket Handler Design

### 2.1 New dependency

Add `nhooyr.io/websocket` v1.8.17 (lightweight, stdlib-compatible, context-aware):

```bash
go get nhooyr.io/websocket@v1.8.17
```

**Why nhooyr over gorilla/websocket:** nhooyr uses `context.Context` natively, supports `wsjson` helpers, and is actively maintained. gorilla/websocket is archived.

### 2.2 WebSocket message protocol (JSON)

#### Client → Server
```json
{
  "type": "chat",
  "agent_id": "agent-001",
  "message": "Hello agent",
  "request_id": "req_1708834200_abc"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | `"chat"` (future: `"ping"`, `"cancel"`) |
| `agent_id` | string | yes | Target agent ID |
| `message` | string | yes | User message content |
| `request_id` | string | yes | Client-generated unique ID for correlation |

#### Server → Client
```json
{
  "type": "token",
  "request_id": "req_1708834200_abc",
  "agent_id": "agent-001",
  "content": "Hello",
  "done": false,
  "model": "",
  "error": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `"token"` (streaming chunk), `"done"` (final), `"error"`, `"system"`, `"pong"` |
| `request_id` | string | Correlates to client request |
| `agent_id` | string | Responding agent |
| `content` | string | Token text (for `"token"`) or full response (for `"done"`) |
| `done` | bool | `true` on final message |
| `model` | string | Model used (set on `"done"`) |
| `error` | string | Error message (for `"error"` type) |

### 2.3 Handler implementation plan

**File: `internal/api/ws_terminal.go`** (new file)

```
package api

// Types:
//   WSRequest  — client→server message (type, agent_id, message, request_id)
//   WSResponse — server→client message (type, request_id, agent_id, content, done, model, error)

// func (s *Server) handleTerminalWS(w http.ResponseWriter, r *http.Request)
//   1. Extract JWT from ?token= query param
//   2. Validate JWT using security.ValidateToken(token, s.jwtSecret)
//   3. If invalid → HTTP 401 before upgrade
//   4. Upgrade to WebSocket: websocket.Accept(w, r, &websocket.AcceptOptions{...})
//   5. Enter read loop:
//      a. Read JSON message (WSRequest)
//      b. Validate agent_id exists in registry
//      c. Create orchestrator.Message, send to inbox
//      d. Wait for response via httpChannel.WaitForResponse()
//      e. Send WSResponse with done=true
//   6. On error/disconnect: close gracefully
```

**Phase 1 (this PR):** Non-streaming — send full response as single `done` message. This works with the existing `HTTPChannel.WaitForResponse()` pattern.

**Phase 2 (follow-up):** Add `StreamChat()` to `ModelProvider` interface and stream tokens incrementally. This requires provider-level changes and is out of scope.

### 2.4 Concurrency model

- One goroutine per WS connection for reading
- One goroutine per active request for waiting on orchestrator response
- Use `context.WithTimeout` (30s) per request
- Max 1 concurrent request per connection (queue or reject additional)

---

## 3. xterm.js Terminal Redesign

### 3.1 CDN dependencies

```html
<!-- xterm.js v5.5.0 (latest stable) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/css/xterm.min.css">
<script src="https://cdn.jsdelivr.net/npm/@xterm/xterm@5.5.0/lib/xterm.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@xterm/addon-fit@0.10.0/lib/addon-fit.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@xterm/addon-web-links@0.11.0/lib/addon-web-links.min.js"></script>

<!-- Keep marked.js for markdown rendering -->
<script src="https://cdn.jsdelivr.net/npm/marked@11.1.1/marked.min.js"></script>
```

### 3.2 UI layout

```
┌─────────────────────────────────────────────┐
│ 🧬 EvoClaw Terminal   [agent-dropdown ▼]  ● │  ← header bar (keep existing)
├─────────────────────────────────────────────┤
│                                             │
│  xterm.js terminal area                     │  ← full height, dark theme
│  - Streaming responses appear here          │
│  - Markdown code blocks syntax-highlighted  │
│  - User input at prompt line                │
│                                             │
│  evoclaw@agent-001 > _                      │  ← prompt with agent name
│                                             │
└─────────────────────────────────────────────┘
```

### 3.3 JavaScript architecture

**File: `web/terminal.html`** (rewrite)

```
Classes/modules (all inline in <script>):

1. TerminalApp
   - Properties: term (Terminal), fitAddon, ws (WebSocket), currentAgent, inputBuffer, isProcessing
   - init(): create Terminal, load addons, connect WS, load agents, bind events
   - connectWS(): open WS with ?token= param, handle onmessage/onclose/onerror
   - reconnectWS(): exponential backoff reconnect (1s, 2s, 4s, max 30s)

2. Input handling
   - term.onData(data): capture keystrokes
   - Printable chars → append to inputBuffer, echo to terminal
   - Enter → send message, clear buffer
   - Backspace → remove last char from buffer, erase on terminal
   - Ctrl+C → clear inputBuffer, write ^C + newline + new prompt
   - Ctrl+L → clear terminal, redraw prompt
   - Up/Down → command history (array of last 50 commands)

3. Output rendering
   - writeResponse(content): write agent response to terminal
   - For code blocks (``` delimited): use ANSI colors for syntax highlighting
   - For inline code: dim color
   - For bold (**text**): use ANSI bold \x1b[1m
   - For headers (#): bold + color
   - Plain text: default color
   - Keep it simple — basic ANSI escapes, not full markdown→ANSI

4. Prompt
   - Format: \x1b[32mevoclaw\x1b[0m@\x1b[36m{agent_id}\x1b[0m > 
   - Redrawn after each response completes

5. Agent selector
   - Keep <select> dropdown in header
   - On change: update prompt, send system message to terminal
   - Fetch agents from /api/agents on load
```

### 3.4 xterm.js theme config

```javascript
{
    theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#d4d4d4',
        cursorAccent: '#1e1e1e',
        selectionBackground: '#264f78',
        black: '#1e1e1e',
        red: '#f48771',
        green: '#4ec9b0',
        yellow: '#dcdcaa',
        blue: '#569cd6',
        magenta: '#c586c0',
        cyan: '#9cdcfe',
        white: '#d4d4d4',
    },
    fontFamily: "'Monaco', 'Menlo', 'Consolas', monospace",
    fontSize: 14,
    cursorBlink: true,
    scrollback: 5000,
}
```

---

## 4. Token Streaming Approach

### Phase 1 (this PR): Full-response over WS

```
Client                    Server                     Orchestrator
  |                         |                            |
  |--WSRequest{chat}------->|                            |
  |                         |--Message-->inbox----------->|
  |                         |                            |--Chat(req)-->Provider
  |                         |                            |<--ChatResponse------
  |                         |<--Response via HTTPChannel-|
  |<--WSResponse{done=true}-|                            |
```

The WS handler:
1. Receives `WSRequest`
2. Creates `orchestrator.Message` with `Channel: "websocket"` and `Metadata: {"ws_request_id": request_id}`
3. Registers a pending response channel (reuse `HTTPChannel` pattern or create `WSChannel`)
4. Sends message to `orchestrator.GetInbox()`
5. Waits on response channel (30s timeout)
6. Sends `WSResponse` with full content and `done: true`

**Implementation choice:** Create a new `WSChannel` (`internal/channels/ws.go`) that implements `Channel` interface. This is cleaner than reusing `HTTPChannel` because WS connections are persistent.

```
// WSChannel — manages active WS connections and routes responses
type WSChannel struct {
    mu      sync.RWMutex
    conns   map[string]*wsConn  // messageID → connection
    logger  *slog.Logger
}

// wsConn wraps a single WS connection
type wsConn struct {
    conn      *websocket.Conn
    requestID string
    respCh    chan types.Response
}
```

Register `WSChannel` with orchestrator: `orch.RegisterChannel(wsChannel)`

### Phase 2 (future): True token streaming

Would require:
- `ModelProvider.StreamChat(ctx, req, callback func(token string))` interface addition
- Orchestrator routing stream callbacks to the originating channel
- WS handler sending incremental `WSResponse{type: "token", done: false}` messages

**Not in scope for this PR.** Phase 1 gives a working terminal; Phase 2 adds streaming UX.

---

## 5. Auth Flow

### Token acquisition
```
1. User opens /terminal in browser
2. terminal.html shows a login form OR reads token from localStorage
3. User POSTs to /api/auth/token with { agent_id, role, api_key }
4. Server returns { token, expires_in }
5. Client stores token in localStorage
6. Client connects WS: ws://host/api/terminal/ws?token=<jwt>
```

### WS auth validation (in `handleTerminalWS`)
```
1. Parse ?token= from r.URL.Query()
2. If empty → respond 401 BEFORE WebSocket upgrade
3. Call security.ValidateToken(token, s.jwtSecret)
4. If invalid/expired → respond 401
5. If valid → proceed with websocket.Accept()
6. Store claims (agent_id, role) on connection context
```

### Dev mode
When `EVOCLAW_JWT_SECRET` is not set (jwtSecret == nil):
- Skip token validation on WS upgrade
- Log warning: "WebSocket terminal running without auth (dev mode)"
- Same pattern as existing `jwtAuthWrapper` in server.go

### Token in header bar
Add a small auth UI to terminal.html:
- If no token in localStorage → show "Login" button in header
- On click → prompt for API key, POST to `/api/auth/token`
- Store result in localStorage
- On 401 during WS connect → clear localStorage, show login prompt

---

## 6. Test Plan

### File: `internal/api/ws_terminal_test.go`

#### Test 1: `TestWSAuth_NoToken`
- Connect to `/api/terminal/ws` without `?token=`
- Expect HTTP 401 response (not upgraded)

#### Test 2: `TestWSAuth_InvalidToken`
- Connect with `?token=garbage`
- Expect HTTP 401

#### Test 3: `TestWSAuth_ExpiredToken`
- Generate token with -1h expiry
- Connect → expect 401

#### Test 4: `TestWSAuth_ValidToken_DevMode`
- Server with `jwtSecret == nil`
- Connect without token → expect successful upgrade

#### Test 5: `TestWSChat_ValidMessage`
- Setup: create test server with mock orchestrator, register a test agent
- Connect WS with valid token
- Send `WSRequest{type: "chat", agent_id: "test-agent", message: "hello", request_id: "r1"}`
- Mock orchestrator returns "world"
- Expect `WSResponse{type: "done", content: "world", done: true, request_id: "r1"}`

#### Test 6: `TestWSChat_InvalidAgent`
- Send request with non-existent `agent_id`
- Expect `WSResponse{type: "error", error: "agent not found"}`

#### Test 7: `TestWSChat_Timeout`
- Mock orchestrator that never responds
- Send request with 2s test timeout
- Expect `WSResponse{type: "error", error: "timeout"}`

#### Test 8: `TestWSChat_MalformedJSON`
- Send raw bytes "not json"
- Expect error response or connection close

#### Test 9: `TestWSPingPong`
- Send `WSRequest{type: "ping"}`
- Expect `WSResponse{type: "pong"}`

### Test helpers needed
```go
// testWSServer() — creates httptest.Server with WS handler, mock registry, mock orchestrator
// mockOrchestrator — implements GetInbox(), channels have pre-programmed responses
// wsConnect(t, url, token) — helper to dial WS with token param
```

### Running tests
```bash
go test ./internal/api/ -run TestWS -v -count=1
```

---

## 7. File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `go.mod` / `go.sum` | Modify | Add `nhooyr.io/websocket` v1.8.17 |
| `internal/api/ws_terminal.go` | **Create** | WS handler, WSRequest/WSResponse types, auth logic |
| `internal/api/ws_terminal_test.go` | **Create** | 9 test cases per §6 |
| `internal/api/server.go` | Modify | Add route: `mux.HandleFunc("/api/terminal/ws", s.handleTerminalWS)` |
| `internal/api/server.go` | Modify | Increase `WriteTimeout` to 0 or use hijack (WS needs long-lived conn) |
| `internal/channels/ws.go` | **Create** | `WSChannel` implementing `Channel` interface |
| `internal/channels/ws_test.go` | **Create** | Unit tests for WSChannel |
| `web/terminal.html` | **Rewrite** | xterm.js UI per §3 |

### server.go specific changes

1. Add WS route **before** the auth wrapper section:
```go
mux.HandleFunc("/api/terminal/ws", s.handleTerminalWS)
```

2. The `jwtAuthWrapper` already skips non-`/api/` routes. For WS, auth is handled inside `handleTerminalWS` (before upgrade), so either:
   - Add `/api/terminal/ws` to the skip list in `jwtAuthWrapper`, OR
   - Let the middleware pass (it reads `Authorization` header; WS uses query param instead — the middleware would reject). **Better to skip it.**

3. Remove `WriteTimeout: 15s` for the whole server is too aggressive. Instead, the WS handler should hijack before the timeout applies (nhooyr handles this internally). Alternatively, set `WriteTimeout: 0` and rely on per-handler timeouts. **Recommendation:** set to 0 and add explicit timeouts in non-WS handlers.

### WSChannel registration in NewServer or Start

In `server.go` `NewServer()`:
```go
wsChannel := channels.NewWSChannel(logger)
if orch != nil {
    orch.RegisterChannel(wsChannel)
}
s.wsChannel = wsChannel
```

Add `wsChannel *channels.WSChannel` field to `Server` struct.

---

## 8. Branch & PR Instructions

```bash
# 1. Branch
git checkout -b feature/web-terminal-ws
git push -u origin feature/web-terminal-ws

# 2. Implement in this order:
#    a. go get nhooyr.io/websocket
#    b. internal/channels/ws.go + tests
#    c. internal/api/ws_terminal.go + tests  
#    d. internal/api/server.go changes
#    e. web/terminal.html rewrite
#    f. Run full test suite: go test ./... -count=1

# 3. PR
gh pr create \
  --title "feat: WebSocket terminal with xterm.js UI" \
  --body "## What
- WebSocket endpoint at /api/terminal/ws for real-time agent chat
- xterm.js-based terminal UI replacing the chat bubble interface
- JWT auth via ?token= query parameter
- WSChannel for orchestrator integration

## Phase 1 (this PR)
Full-response delivery over WebSocket (not token-streaming yet).

## Phase 2 (follow-up)
Token-by-token streaming via StreamChat provider interface.

## Testing
- 9 WS handler tests (auth, chat, timeout, malformed)
- WSChannel unit tests
- Manual: open /terminal, select agent, send message" \
  --base main
```

---

## 9. Open Questions for Bowen

1. **Auth for terminal page itself** — Should `/terminal` (the HTML page) require auth, or only the WS endpoint? Currently `/terminal` is unauthenticated (non-API route). Recommendation: keep page public, auth on WS connect.

2. **Session persistence** — Should terminal history survive page refresh? Could store in localStorage. Recommendation: yes, save last 100 messages to localStorage.

3. **Multi-agent tabs** — Future: allow multiple agent conversations in tabs within the terminal? For now, single agent via dropdown is sufficient.
