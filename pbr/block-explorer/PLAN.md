# ClawChain Block Explorer — Technical Plan

**Issue:** clawinfra/claw-chain#34  
**Branch:** `feat/block-explorer`  
**Path:** `services/explorer/`  
**Deploy:** `explorer.clawchain.win`

---

## 1. Architecture Overview + Data Flow

```
Browser (Next.js CSR) ←→ @polkadot/api (WS) ←→ ClawChain Node (wss://testnet.clawchain.win)
```

- **Next.js 14 App Router** with client-side rendering for all chain data pages (WS subscriptions require browser runtime)
- **No backend/API routes** — all data fetched directly from chain RPC via `@polkadot/api`
- **Data flow:**
  1. `lib/api.ts` creates singleton `ApiPromise` connecting to `NEXT_PUBLIC_WS_URL`
  2. Pages use React hooks that call into `lib/` query functions
  3. `/blocks` page subscribes to `chain.subscribeNewHeads()` for live updates
  4. `/blocks/[hash]`, `/tx/[hash]`, `/agents/[address]` fetch on-demand via RPC
- **State management:** React `useState`/`useReducer` only — no external state library needed
- **Connection lifecycle:** Single WS connection shared across pages via React context; auto-reconnect on disconnect with exponential backoff

## 2. File Structure with Function Signatures

```
services/explorer/
├── .env.example
├── .eslintrc.json
├── Dockerfile
├── README.md
├── next.config.js
├── package.json
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json                  # strict: true, noUncheckedIndexedAccess: true
├── public/
│   └── favicon.ico
├── src/
│   ├── app/
│   │   ├── layout.tsx             # RootLayout — ApiProvider wrapper, header, dark theme
│   │   ├── page.tsx               # Redirect to /blocks
│   │   ├── globals.css            # Tailwind directives + dark theme vars
│   │   ├── blocks/
│   │   │   ├── page.tsx           # BlockListPage — "use client", live block list
│   │   │   └── [hash]/
│   │   │       └── page.tsx       # BlockDetailPage — "use client"
│   │   ├── tx/
│   │   │   └── [hash]/
│   │   │       └── page.tsx       # TxDetailPage — "use client"
│   │   └── agents/
│   │       └── [address]/
│   │           └── page.tsx       # AgentProfilePage — "use client"
│   ├── components/
│   │   ├── Header.tsx             # Logo, nav links, live block number
│   │   ├── BlockList.tsx          # Live block table with auto-scroll
│   │   ├── BlockDetail.tsx        # Single block info + extrinsic list
│   │   ├── TxDetail.tsx           # Extrinsic info + events
│   │   ├── AgentProfile.tsx       # DID + reputation + quota cards
│   │   ├── LiveIndicator.tsx      # Green/red dot for WS status
│   │   ├── LoadingState.tsx       # Skeleton/spinner
│   │   └── ErrorState.tsx         # Error display with retry button
│   ├── hooks/
│   │   ├── useApi.ts              # Access ApiPromise from context
│   │   ├── useNewHeads.ts         # Subscribe to new block headers
│   │   ├── useBlock.ts            # Fetch single block by hash
│   │   ├── useTx.ts              # Fetch extrinsic by hash
│   │   └── useAgent.ts           # Fetch agent DID + reputation + quota
│   ├── lib/
│   │   ├── api.ts                 # ApiPromise singleton + connection management
│   │   ├── format.ts             # Formatting utilities
│   │   └── types.ts              # All TypeScript interfaces
│   └── providers/
│       └── ApiProvider.tsx        # React context for @polkadot/api connection
```

### Function Signatures

#### `lib/api.ts`
```typescript
// Returns singleton ApiPromise, creates if not exists
export function getApi(wsUrl?: string): Promise<ApiPromise>;

// Disconnect and clear singleton
export function disconnectApi(): Promise<void>;
```

