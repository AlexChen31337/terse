# EvoClaw Desktop Tools - Implementation Plan

**Sprint:** 10 days  
**Start:** 2026-02-12  
**Target:** Desktop parity with OpenClaw  

---

## Day-by-Day Breakdown

### Day 1-2: Foundation ✅ (Current)
- [x] Architecture design document
- [ ] Rust project scaffold
- [ ] Security module (sandbox.rs)
- [ ] Path validation module
- [ ] Test harness setup

**Deliverables:**
- Architecture doc (DONE)
- Implementation plan (DONE)
- `Cargo.toml` with dependencies
- `src/security.rs` with path validation
- `src/sandbox.rs` with bubblewrap integration

---

### Day 3: File Operations
**Tools:** read, write, edit

**Tasks:**
1. Implement `src/tools/file_ops.rs`
2. Add CLI commands for each tool
3. Write unit tests (90%+ coverage)
4. Security tests (path traversal, size limits)

**Test Cases:**
- Read with offset/limit
- Write with parent dir creation
- Edit with exact match
- Path traversal attempts (should fail)
- Size limit enforcement
- Permission errors

---

### Day 4: Search Tools
**Tools:** glob, grep

**Tasks:**
1. Implement `src/tools/search.rs`
2. Integrate `ignore` crate for .gitignore
3. Regex safety checks
4. Performance benchmarks

**Test Cases:**
- Glob with wildcards
- Glob with .gitignore
- Grep with simple regex
- Grep with complex regex
- Max results enforcement
- Timeout handling

---

### Day 5: Web Tools
**Tools:** websearch, webfetch, codesearch

**Tasks:**
1. Implement `src/tools/web.rs`
2. Brave Search API integration
3. URL fetch with HTML parsing
4. Rate limiting
5. Mock tests + optional live tests

**Test Cases:**
- Search with various queries
- Fetch with HTML extraction
- Rate limit enforcement
- URL validation (block internal IPs)
- Timeout handling
- API error handling

---

### Day 6: Execution & Interaction
**Tools:** bash, question

**Tasks:**
1. Implement `src/tools/exec.rs`
2. Bubblewrap sandbox integration
3. Command validation and blocklist
4. Implement `src/tools/interaction.rs`
5. Security tests (escape attempts)

**Test Cases:**
- Sandboxed command execution
- Network access blocking
- Resource limit enforcement
- Command injection prevention
- Question timeout
- Input sanitization

---

### Day 7: Project Management & Meta
**Tools:** todowrite, todoread, task, skill

**Tasks:**
1. Implement `src/tools/project.rs`
2. JSON storage for todos
3. Implement `src/tools/meta.rs`
4. Integration with orchestrator API

**Test Cases:**
- Todo CRUD operations
- Todo filtering
- Task spawning
- Skill loading

---

### Day 8: Integration
**Tasks:**
1. Create SKILL.md with frontmatter
2. Create agent.toml with all tools
3. Build binaries for all tools
4. End-to-end tests
5. EvoClaw orchestrator integration test

**Test Cases:**
- Skill loads correctly
- All tools callable via agent.toml
- Environment variable injection
- Error handling and logging

---

### Day 9: Edge Testing
**Tasks:**
1. Cross-compile for arm64
2. Test on Raspberry Pi 4
3. Resource limit validation
4. Performance profiling
5. Security audit

**Test Cases:**
- All tools work on Pi 4
- Resource limits enforced
- Timeout handling
- No sandbox escapes

---

### Day 10: Documentation
**Tasks:**
1. Complete README.md
2. Update docs/SKILLS-SYSTEM.md
3. Update main README.md
4. Security best practices guide
5. Edge deployment guide

**Sections:**
- Installation instructions
- Usage examples for each tool
- Security model explanation
- Troubleshooting guide
- Edge device setup

---

## Critical Path

```mermaid
graph LR
    A[Day 1-2: Foundation] --> B[Day 3: File Ops]
    B --> C[Day 4: Search]
    C --> D[Day 5: Web]
    D --> E[Day 6: Exec]
    E --> F[Day 7: Project]
    F --> G[Day 8: Integration]
    G --> H[Day 9: Edge Test]
    H --> I[Day 10: Docs]
```

---

## Current Progress

**Completed:**
- ✅ Architecture design (comprehensive)
- ✅ Implementation plan
- ✅ Understanding of EvoClaw architecture
- ✅ Security model design
- ✅ Tool specifications

**Next Steps:**
1. Create Rust project scaffold
2. Implement security.rs with path validation
3. Implement sandbox.rs with bubblewrap
4. Set up test framework

---

## Resource Requirements

**Development:**
- Rust 1.70+
- cargo, rustc
- bubblewrap (Linux)
- Pi 4 for testing (or QEMU)

**APIs:**
- Brave Search API key (for websearch)
- Optional: Code search API

**Time Allocation:**
- Coding: 60%
- Testing: 25%
- Documentation: 10%
- Integration: 5%

---

**Status:** Ready to implement  
**Next Action:** Create Rust project scaffold
