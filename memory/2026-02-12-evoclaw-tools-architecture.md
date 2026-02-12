# EvoClaw Desktop Parity Tool Suite - Architecture Design

**Date:** 2026-02-12  
**Version:** 1.0  
**Status:** Implementation Ready  

---

## 1. Executive Summary

This document defines the architecture for a comprehensive tool suite that brings EvoClaw to desktop feature parity with OpenClaw. The suite implements 14 essential tools across file operations, search/discovery, development, and project management, with robust security and sandboxing for edge devices.

**Key Objectives:**
- ✅ Desktop parity: 14 tools matching OpenClaw capabilities
- ✅ Edge-safe: Sandboxing for Pi/embedded devices
- ✅ Skill system: Follows EvoClaw's modular architecture
- ✅ High coverage: 85%+ test coverage
- ✅ Production ready: Security, error handling, logging

---

## 2. Architecture Overview

### 2.1 System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     EvoClaw Orchestrator (Go)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Skill Loader & Registry                  │  │
│  │  - Discovers ~/.evoclaw/skills/                      │  │
│  │  - Parses SKILL.md + agent.toml                      │  │
│  │  - Injects into agent context                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           desktop-tools Skill (NEW)                   │  │
│  │  - 14 tools: read, write, edit, glob, grep, ...     │  │
│  │  - Sandboxed execution via bubblewrap                │  │
│  │  - Permission-based security model                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│              MQTT Command Bus (Edge Agents)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Edge Agent (Rust) - Pi / Embedded              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │        Command Handler: exec, file_read, ...          │  │
│  │  - Receives tool invocation from orchestrator         │  │
│  │  - Validates constraints & permissions                │  │
│  │  - Executes in restricted environment                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Skill Structure

```
~/.evoclaw/skills/desktop-tools/
├── SKILL.md                    # Manifest with frontmatter
├── agent.toml                  # Tool definitions (14 tools)
├── bin/                        # Tool executables
│   ├── dt-read                 # Rust binary for file read
│   ├── dt-write                # Rust binary for file write
│   ├── dt-edit                 # Rust binary for string edit
│   ├── dt-glob                 # Rust binary for glob search
│   ├── dt-grep                 # Rust binary for content search
│   ├── dt-websearch            # Rust binary for web search
│   ├── dt-webfetch             # Rust binary for URL fetch
│   ├── dt-codesearch           # Rust binary for code search
│   ├── dt-bash                 # Rust binary for shell exec
│   ├── dt-question             # Rust binary for user input
│   ├── dt-todowrite            # Rust binary for task write
│   ├── dt-todoread             # Rust binary for task read
│   ├── dt-task                 # Rust binary for agent spawn
│   └── dt-skill                # Rust binary for skill load
├── src/                        # Rust source
│   ├── main.rs                 # CLI dispatcher
│   ├── tools/
│   │   ├── mod.rs
│   │   ├── file_ops.rs         # read, write, edit
│   │   ├── search.rs           # glob, grep
│   │   ├── web.rs              # websearch, webfetch, codesearch
│   │   ├── exec.rs             # bash (sandboxed)
│   │   ├── interaction.rs      # question
│   │   ├── project.rs          # todowrite, todoread
│   │   └── meta.rs             # task, skill
│   ├── sandbox.rs              # Sandboxing logic
│   ├── security.rs             # Permission checks
│   └── lib.rs
├── tests/                      # Integration tests (85%+ coverage)
│   ├── file_ops_test.rs
│   ├── search_test.rs
│   ├── web_test.rs
│   ├── exec_test.rs
│   ├── interaction_test.rs
│   ├── project_test.rs
│   └── meta_test.rs
├── sandbox/                    # Sandbox configs
│   ├── bubblewrap.json         # Linux (Pi, desktop)
│   └── sandbox-exec.json       # macOS (not for Pi)
├── Cargo.toml                  # Rust dependencies
├── Cargo.lock
└── README.md                   # User guide
```

---

## 3. Tool Specifications

### 3.1 File Operations

#### **read** - Read file contents
```toml
[tools.read]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-read"
description = "Read file contents with offset/limit support"
args = ["$path", "$offset", "$limit"]
timeout_secs = 10
```

