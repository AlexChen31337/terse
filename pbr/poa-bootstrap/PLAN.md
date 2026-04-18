# PLAN: ADR-001 PoA Bootstrap for ClawChain

**Issue:** clawinfra/claw-chain#28  
**Branch:** `feat/poa-bootstrap`  
**Working clone:** `/tmp/claw-chain-poa`

---

## 1. Architecture Overview + Data Flow

### What We're Building
A `public_testnet_config()` chain spec with 3 PoA validators (Aura/GRANDPA), wired as `--chain testnet`. The existing `testnet_genesis()` function already handles session keys, staking, balances, and sudo — we reuse it with testnet-specific parameters.

### Data Flow
```
CLI: --chain testnet
  → command.rs::load_spec("testnet")
    → chain_spec::public_testnet_config()
      → testnet_genesis(3 authorities, sudo=Validator1, endowed accounts, false)
        → JSON genesis patch (balances, session, staking, sudo)
```

### VPS Deployment Flow
```
1. SSH to root@135.181.157.121
2. Stop existing raw clawchain-node process (pkill or kill)
3. Write systemd unit file
4. systemctl daemon-reload && enable && start
5. Verify blocks via curl localhost:9944 (RPC health)
```

---

## 2. File Structure with Exact Function Signatures

### File: `node/src/chain_spec.rs`

**Add one new public function:**

```rust
/// Public testnet chain spec — 3 PoA authorities (Validator1, Validator2, Validator3).
/// 
/// ADR-001: Initial PoA bootstrap. Expandable to 7-10 validators via sudo governance.
/// TODO(PoS-transition): Replace invulnerables with elected set via pallet-election-provider-multi-phase.
/// TODO(PoS-transition): Remove sudo pallet once council governance is active.
pub fn public_testnet_config() -> Result<ChainSpec, String>
```

**Implementation spec:**
- WASM binary: same `WASM_BINARY` check as other configs
- Name: `"ClawChain Public Testnet"`
- ID: `"clawchain_testnet_public"`
- Chain type: `ChainType::Live`
- Protocol ID: `"clawchain-testnet"`
- Initial authorities (3): `authority_keys_from_seed("Validator1")`, `authority_keys_from_seed("Validator2")`, `authority_keys_from_seed("Validator3")`
- Sudo: `get_account_id_from_seed::<sr25519::Public>("Validator1")`
- Endowed accounts list:
  - Validator1, Validator2, Validator3 (controller accounts)
  - Validator1//stash, Validator2//stash, Validator3//stash (stash accounts — added automatically by `testnet_genesis`)
  - Treasury account (see below)
- `_enable_println`: `false`
- Bootnodes: empty vec (added later via chain spec JSON export)
- Telemetry: None

**Token distribution — modify `testnet_genesis()` or create a new genesis builder:**

The existing `testnet_genesis()` splits `VALIDATOR_ALLOCATION + TREASURY_ALLOCATION` equally among all endowed accounts. For public testnet, we need explicit control:

**Option chosen: New function `public_testnet_genesis()`** to avoid breaking dev/local configs.

```rust
/// Genesis config for public testnet with explicit token distribution.
///
/// Distribution:
/// - Each validator stash: STASH (1M CLAW) for staking bond
/// - Each validator controller: 100_000 CLAW for transaction fees
/// - Treasury account: TREASURY_ALLOCATION (20% of total supply)
/// - Sudo (Validator1): additional 100_000 CLAW for governance txs
fn public_testnet_genesis(
    initial_authorities: Vec<(AccountId, AccountId, AuraId, GrandpaId)>,
    root_key: AccountId,
) -> serde_json::Value
```

**Balance entries (computed inside `public_testnet_genesis`):**
- Each authority stash (`x.0`): `STASH` (1_000_000 * 10^12)
- Each authority controller (`x.1`): `100_000 * 10^12`
- Treasury account (derived from `TreasuryPalletId` = `b"py/trsry"`): `TREASURY_ALLOCATION` (200_000_000 * 10^12)
- Note: Treasury PalletId account derivation needs import. Use: `use sp_runtime::traits::AccountIdConversion; use frame_support::PalletId;` then `PalletId(*b"py/trsry").into_account_truncating()`

**Session, staking, sudo JSON blocks:** identical structure to existing `testnet_genesis()`, just with the 3 validators.

