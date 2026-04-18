---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'rust-dev')"
---

# Rust Development Skill

**Purpose:** Rust programming with LSP support for ClawChain Substrate development

## Tools Installed

- **rustc:** 1.93.0 (Rust compiler)
- **cargo:** 1.93.0 (Package manager & build tool)
- **rust-analyzer:** 1.93.0 (LSP for IDE features)

## Usage

### Initialize Rust Project

```bash
source $HOME/.cargo/env
cargo new my_project
cd my_project
```

### Build & Test

```bash
cargo build           # Compile
cargo test            # Run tests
cargo check           # Fast syntax check
cargo clippy          # Linter
cargo fmt             # Format code
```

### Substrate Development

```bash
# Add Substrate dependencies to Cargo.toml
cargo add frame-support
cargo add frame-system
cargo add parity-scale-codec

# Build pallet
cargo build --release
```

### LSP Features (rust-analyzer)

The LSP provides:
- Type inference
- Code completion
- Jump to definition
- Inline errors
- Refactoring suggestions

**Note:** LSP runs automatically when editing `.rs` files with compatible editors.

## Environment

Always source Cargo environment first:

```bash
source $HOME/.cargo/env
```

This adds `~/.cargo/bin` to PATH.

## For ClawChain

When building Substrate pallets:

1. Create pallet structure
2. Define storage, events, errors
3. Implement extrinsics
4. Write tests
5. Build with `cargo build --release`

Rust-analyzer will provide real-time feedback while coding.

## References

- Rust docs: https://doc.rust-lang.org/
- Cargo book: https://doc.rust-lang.org/cargo/
- Substrate docs: https://docs.substrate.io/
- rust-analyzer: https://rust-analyzer.github.io/

