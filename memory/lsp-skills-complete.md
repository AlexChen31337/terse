# LSP Skills - Complete Collection

**Created:** 2026-02-05  
**Status:** ✅ 6 skills installed and ready

---

## Installed LSP Skills

### 1. **pyright-lsp** (Python)
- Static type checking with Microsoft Pyright
- Extensions: `.py`, `.pyi`
- Install: `npm install -g pyright`
- Based on: [Anthropic official plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pyright-lsp)

### 2. **typescript-lsp** (TypeScript/JavaScript)
- TypeScript language server
- Extensions: `.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, `.cts`, `.mjs`, `.cjs`
- Install: `npm install -g typescript-language-server typescript`
- Based on: [Anthropic official plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/typescript-lsp)

### 3. **gopls-lsp** (Go)
- Official Go language server
- Extensions: `.go`
- Install: `go install golang.org/x/tools/gopls@latest`
- Based on: [Anthropic official plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/gopls-lsp)

### 4. **rust-analyzer-lsp** (Rust)
- Rust language server with cargo integration
- Extensions: `.rs`
- Install: `rustup component add rust-analyzer`
- Based on: [Anthropic official plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/rust-analyzer-lsp)

### 5. **clangd-lsp** (C/C++)
- LLVM-based C/C++ language server
- Extensions: `.c`, `.h`, `.cpp`, `.cc`, `.cxx`, `.hpp`, `.hxx`
- Install: `brew install llvm` (macOS) or `sudo apt install clangd` (Linux)
- Based on: [Anthropic official plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/clangd-lsp)

### 6. **solidity-lsp** (Smart Contracts)
- Solidity compiler and linter integration
- Extensions: `.sol`
- Install: `npm install -g solc solhint`
- **Custom creation** for ClawChain blockchain development
- Includes Substrate/ink! framework reference

---

## Verification

```bash
$ openclaw skills list | grep lsp | grep ready
│ ✓ ready   │ 📦 clangd-lsp          │ C/C++ language server...         │ openclaw-workspace │
│ ✓ ready   │ 📦 gopls-lsp           │ Go language server...            │ openclaw-workspace │
│ ✓ ready   │ 📦 pyright-lsp         │ Python language server...        │ openclaw-workspace │
│ ✓ ready   │ 📦 rust-analyzer-lsp   │ Rust language server...          │ openclaw-workspace │
│ ✓ ready   │ 📦 solidity-lsp        │ Solidity language server...      │ openclaw-workspace │
│ ✓ ready   │ 📦 typescript-lsp      │ TypeScript language server...    │ openclaw-workspace │
```

All 6 skills show ✓ ready status!

---

## Language Coverage

**Current:**
- ✅ Python (pyright)
- ✅ TypeScript/JavaScript (typescript-language-server)
- ✅ Go (gopls)
- ✅ Rust (rust-analyzer)
- ✅ C/C++ (clangd)
- ✅ Solidity (solc/solhint)

**Available in Anthropic plugins (not yet created):**
- Java (jdtls-lsp) - `brew install jdtls`
- C# (csharp-lsp) - OmniSharp
- PHP (php-lsp) - Intelephense via npm
- Lua (lua-lsp) - lua-language-server
- Kotlin (kotlin-lsp) - JetBrains kotlin-lsp
- Swift (swift-lsp) - SourceKit-LSP (included with Xcode/Swift)

---

## Benefits

1. **Token efficient**: LSP diagnostics run externally, don't bloat context
2. **Deterministic**: Compiler/linter output is reliable
3. **Professional**: Industry-standard tooling
4. **Language coverage**: 6 major languages supported
5. **ClawChain ready**: Solidity skill includes Substrate/ink! support

---

## Usage Pattern

When editing code:
1. LSP provides real-time diagnostics in editors
2. Run formatters (`gofmt`, `cargo fmt`, `clang-format`, etc.)
3. Run linters/checkers before committing
4. Use LSP features: go-to-def, find-refs, autocomplete

---

## Next Steps

1. ✅ 6 core languages covered (Python, TypeScript, Go, Rust, C/C++, Solidity)
2. 📋 Consider adding Java/C#/PHP if needed
3. 📤 Publish to ClawHub after Feb 12, 2026 (GitHub account age requirement)
4. 🧪 Test skills on real ClawChain codebase

---

## Files

**Skill packages:**
- `/home/bowen/clawd/pyright-lsp.skill`
- `/home/bowen/clawd/typescript-lsp.skill`
- `/home/bowen/clawd/gopls-lsp.skill`
- `/home/bowen/clawd/rust-analyzer-lsp.skill`
- `/home/bowen/clawd/clangd-lsp.skill`
- `/home/bowen/clawd/solidity-lsp.skill`

**Installed location:**
- `~/.openclaw/skills/{skill-name}/`

**Git repo:**
- All skills committed to `/home/bowen/clawd` workspace

---

## ClawChain Integration

**Solidity LSP** is specifically designed for ClawChain development with:
- Solidity smart contract compilation and analysis
- Security linting with solhint
- Gas optimization detection
- **Framework guides**: Hardhat, Foundry, and **ink!** (Substrate)

Combined with rust-analyzer, we have end-to-end support for:
- **Substrate pallets** (Rust + rust-analyzer)
- **Smart contracts** (Solidity or ink!)
- **Development tooling** (TypeScript for scripts)

Perfect stack for ClawChain blockchain development! 🦀⛓️
