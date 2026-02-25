# ClawChain Testnet Faucet — Technical Plan

**Issue:** clawinfra/claw-chain#33
**Branch:** `feat/testnet-faucet`
**Location:** `services/faucet/`

---

## 1. Architecture Overview + Data Flow

Single Express.js server serving both API and static frontend. SQLite for rate-limit state. @polkadot/api for on-chain transfers.

```
User Browser
    │
    ├─ GET /              → serves static index.html
    ├─ POST /faucet       → rate-limit check → transfer CLAW → return tx_hash
    ├─ GET /status        → faucet balance + stats
    ├─ GET /auth/github   → GitHub OAuth redirect
    └─ GET /auth/github/callback → sets session cookie, redirects to /
    
POST /faucet flow:
  1. Extract IP from req (X-Forwarded-For or remoteAddress)
  2. Parse body: { address: string, github_token?: string }
  3. Check IP rate limit: ≤10 req/hr (SQLite query)
  4. Check address rate limit: last drip >24h ago (SQLite query)
  5. Determine amount: 1000 CLAW if valid github session, else 100 CLAW
  6. Connect @polkadot/api → transfer from FAUCET_SEED account
  7. Record drip in SQLite
  8. Return { tx_hash, amount, next_drip_at }
```

## 2. File Structure + Function Signatures

```
services/faucet/
├── package.json
├── tsconfig.json
├── Dockerfile
├── .env.example
├── README.md
├── src/
│   ├── index.ts              # Entry point
│   ├── server.ts             # Express app factory
│   ├── config.ts             # Env config loader
│   ├── db.ts                 # SQLite setup + queries
│   ├── chain.ts              # Polkadot API + transfer
│   ├── routes/
│   │   ├── faucet.ts         # POST /faucet
│   │   ├── status.ts         # GET /status
│   │   └── auth.ts           # GitHub OAuth routes
│   └── middleware/
│       └── rateLimit.ts      # IP rate limiting middleware
├── public/
│   └── index.html            # Single-page frontend (HTML+CSS+JS inline)
└── tests/
    ├── db.test.ts
    ├── faucet.test.ts
    └── rateLimit.test.ts
```

### Function Signatures

**`src/config.ts`**
```typescript
export interface Config {
  port: number;           // default 3000
  rpcUrl: string;         // e.g. ws://localhost:9944
  faucetSeed: string;     // sr25519 seed phrase
  githubClientId: string;
  githubClientSecret: string;
  sessionSecret: string;  // for express-session
  dbPath: string;         // default ./faucet.db
  dripAmount: bigint;     // 100 * 10^12 (100 CLAW, 12 decimals)
  boostAmount: bigint;    // 1000 * 10^12
  cooldownMs: number;     // 24 * 60 * 60 * 1000
  ipRateLimit: number;    // 10 req/hr
}
export function loadConfig(): Config;
```

**`src/db.ts`**
```typescript
import Database from 'better-sqlite3';

export function initDb(dbPath: string): Database.Database;
// Creates tables if not exist

export function recordDrip(db: Database.Database, address: string, ip: string, amount: string, txHash: string): void;

export function getLastDrip(db: Database.Database, address: string): { created_at: string; amount: string } | undefined;

export function getIpRequestCount(db: Database.Database, ip: string, windowMs: number): number;

export function getStats(db: Database.Database): { total_drips: number; total_amount: string; unique_addresses: number };
```

**`src/chain.ts`**
```typescript
import { ApiPromise } from '@polkadot/api';

export async function connectChain(rpcUrl: string): Promise<ApiPromise>;

export async function transferClaw(
  api: ApiPromise,
  seed: string,
  toAddress: string,
  amount: bigint
): Promise<string>;
// Returns tx hash. Throws on failure.

export async function getFaucetBalance(api: ApiPromise, seed: string): Promise<string>;
// Returns free balance as string
```

**`src/routes/faucet.ts`**
```typescript
import { Router } from 'express';
// POST /faucet
// Body: { address: string }
// Session may contain: req.session.githubUser (set by OAuth)
// Response 200: { tx_hash: string, amount: string, next_drip_at: string }
// Response 429: { error: string, next_drip_at: string }
// Response 400: { error: string }
// Response 500: { error: string }
export function faucetRouter(deps: { db, api, config }): Router;
```

**`src/routes/status.ts`**
```typescript
// GET /status
// Response 200: { balance: string, total_drips: number, total_amount: string, unique_addresses: number }
export function statusRouter(deps: { db, api, config }): Router;
```

**`src/routes/auth.ts`**
```typescript
// GET /auth/github → redirects to GitHub OAuth
// GET /auth/github/callback → sets session, redirects to /
// GET /auth/logout → destroys session, redirects to /
// GET /auth/me → { authenticated: boolean, username?: string }
export function authRouter(deps: { config }): Router;
```

**`src/middleware/rateLimit.ts`**
```typescript
// Express middleware: checks IP against 10 req/hr limit
// Returns 429 if exceeded
export function ipRateLimitMiddleware(deps: { db, config }): RequestHandler;
```

**`src/server.ts`**
```typescript
export async function createApp(config: Config): Promise<Express>;
// Wires up all routes, middleware, static serving, session, passport
```

**`src/index.ts`**
```typescript
// Loads config, calls createApp, listens on port
```

## 3. Interface Definitions

### API

