---
name: typescript-lsp
description: TypeScript language server providing type checking, code intelligence, and LSP diagnostics for .ts, .tsx, .js, .jsx files. Use when working with TypeScript or JavaScript code that needs type checking, autocomplete, error detection, refactoring support, or code navigation.
---

# TypeScript LSP

TypeScript language server integration providing comprehensive type checking and code intelligence through the official TypeScript compiler.

## Capabilities

- **Type checking**: Static analysis of TypeScript and JavaScript types
- **Code intelligence**: Autocomplete, go-to-definition, find references, rename symbols
- **Error detection**: Real-time diagnostics for type errors, syntax issues, and semantic problems
- **Refactoring**: Extract function/variable, organize imports, quick fixes
- **Supported extensions**: `.ts`, `.tsx`, `.js`, `.jsx`

## Installation Check

TypeScript is typically installed per-project. Verify availability:

```bash
which tsc || npm install -g typescript
```

Check version:
```bash
tsc --version
```

## Usage

Run type checking:

```bash
tsc --noEmit  # Type check without generating output files
```

Compile TypeScript files:

```bash
tsc src/index.ts
```

Watch mode for continuous type checking:

```bash
tsc --watch --noEmit
```

## Configuration

Create `tsconfig.json` in project root:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Integration Pattern

When editing TypeScript/JavaScript code:
1. Run `tsc --noEmit` after significant changes
2. Address type errors before committing
3. Use `tsc --watch` during active development
4. Leverage quick fixes for common issues

## Common Flags

- `--noEmit`: Type check only, no output files
- `--strict`: Enable all strict type checking options
- `--watch`: Watch mode for continuous compilation
- `--project <path>`: Specify tsconfig.json location
- `--pretty`: Stylize errors and messages

## More Information

- [TypeScript Official Documentation](https://www.typescriptlang.org/docs/)
- [TypeScript Compiler Options](https://www.typescriptlang.org/tsconfig)
- [GitHub Repository](https://github.com/microsoft/TypeScript)
