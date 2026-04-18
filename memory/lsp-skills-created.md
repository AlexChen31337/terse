# LSP Skills for OpenClaw

**Created:** 2026-02-05  
**Status:** ✅ Installed and ready

---

## Overview

Adapted official Claude Code LSP plugins to OpenClaw skills format, enabling language server protocol support for Python, TypeScript, Go, and Solidity development.

## Created Skills

### 1. pyright-lsp
**Location:** `~/.openclaw/skills/pyright-lsp`  
**Package:** `/home/bowen/clawd/pyright-lsp.skill`

**Capabilities:**
- Python static type checking
- Code intelligence (autocomplete, go-to-definition)
- Real-time error detection
- Supports `.py` and `.pyi` files

**Installation:**
```bash
npm install -g pyright
# or
pip install pyright
# or
pipx install pyright  # recommended
```

**Usage:**
```bash
pyright path/to/file.py
pyright  # entire project
```

---

### 2. typescript-lsp
**Location:** `~/.openclaw/skills/typescript-lsp`  
**Package:** `/home/bowen/clawd/typescript-lsp.skill`

**Capabilities:**
- TypeScript/JavaScript type checking
- Code intelligence (autocomplete, refactoring)
- Real-time diagnostics
- Supports `.ts`, `.tsx`, `.js`, `.jsx` files

**Installation:**
```bash
npm install -g typescript
```

**Usage:**
```bash
tsc --noEmit  # type check only
tsc --watch --noEmit  # continuous checking
```

---

### 3. gopls-lsp
**Location:** `~/.openclaw/skills/gopls-lsp`  
**Package:** `/home/bowen/clawd/gopls-lsp.skill`

**Capabilities:**
- Go code intelligence (autocomplete, go-to-def, find refs)
- Real-time error detection
- Refactoring (rename, extract function)
- Static analysis and code suggestions
- Supports `.go` files

**Installation:**
```bash
go install golang.org/x/tools/gopls@latest
# Make sure $GOPATH/bin or $HOME/go/bin is in PATH
```

**Usage:**
```bash
gofmt -w file.go  # format
go vet ./...      # lint
go build ./...    # compile
go test ./...     # test
```

---

### 4. solidity-lsp
**Location:** `~/.openclaw/skills/solidity-lsp`  
**Package:** `/home/bowen/clawd/solidity-lsp.skill`

**Capabilities:**
- Smart contract compilation (solc)
- Linting and security analysis (solhint)
- Gas optimization detection
- Supports `.sol` files
- **ClawChain ready**: Includes Substrate/ink! guidance

**Installation:**
```bash
npm install -g solc solhint
```

**Usage:**
```bash
solcjs --bin --abi contract.sol
solhint 'contracts/**/*.sol'
```

**Includes:** `references/frameworks.md` with Hardhat/Foundry/ink! setup guides

---

## Verification

```bash
$ openclaw skills list | grep -E "(pyright|typescript|gopls|solidity)"
│ ✓ ready   │ 📦 gopls-lsp      │ Go language server...        │ openclaw-workspace │
│ ✓ ready   │ 📦 pyright-lsp    │ Python language server...    │ openclaw-workspace │
│ ✓ ready   │ 📦 solidity-lsp   │ Solidity language server...  │ openclaw-workspace │
│ ✓ ready   │ 📦 typescript-lsp │ TypeScript language server...│ openclaw-workspace │
```

All four skills show ✓ ready status!

---

## Source

Adapted from Anthropic's official Claude Code plugins:
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pyright-lsp
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/typescript-lsp
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/gopls-lsp
- Solidity LSP is custom-created for ClawChain development

---

## Next Steps

1. **Test skills** on real code files
2. **Consider publishing to ClawHub** after validation (7-day GitHub account requirement: Feb 12, 2026)
3. **Add more LSP skills** as needed (Rust, C++, Java, etc.)
4. **Integrate with ClawChain** development workflow

---

## Benefits

- **Token efficient**: LSP diagnostics run externally, don't bloat context
- **Deterministic**: Compiler/linter output is reliable
- **Professional**: Industry-standard tooling
- **ClawChain ready**: Solidity skill includes Substrate/ink! support

**For ClawChain development:** The solidity-lsp skill is essential for building and validating smart contract pallets. Combined with the substrate framework knowledge, we have end-to-end blockchain development capability! 🚀