**Security:**
- Validates path is within allowed workspace
- Blocks reading system files (/etc/passwd, /proc, etc.)
- Enforces max file size (50MB default)
- Supports offset/limit for large files

**Implementation:**
```rust
pub fn read_file(path: &Path, offset: usize, limit: usize) -> Result<String> {
    validate_path(path)?;
    let content = fs::read_to_string(path)?;
    let lines: Vec<&str> = content.lines().collect();
    let start = offset.min(lines.len());
    let end = (offset + limit).min(lines.len());
    Ok(lines[start..end].join("\n"))
}
```

#### **write** - Create/overwrite files
```toml
[tools.write]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-write"
description = "Write content to file (creates parent dirs)"
args = ["$path", "$content"]
timeout_secs = 10
```

**Security:**
- Validates path is within workspace
- Creates parent directories automatically
- Enforces max file size limits
- Blocks writing to system paths

#### **edit** - String replacements
```toml
[tools.edit]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-edit"
description = "Make exact string replacements in files"
args = ["$path", "$old_text", "$new_text"]
timeout_secs = 10
```

**Security:**
- Requires exact match (no regex to prevent injection)
- Atomic writes (temp file → rename)
- Validates old_text exists before editing
- Enforces file size limits

### 3.2 Search & Discovery

#### **glob** - Find files by patterns
```toml
[tools.glob]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-glob"
description = "Find files matching glob patterns"
args = ["$pattern", "$max_results"]
timeout_secs = 30
```

**Security:**
- Respects .gitignore by default
- Max results limit (1000 default)
- Timeout protection for large trees
- No access to hidden system dirs

**Implementation:**
```rust
pub fn glob_search(pattern: &str, max: usize) -> Result<Vec<PathBuf>> {
    let walker = WalkBuilder::new(".")
        .standard_filters(true)  // Respect .gitignore
        .hidden(false)
        .build();
    
    let glob = GlobBuilder::new(pattern).build()?;
    let mut results = Vec::new();
    
    for entry in walker {
        if results.len() >= max { break; }
        if let Ok(e) = entry {
            if glob.is_match(e.path()) {
                results.push(e.path().to_path_buf());
            }
        }
    }
    Ok(results)
}
```

#### **grep** - Search file contents
```toml
[tools.grep]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-grep"
description = "Search file contents with regex"
args = ["$pattern", "$path", "$max_results"]
timeout_secs = 30
```

**Security:**
- Regex complexity limits (max 1000 chars)
- Max results limit
- Timeout protection
- Respects .gitignore

#### **websearch** - Real-time web search
```toml
[tools.websearch]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-websearch"
description = "Search the web via Brave/SearXNG"
args = ["$query", "$max_results"]
env = ["SEARCH_API_KEY=${BRAVE_API_KEY}"]
timeout_secs = 15
```

**Security:**
- Rate limiting (10 req/min)
- API key from secure vault
- Sanitizes query input
- Timeout protection

#### **webfetch** - Fetch URLs
```toml
[tools.webfetch]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-webfetch"
description = "Fetch and extract readable content from URLs"
args = ["$url", "$max_chars"]
timeout_secs = 15
```

**Security:**
- URL allowlist (blocks internal IPs)
- Max content size (5MB)
- User-agent header
- Timeout protection

#### **codesearch** - Search programming docs
```toml
[tools.codesearch]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-codesearch"
description = "Search programming docs and APIs"
args = ["$query", "$language"]
env = ["CODESEARCH_API_KEY=${CODESEARCH_KEY}"]
timeout_secs = 15
```

**Security:**
- API key from vault
- Rate limiting
- Sanitized queries

### 3.3 Development

#### **bash** - Run shell commands
```toml
[tools.bash]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-bash"
description = "Execute shell commands in sandboxed environment"
args = ["$command", "$workdir"]
timeout_secs = 60
```

**Security (CRITICAL):**
- Sandboxed via bubblewrap (Linux) or sandbox-exec (macOS)
- No network access by default
- Read-only filesystem except workspace
- Timeout enforced
- Command blocklist (rm -rf /, dd, etc.)
- PTY support optional (with approval)