**Add constant:**
```rust
/// Controller account operating balance (100k CLAW)
const CONTROLLER_BALANCE: Balance = 100_000 * 10u128.pow(12);
```

### File: `node/src/command.rs`

**Change in `load_spec()`:** Add one match arm:

```rust
"testnet" => Box::new(chain_spec::public_testnet_config()?),
```

Insert between `"local"` and the `path =>` fallback arm. Exact location: after line `"local" => Box::new(chain_spec::local_testnet_config()?),`.

### File: `/etc/systemd/system/clawchain-node.service` (on VPS)

```ini
[Unit]
Description=ClawChain Node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/root/clawchain-node \
    --chain local \
    --name "clawchain-vps-01" \
    --rpc-port 9944 \
    --rpc-cors all \
    --rpc-methods Safe \
    --rpc-external \
    --prometheus-external \
    --base-path /root/.local/share/clawchain-node
Restart=on-failure
RestartSec=10
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

**Note:** Uses `--chain local` now (not `testnet`) because testnet binary needs a rebuild with the new chain spec. The Builder should add a comment in the unit file noting this will change to `--chain testnet` after binary rebuild.

---

## 3. Interface Definitions (API, CLI, Config)

### CLI Interface
```
clawchain-node --chain testnet    # Uses public_testnet_config()
clawchain-node --chain local      # Existing local_testnet_config()
clawchain-node --chain dev        # Existing development_config()
clawchain-node --chain ""         # Defaults to dev (existing behavior)
clawchain-node --chain <path>     # Load from JSON file (existing behavior)
```

### Exported Chain Spec
After implementation, running `clawchain-node build-spec --chain testnet --raw > testnet-raw.json` should produce a valid raw chain spec. This is NOT part of the PR but should be verified.

---

## 4. Data Models and Schemas

### Authority Key Tuple (existing, unchanged)
```rust
(AccountId, AccountId, AuraId, GrandpaId)
// (stash_account, controller_account, aura_sr25519_key, grandpa_ed25519_key)
```

### Genesis JSON Patch Structure (output of `public_testnet_genesis`)
```json
{
  "balances": {
    "balances": [
      ["<Validator1//stash>", 1000000000000000000],
      ["<Validator1>",        100000000000000000],
      ["<Validator2//stash>", 1000000000000000000],
      ["<Validator2>",        100000000000000000],
      ["<Validator3//stash>", 1000000000000000000],
      ["<Validator3>",        100000000000000000],
      ["<TreasuryPalletAccount>", 200000000000000000000000]
    ]
  },
  "session": {
    "keys": [
      ["<stash>", "<stash>", {"aura": "<aura_key>", "grandpa": "<grandpa_key>"}]
    ]
  },
  "staking": {
    "validatorCount": 3,
    "minimumValidatorCount": 2,
    "invulnerables": ["<stash1>", "<stash2>", "<stash3>"],
    "stakers": [
      ["<stash>", "<controller>", 1000000000000000000, "Validator"]
    ]
  },
  "sudo": { "key": "<Validator1>" }
}
```

**Key difference from dev/local:** `minimumValidatorCount` is **2** (not 1) for liveness in a 3-validator set (tolerates 1 offline).

---

## 5. Error Handling Strategy

- `WASM_BINARY` unavailable: return `Err("Development wasm not available")` — same as existing configs
- `PalletId` import failure: compile-time error, no runtime handling needed
- VPS SSH failure: Builder should check SSH connectivity first, abort with clear error if unreachable
- Existing process on VPS: use `pkill -f clawchain-node` or find PID via `pgrep -f clawchain-node` — if no process found, continue silently
- Systemd start failure: check `journalctl -u clawchain-node -n 50` for diagnostics
- Cargo clippy warnings: must be zero warnings (deny all). Run: `cargo clippy --all-targets -- -D warnings`

---

## 6. Test Plan

### 6.1 Compilation & Lint
```bash
cd /tmp/claw-chain-poa
cargo clippy --all-targets -- -D warnings  # Must be clean
cargo test --all                             # All existing tests pass
```

### 6.2 Chain Spec Validation
```bash
# Verify testnet spec generates valid JSON
cargo run -- build-spec --chain testnet 2>/dev/null | jq '.id' 
# Expected: "clawchain_testnet_public"

cargo run -- build-spec --chain testnet 2>/dev/null | jq '.chainType'
# Expected: "Live"