#### `lib/types.ts`
```typescript
export interface BlockSummary {
  hash: string;          // hex
  number: number;
  timestamp: number;     // unix ms
  extrinsicCount: number;
  producer: string;      // validator address
}

export interface BlockInfo extends BlockSummary {
  parentHash: string;
  stateRoot: string;
  extrinsicsRoot: string;
  extrinsics: ExtrinsicSummary[];
}

export interface ExtrinsicSummary {
  hash: string;
  index: number;         // index within block
  section: string;       // e.g. "agentRegistry"
  method: string;        // e.g. "registerAgent"
  signer: string | null; // null for unsigned/inherent
  success: boolean;
}

export interface ExtrinsicInfo extends ExtrinsicSummary {
  blockHash: string;
  blockNumber: number;
  args: Record<string, unknown>;
  events: DecodedEvent[];
  tip: string;
  fee: string;
}

export interface DecodedEvent {
  section: string;
  method: string;
  data: Record<string, unknown>;
}

export interface AgentInfo {
  address: string;
  did: string | null;         // from pallet-agent-registry
  reputation: number | null;  // from pallet-reputation
  reputationHistory: { block: number; score: number }[];
  gasQuota: {
    remaining: string;
    total: string;
    lastRefill: number;
  } | null;                   // from pallet-gas-quota
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";
```

#### `lib/format.ts`
```typescript
export function shortenHash(hash: string, chars?: number): string;  // default 6
export function formatTimestamp(unixMs: number): string;             // relative "5s ago"
export function formatAddress(address: string): string;             // SS58 shortened
export function formatBalance(raw: string, decimals?: number): string;
```

#### `providers/ApiProvider.tsx`
```typescript
// Props: { wsUrl: string; children: ReactNode }
// Context value: { api: ApiPromise | null; status: ConnectionStatus; blockNumber: number | null }
// Handles: connect on mount, reconnect with exponential backoff (1s, 2s, 4s, max 30s), disconnect on unmount
```

#### `hooks/useApi.ts`
```typescript
export function useApi(): { api: ApiPromise | null; status: ConnectionStatus; blockNumber: number | null };
```

#### `hooks/useNewHeads.ts`
```typescript
// Returns latest N block headers, auto-updates via subscription
// maxBlocks default 50, older blocks dropped from array
export function useNewHeads(maxBlocks?: number): { blocks: BlockSummary[]; loading: boolean; error: string | null };
```

#### `hooks/useBlock.ts`
```typescript
export function useBlock(hash: string): { block: BlockInfo | null; loading: boolean; error: string | null };
```

#### `hooks/useTx.ts`
```typescript
// Fetches extrinsic by hash — searches recent blocks or uses indexer if available
export function useTx(hash: string): { tx: ExtrinsicInfo | null; loading: boolean; error: string | null };
```

#### `hooks/useAgent.ts`
```typescript
// Queries pallet-agent-registry, pallet-reputation, pallet-gas-quota for address
export function useAgent(address: string): { agent: AgentInfo | null; loading: boolean; error: string | null };
```

### Component Props

```typescript
// Header: no props (uses useApi for block number + LiveIndicator)
// BlockList: { blocks: BlockSummary[]; loading: boolean }
// BlockDetail: { block: BlockInfo }
// TxDetail: { tx: ExtrinsicInfo }
// AgentProfile: { agent: AgentInfo }
// LiveIndicator: { status: ConnectionStatus }
// LoadingState: { text?: string }
// ErrorState: { message: string; onRetry?: () => void }
```

## 3. Interface Definitions

### Config (Environment)

`.env.example`:
```
NEXT_PUBLIC_WS_URL=wss://testnet.clawchain.win
```

No other config needed. No API keys, no backend.

### CLI

No CLI. This is a web app only.

### URLs / Routes

| Route | Description |
|---|---|
| `/` | Redirect → `/blocks` |
| `/blocks` | Live block list, newest first |
| `/blocks/[hash]` | Block detail with extrinsic list |
| `/tx/[hash]` | Extrinsic detail with decoded events |
| `/agents/[address]` | Agent DID, reputation, gas quota |

## 4. Data Models and Schemas

All types defined in `lib/types.ts` (see §2 above). No database. No server-side state. All data is ephemeral, fetched from chain RPC.

### Pallet Storage Queries

| Pallet | Storage/Call | Used For |
|---|---|---|
| `system` | `chain.getBlock(hash)` | Block detail |
| `system` | `chain.subscribeNewHeads()` | Live block feed |
| `timestamp` | `timestamp.now()` at block | Block timestamp |
| `agentRegistry` | `agentRegistry.agents(address)` | Agent DID lookup |
| `reputation` | `reputation.scores(address)` | Reputation score |
| `gasQuota` | `gasQuota.quotas(address)` | Gas quota info |