**Sandbox Configuration:**
```json
{
  "engine": "bubblewrap",
  "network": false,
  "readonly_paths": ["/usr", "/bin", "/lib", "/lib64"],
  "readwrite_paths": ["$WORKSPACE"],
  "blocked_paths": ["/proc", "/sys", "/dev"],
  "env_vars": ["PATH", "HOME", "USER"],
  "max_processes": 100,
  "max_memory_mb": 512
}
```

**Implementation:**
```rust
pub fn exec_sandboxed(cmd: &str, workdir: &Path) -> Result<ExecResult> {
    validate_command(cmd)?;  // Block dangerous commands
    
    let sandbox_cmd = if cfg!(target_os = "linux") {
        build_bubblewrap_cmd(cmd, workdir)?
    } else if cfg!(target_os = "macos") {
        build_sandbox_exec_cmd(cmd, workdir)?
    } else {
        return Err("Unsupported platform for sandboxing".into());
    };
    
    let output = Command::new(&sandbox_cmd[0])
        .args(&sandbox_cmd[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?
        .wait_with_output()?;
    
    Ok(ExecResult {
        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        exit_code: output.status.code().unwrap_or(-1),
    })
}
```

#### **question** - Ask for user input
```toml
[tools.question]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-question"
description = "Prompt user for input or choices"
args = ["$prompt", "$choices"]
timeout_secs = 300
```

**Security:**
- Timeout (default 5 min)
- Input sanitization
- Choice validation

### 3.4 Project Management

#### **todowrite** / **todoread** - Track tasks
```toml
[tools.todowrite]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-todowrite"
description = "Write task to todo list"
args = ["$task", "$priority"]
timeout_secs = 5

[tools.todoread]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-todoread"
description = "Read todo list with optional filters"
args = ["$status", "$priority"]
timeout_secs = 5
```

**Storage:** `~/.evoclaw/data/todos.json`
```json
{
  "tasks": [
    {
      "id": "uuid-v4",
      "task": "Implement read tool",
      "priority": "high",
      "status": "done",
      "created_at": 1676300000,
      "completed_at": 1676305000
    }
  ]
}
```

#### **task** - Launch specialized agents
```toml
[tools.task]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-task"
description = "Spawn a subagent for specific task"
args = ["$task_description", "$model"]
timeout_secs = 3600
```

**Integration:**
- Uses EvoClaw's agent spawning API
- Communicates via MQTT
- Task state stored in WAL

#### **skill** - Load specialized workflows
```toml
[tools.skill]
command = "~/.evoclaw/skills/desktop-tools/bin/dt-skill"
description = "Load and execute a skill workflow"
args = ["$skill_name", "$action"]
timeout_secs = 60
```

**Integration:**
- Queries skill registry
- Validates dependencies
- Executes skill tools

---

## 4. Security Model

### 4.1 Three-Layer Security

**Layer 1: Path Validation**
- All file paths validated against workspace root
- Canonical path resolution (prevents ../ traversal)
- Blocklist for system paths

**Layer 2: Sandboxing (Linux/Pi)**
- Bubblewrap for process isolation
- Namespace isolation (PID, mount, network, IPC)
- Capability dropping (CAP_SYS_ADMIN, etc.)
- Resource limits (CPU, memory, processes)

**Layer 3: Genome Constraints**
- Ed25519 signature verification
- Owner-signed constraint enforcement
- Per-agent permission model

### 4.2 Permission Matrix

| Tool        | Workspace | Network | Exec | User Input | Edge Safe |
|-------------|-----------|---------|------|------------|-----------|
| read        | ✓         | ✗       | ✗    | ✗          | ✓         |
| write       | ✓         | ✗       | ✗    | ✗          | ✓         |
| edit        | ✓         | ✗       | ✗    | ✗          | ✓         |
| glob        | ✓         | ✗       | ✗    | ✗          | ✓         |
| grep        | ✓         | ✗       | ✗    | ✗          | ✓         |
| websearch   | ✗         | ✓       | ✗    | ✗          | ✓         |
| webfetch    | ✗         | ✓       | ✗    | ✗          | ✓         |
| codesearch  | ✗         | ✓       | ✗    | ✗          | ✓         |
| bash        | ✓         | ✗*      | ✓    | ✗          | ✓**       |
| question    | ✗         | ✗       | ✗    | ✓          | ✓         |
| todowrite   | ✓         | ✗       | ✗    | ✗          | ✓         |
| todoread    | ✓         | ✗       | ✗    | ✗          | ✓         |
| task        | ✗         | ✓       | ✓    | ✗          | ✓         |
| skill       | ✓         | ✓       | ✓    | ✗          | ✓         |