cargo run -- build-spec --chain testnet 2>/dev/null | jq '.genesis' | head
# Should contain balances, session, staking, sudo sections
```

### 6.3 Existing Configs Unbroken
```bash
cargo run -- build-spec --chain dev 2>/dev/null | jq '.id'
# Expected: "clawchain_dev"

cargo run -- build-spec --chain local 2>/dev/null | jq '.id'  
# Expected: "clawchain_local_testnet"
```

### 6.4 VPS Verification
```bash
ssh -i ~/.ssh/id_ed25519_alexchen root@135.181.157.121 \
    "systemctl is-active clawchain-node && curl -s -H 'Content-Type: application/json' \
    -d '{\"id\":1,\"jsonrpc\":\"2.0\",\"method\":\"system_health\",\"params\":[]}' \
    http://localhost:9944 | jq '.result.peers'"
# Expected: service active, peers >= 0, isSyncing field present
```

### 6.5 Authority Count Verification
```bash
cargo run -- build-spec --chain testnet 2>/dev/null | jq '.genesis.runtimeGenesis.patch.session.keys | length'
# Expected: 3

cargo run -- build-spec --chain testnet 2>/dev/null | jq '.genesis.runtimeGenesis.patch.staking.validatorCount'
# Expected: 3
```

---

## 7. Constraints and Assumptions

### Constraints
1. **No new dependencies** — only use imports already available in `node/` crate (sp_runtime, frame_support for PalletId)
2. **`node/Cargo.toml` may need `frame-support` added** — check if PalletId is available. If not, use raw account derivation or hardcode the treasury account bytes. Prefer adding the dep.
3. **Cargo clippy must be clean** — zero warnings with `-D warnings`
4. **Existing dev/local configs must not change** — `testnet_genesis()` stays untouched
5. **VPS currently uses `--chain local`** — testnet binary not yet deployed, service starts with local chain
6. **Branch: `feat/poa-bootstrap`** — branched from `main`
7. **PR links issue #28** — body must contain `Closes #28` or `Fixes #28`

### Assumptions
1. `gh` CLI is authenticated as AlexChen31337 and has push access to clawinfra/claw-chain
2. SSH key `~/.ssh/id_ed25519_alexchen` has root access to 135.181.157.121
3. The VPS has a `clawchain-node` binary at `/root/clawchain-node` (or discoverable via `which`/`find`)
4. WASM binary builds successfully with current toolchain
5. `authority_keys_from_seed("Validator1")` produces deterministic dev keys (fine for testnet bootstrap, real keys rotated later)
6. Treasury PalletId `b"py/trsry"` matches runtime config (verified: line 412 of runtime/src/lib.rs)
7. The VPS may have an existing raw clawchain-node process (not systemd-managed) that must be stopped first

### PoS Transition Path (Comments Only)
The Builder must add these as `// TODO(PoS-transition):` comments in `public_testnet_config()`:
1. Replace `authority_keys_from_seed` with real externally-generated keys
2. Add `pallet-election-provider-multi-phase` for validator election
3. Remove `invulnerables` once sufficient stake is bonded
4. Transition sudo to council-based governance
5. Increase `validatorCount` to 7-10 as network grows

### Git Workflow
```bash
cd /tmp/claw-chain-poa
git checkout -b feat/poa-bootstrap
# ... make changes ...
cargo clippy --all-targets -- -D warnings
cargo test --all
git add -A
git commit -m "feat: ADR-001 PoA bootstrap with 3-validator testnet config

- Add public_testnet_config() with Validator1/2/3 authorities
- Wire --chain testnet in command.rs
- 1M CLAW stash per validator, 20% treasury allocation
- minimumValidatorCount=2 for Byzantine tolerance
- PoS transition path documented as TODO comments

Closes #28"
git push -u origin feat/poa-bootstrap
gh pr create --title "feat: ADR-001 PoA bootstrap for public testnet" \
    --body "Implements #28 — ADR-001 PoA bootstrap.

## Changes
- \`public_testnet_config()\` in chain_spec.rs with 3 authorities
- \`--chain testnet\` wired in command.rs  
- Explicit token distribution (1M CLAW/validator, 20% treasury)
- PoS transition TODO comments

## VPS
- systemd service created on 135.181.157.121
- Running with \`--chain local\` until testnet binary deployed

Closes #28" \
    --base main
```