**Note:** Exact storage key names may differ from actual pallet implementation. Builder MUST check pallet source at `pallets/agent-registry/`, `pallets/reputation/`, `pallets/gas-quota/` for actual storage item names and decode accordingly. If the node is unreachable at build time, use try/catch with graceful "data unavailable" fallback.

## 5. Error Handling Strategy

| Scenario | Handling |
|---|---|
| WS connection fails on load | Show `ErrorState` with retry button; `LiveIndicator` red |
| WS disconnects mid-session | Auto-reconnect with exponential backoff (1s→2s→4s→…→30s max); show yellow indicator during reconnect; blocks list freezes but preserves existing data |
| Block/tx hash not found | Show "Not found" page with link back to /blocks |
| Agent address has no DID/reputation | Show "No data" for missing fields, not an error |
| Pallet query fails (pallet doesn't exist on chain) | Catch, show "Unavailable" badge for that section |
| RPC timeout (>10s) | Abort, show error with retry |
| Invalid hash/address in URL | Validate format client-side, show "Invalid" message |

All hooks return `{ data, loading, error }` triple. Components render `LoadingState` when loading, `ErrorState` when error, data when available.

## 6. Test Plan

### Unit Tests (Vitest)
- `lib/format.ts` — all formatting functions with edge cases (empty hash, 0 timestamp, etc.)
- `lib/types.ts` — type guards if any

### Component Tests (Vitest + React Testing Library)
- `LoadingState` — renders spinner
- `ErrorState` — renders message + retry button fires callback
- `LiveIndicator` — renders correct color for each ConnectionStatus
- `BlockList` — renders table rows from BlockSummary[]
- `BlockDetail` — renders all fields from BlockInfo
- `TxDetail` — renders decoded events
- `AgentProfile` — renders with null fields gracefully
- `Header` — renders nav links and block number

### Integration Tests (Vitest + mocked @polkadot/api)
- `useNewHeads` — mock subscribeNewHeads, verify blocks array updates
- `useBlock` — mock getBlock, verify BlockInfo mapping
- `useAgent` — mock pallet queries, verify AgentInfo assembly
- `ApiProvider` — mock connect/disconnect lifecycle

### E2E (Playwright — stretch goal, not blocking PR)
- Navigate /blocks → see block list
- Click block → /blocks/[hash] loads
- Click extrinsic → /tx/[hash] loads
- Navigate /agents/[address] → see profile

### Coverage Target
≥ 90% on `lib/` and `hooks/`. Components ≥ 80%.

## 7. Constraints and Assumptions

1. **No indexer/database** — all data from live RPC. This means tx lookup by hash requires iterating recent blocks (limitation acknowledged; future indexer can be added).
2. **Pallets exist on testnet** — `agent-registry`, `reputation`, `gas-quota` are deployed. If not, those sections show "unavailable" gracefully.
3. **@polkadot/api v10+** compatible with ClawChain's Substrate runtime.
4. **Next.js 14 App Router** with `"use client"` for all data pages (WS requires browser).
5. **No SSR for chain data** — layout/shell is SSR, chain data is CSR only.
6. **Tailwind dark theme:** bg `#0a0a0a`, accent `#00D4FF`, text `#E5E7EB` (gray-200), secondary text `#9CA3AF` (gray-400).
7. **Dependencies:** `next@14`, `react@18`, `@polkadot/api`, `tailwindcss`, `vitest`, `@testing-library/react`, `playwright` (dev).
8. **Dockerfile:** Multi-stage (node:20-alpine build → node:20-alpine runner), output standalone.
9. **Git workflow:** Clone `clawinfra/claw-chain` to `/tmp/claw-chain-explorer`, branch `feat/block-explorer`, all files under `services/explorer/`, PR body references "Closes #34".
10. **Max 50 blocks in live list** — older blocks pruned from memory to prevent unbounded growth.
11. **No authentication** — public read-only explorer.
12. **Responsive** — mobile-friendly but desktop-first.