| Method | Path | Body/Query | Success | Error |
|--------|------|-----------|---------|-------|
| POST | /faucet | `{ address: string }` | 200 `{ tx_hash, amount, next_drip_at }` | 400/429/500 `{ error, next_drip_at? }` |
| GET | /status | — | 200 `{ balance, total_drips, total_amount, unique_addresses }` | 500 |
| GET | /auth/github | — | 302 → GitHub | — |
| GET | /auth/github/callback | `?code=` | 302 → / | 302 → /?error=auth_failed |
| GET | /auth/me | — | 200 `{ authenticated, username? }` | — |
| GET | /auth/logout | — | 302 → / | — |

### Config (.env.example)

```
RPC_URL=ws://localhost:9944
FAUCET_SEED=//Alice
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
SESSION_SECRET=change-me
PORT=3000
DB_PATH=./faucet.db
```

### Frontend (public/index.html)

Single HTML file with inline CSS and JS. No build step.

**Design:**
- Background: `#0a0a0a`, accent: `#00D4FF`
- ClawChain logo/title at top
- Single input field for SS58 address + "Request 100 CLAW" button
- "GitHub Boost x10" button (links to /auth/github, then auto-requests 1000)
- On success: display tx hash (linked to explorer if available)
- On cooldown: countdown timer showing time until next_drip_at
- On error: red error message
- GET /auth/me on page load to show GitHub status
- GET /status on page load to show faucet balance + stats

**JS flow:**
1. `checkAuth()` → GET /auth/me → toggle boost button visibility
2. `checkStatus()` → GET /status → display balance/stats
3. `requestDrip(address)` → POST /faucet → show result/countdown/error
4. Countdown timer: `setInterval` updating display until next_drip_at

## 4. Data Models and Schemas

### SQLite: `drips` table

```sql
CREATE TABLE IF NOT EXISTS drips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  address TEXT NOT NULL,
  ip TEXT NOT NULL,
  amount TEXT NOT NULL,
  tx_hash TEXT NOT NULL,
  github_user TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_drips_address ON drips(address);
CREATE INDEX IF NOT EXISTS idx_drips_ip_created ON drips(ip, created_at);
```

### Express Session

Use `express-session` with `connect-sqlite3` store (same DB file or separate session.db). Session contains:
```typescript
declare module 'express-session' {
  interface SessionData {
    githubUser?: { username: string; id: number };
    pendingBoost?: boolean; // set before OAuth redirect, consumed after callback
  }
}
```

## 5. Error Handling Strategy

| Scenario | HTTP | Response |
|----------|------|----------|
| Invalid/missing address | 400 | `{ error: "Invalid SS58 address" }` |
| Address cooldown | 429 | `{ error: "Address rate limited", next_drip_at: "<ISO>" }` |
| IP rate limit | 429 | `{ error: "Too many requests", retry_after: <seconds> }` |
| Chain connection failed | 503 | `{ error: "Chain unavailable" }` |
| Transfer failed | 500 | `{ error: "Transfer failed" }` |
| Insufficient faucet balance | 503 | `{ error: "Faucet depleted" }` |

- Validate SS58 address using `@polkadot/util-crypto` `decodeAddress` (wrap in try/catch)
- All chain operations wrapped in try/catch with specific error messages
- Global Express error handler for unhandled exceptions → 500
- Log errors to stderr with timestamp

## 6. Test Plan

### Unit Tests (vitest)

**`tests/db.test.ts`**
- `initDb` creates tables on fresh DB
- `recordDrip` inserts row correctly
- `getLastDrip` returns latest drip for address, undefined if none
- `getIpRequestCount` counts correctly within window, ignores outside window
- `getStats` returns correct aggregates

**`tests/faucet.test.ts`** (supertest + mocked chain)
- POST /faucet with valid address → 200, correct shape
- POST /faucet with invalid address → 400
- POST /faucet when address on cooldown → 429 with next_drip_at
- POST /faucet when IP rate limited → 429
- POST /faucet with GitHub session → amount=1000
- POST /faucet without GitHub session → amount=100
- POST /faucet when chain unavailable → 503

**`tests/rateLimit.test.ts`**
- Allows requests under limit
- Blocks at limit boundary
- Resets after window expires

### Integration (manual, documented in README)
- Start local substrate node, run faucet, request via curl
- Verify on-chain balance change

## 7. Constraints and Assumptions

- **Node.js 18+**, TypeScript with ESM
- **Dependencies:** express, better-sqlite3, @polkadot/api, @polkadot/util-crypto, passport, passport-github2, express-session, connect-sqlite3
- **Dev deps:** typescript, vitest, supertest, @types/*
- **12 decimal places** for CLAW (standard Substrate). 100 CLAW = 100_000_000_000_000 planck
- **SS58 prefix:** use chain default (or 42 for generic Substrate)
- FAUCET_SEED is a mnemonic or `//DevAccount` style URI
- Single-process, no clustering needed for testnet traffic
- SQLite is sufficient — no need for Postgres
- GitHub OAuth callback URL: `https://faucet.clawchain.win/auth/github/callback`
- Trust `X-Forwarded-For` header (behind reverse proxy). Builder should use first value only.
- Dockerfile: multi-stage build, node:18-slim base, expose PORT
- No WebSocket/SSE — frontend polls on user action only

### Git/PR Plan
1. Clone `clawinfra/claw-chain` to `/tmp/claw-chain-faucet`
2. Branch `feat/testnet-faucet` from main
3. Create all files under `services/faucet/`
4. Commit with message: `feat: add testnet faucet service (closes #33)`
5. Push and create PR via `gh pr create` linking issue #33