\* Network can be enabled with explicit permission  
\*\* Sandboxed with strict resource limits on Pi

### 4.3 Edge Device Considerations

**Raspberry Pi 4/5:**
- Full bubblewrap support
- Resource limits: 512MB RAM, 50% CPU
- Timeout: 60s default, 300s max
- No PTY support (terminal emulation disabled)

**Raspberry Pi Zero:**
- Limited sandboxing (fallback to chroot)
- Stricter resource limits: 256MB RAM, 30% CPU
- Timeout: 30s default, 120s max
- Exec tool disabled by default

---

## 5. Implementation Plan

### Phase 1: Core Infrastructure (Days 1-2)
- [x] Architecture design
- [ ] Rust project scaffold
- [ ] Security primitives (sandbox.rs, security.rs)
- [ ] Path validation
- [ ] Test framework setup

### Phase 2: File Operations (Day 3)
- [ ] Implement read, write, edit
- [ ] Unit tests (85%+ coverage)
- [ ] Integration tests
- [ ] Path traversal security tests

### Phase 3: Search Tools (Day 4)
- [ ] Implement glob, grep
- [ ] Regex safety tests
- [ ] Performance benchmarks
- [ ] Integration tests

### Phase 4: Web Tools (Day 5)
- [ ] Implement websearch, webfetch, codesearch
- [ ] API client wrappers
- [ ] Rate limiting
- [ ] Mock tests + live tests

### Phase 5: Execution & Interaction (Day 6)
- [ ] Implement bash with sandboxing
- [ ] Bubblewrap integration (Linux)
- [ ] Sandbox-exec integration (macOS)
- [ ] Implement question tool
- [ ] Security tests (escape attempts)

### Phase 6: Project Management (Day 7)
- [ ] Implement todowrite, todoread
- [ ] JSON storage layer
- [ ] Implement task, skill tools
- [ ] Integration with orchestrator

### Phase 7: Integration & Testing (Days 8-9)
- [ ] Skill packaging (SKILL.md, agent.toml)
- [ ] End-to-end tests
- [ ] Edge device tests (Pi 4)
- [ ] Performance profiling
- [ ] Security audit

### Phase 8: Documentation (Day 10)
- [ ] Update SKILLS-SYSTEM.md
- [ ] Update README.md
- [ ] Tool usage examples
- [ ] Security best practices
- [ ] Edge deployment guide

---

## 6. Testing Strategy

### 6.1 Coverage Targets
- **Overall:** 85%+
- **Security-critical (sandbox.rs, security.rs):** 95%+
- **File operations:** 90%+
- **Web tools:** 80%+
- **Meta tools:** 75%+

### 6.2 Test Categories

**Unit Tests:**
```rust
#[test]
fn test_read_file_with_offset() {
    let temp = tempfile::NamedTempFile::new().unwrap();
    writeln!(temp, "line1\nline2\nline3").unwrap();
    let result = read_file(temp.path(), 1, 1).unwrap();
    assert_eq!(result, "line2");
}

#[test]
fn test_path_traversal_blocked() {
    let result = read_file(Path::new("../../etc/passwd"), 0, 100);
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("path traversal"));
}
```

**Integration Tests:**
```rust
#[test]
fn test_bash_sandboxed_no_network() {
    let result = exec_sandboxed("curl https://google.com", Path::new(".")).unwrap();
    assert_ne!(result.exit_code, 0);  // Should fail
}

#[test]
fn test_bash_sandboxed_workspace_access() {
    let result = exec_sandboxed("echo test > test.txt", Path::new(".")).unwrap();
    assert_eq!(result.exit_code, 0);
    assert!(Path::new("test.txt").exists());
}
```

**Security Tests:**
```rust
#[test]
fn test_command_injection_blocked() {
    let result = exec_sandboxed("echo hello; rm -rf /", Path::new("."));
    assert!(result.is_err());
}

#[test]
fn test_resource_limits_enforced() {
    // Attempt to allocate 2GB RAM
    let result = exec_sandboxed("python -c 'x = [0] * 10**9'", Path::new(".")).unwrap();
    assert_ne!(result.exit_code, 0);  // Should be killed
}
```

---

## 7. Deliverables Checklist

### 7.1 Code
- [ ] `~/.evoclaw/skills/desktop-tools/` skill directory
- [ ] 14 tool binaries in `bin/`
- [ ] Rust source in `src/`
- [ ] Tests in `tests/` (85%+ coverage)
- [ ] `Cargo.toml` with dependencies
- [ ] Sandbox configs in `sandbox/`

### 7.2 Configuration
- [ ] `SKILL.md` with frontmatter metadata
- [ ] `agent.toml` with 14 tool definitions
- [ ] Environment variable mappings
- [ ] Permission requirements

### 7.3 Documentation
- [ ] `README.md` - User guide and examples
- [ ] Updated `docs/SKILLS-SYSTEM.md`
- [ ] Updated main `README.md`
- [ ] Security best practices doc
- [ ] Edge deployment guide

### 7.4 Tests
- [ ] Unit tests for all tools
- [ ] Integration tests for workflows
- [ ] Security tests for sandbox escapes
- [ ] Edge device tests (Pi 4)
- [ ] Performance benchmarks
- [ ] Coverage report (85%+)

### 7.5 CI/CD
- [ ] GitHub Actions workflow
- [ ] Cross-compilation for arm64 (Pi)
- [ ] Test automation
- [ ] Coverage reporting
- [ ] Release artifacts

---

## 8. Dependencies

### 8.1 Rust Crates
```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
anyhow = "1"
thiserror = "1"
tracing = "0.1"
tracing-subscriber = "0.3"
clap = { version = "4", features = ["derive"] }
walkdir = "2"
ignore = "0.4"  # For .gitignore support
regex = "1"
glob = "0.3"
reqwest = { version = "0.11", features = ["json"] }
scraper = "0.17"  # For webfetch HTML parsing
uuid = { version = "1", features = ["v4"] }
chrono = "0.4"

[dev-dependencies]
tempfile = "3"
mockito = "1"  # For HTTP mocking
criterion = "0.5"  # For benchmarks
```

### 8.2 System Dependencies
- **Linux (Pi):** `bubblewrap` (installable via apt)
- **macOS:** `sandbox-exec` (built-in)
- **Build tools:** `cargo`, `rustc` 1.70+

---

## 9. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sandbox escape | High | Multi-layer validation, security tests, capability dropping |
| Resource exhaustion on Pi | Medium | Strict timeouts, memory limits, process limits |
| Path traversal attacks | High | Canonical path resolution, blocklists, tests |
| Command injection | High | Command parsing, blocklists, sandboxing |
| API rate limits | Low | Rate limiting, caching, fallback providers |
| Test coverage gaps | Medium | Automated coverage checks in CI, 85% gate |

---

## 10. Success Metrics

- ✅ All 14 tools implemented and tested
- ✅ 85%+ test coverage achieved
- ✅ Passes security audit (no sandbox escapes)
- ✅ Runs on Pi 4 without issues
- ✅ Integration tests pass on x86 and arm64
- ✅ Documentation complete and reviewed
- ✅ Skill loads correctly in EvoClaw orchestrator

---

## 11. Future Enhancements

**Phase 2 (Post-Launch):**
- Docker container sandboxing (alternative to bubblewrap)
- Remote execution on distributed edge nodes
- Tool usage analytics and optimization
- AI-powered code search (beyond basic codesearch)
- Interactive debugging support
- Distributed task queue for multi-agent workflows

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-12  
**Author:** Alex Chen (EvoClaw Subagent)  
**Review Status:** Ready for Implementation
