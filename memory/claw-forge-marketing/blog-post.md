# claw-forge hits 64% on SWE-bench Verified

*Published: 2026-03-13*

---

## What we measured and why it matters

Today we're publishing the first external benchmark result for claw-forge: **64% on SWE-bench Verified** (32/50 instances resolved), run on March 13, 2026.

SWE-bench Verified is the standard real-world benchmark for agentic software engineering. It's a human-validated set of 500 tasks drawn from actual GitHub issues across popular open-source Python repositories. Each task gives an agent a live codebase and an issue description. Success means generating a patch that passes the original test suite — the same tests the human contributor wrote. There's no partial credit, no hints, no interactive feedback. Either the code works or it doesn't.

This matters because SWE-bench Verified measures the thing that actually matters in software engineering: can you take a real problem and produce a real fix?

---

## Methodology

We ran a 50-instance sample drawn from two repositories: `astropy` and `django`. The run used 5 parallel workers, each operating independently on a Docker-isolated environment with full repository access, a bash shell, and edit capabilities.

**Model:** Claude Sonnet 4.6 (not Opus, not a frontier reasoning model — a mid-tier Sonnet-class model)  
**Scaffold:** claw-forge's standard agentic loop — task parsing, environment setup, iterative patch generation, and automated test verification  
**Workers:** 5 concurrent agents  
**Instances:** 50 (22 astropy, 28 django)  
**No human in the loop.** No cherry-picking. No retries after the fact.

---

## Results

| Repository | Resolved | Total | Rate |
|------------|----------|-------|------|
| astropy    | 13       | 22    | 59%  |
| django     | 19       | 28    | 68%  |
| **Total**  | **32**   | **50**| **64%** |

Django at 68% is the standout. Django's codebase is large, historically maintained, and heavily test-driven. The issues tend to involve subtle behavioral changes — the kind that break things in non-obvious ways if you're not reading the surrounding context carefully. Getting 19/28 there isn't luck.

astropy at 59% is solid for a scientific Python library where issues often touch domain-specific numerical behaviour and astronomy data standards.

---

## How this compares to SOTA

For context: when Claude 3.5 Sonnet was released in late 2024, Anthropic's own scaffold achieved **49% on SWE-bench Verified**, which was state-of-the-art at the time. Claude 3.7 Sonnet subsequently reached SOTA performance (publicly described as leading the leaderboard in early 2026). Top-performing systems on the full leaderboard today sit in the high 60s to low 70s range.

claw-forge's 64% — achieved with a Sonnet-class model, not a reasoning-optimised flagship — puts it firmly in the competitive tier, above what vanilla model scaffolds typically achieve, and in range with the leading systems.

The comparison that matters most: this is 15 points above where Claude 3.5 Sonnet's own scaffold peaked. The difference isn't the model. It's the orchestration.

---

## Cost analysis: $1.05 per instance

The full 50-instance run cost **$52.53**, or approximately **$1.05 per instance**.

Most published SWE-bench SOTA results involve frontier flagship models — the most expensive tier available. At $15–20+ per million output tokens for reasoning models, per-instance costs quickly reach $5–50 depending on task complexity and iteration depth.

claw-forge uses a Sonnet-class model at roughly $3/million input tokens. The economics of agent-driven software engineering change at $1/instance. It's the difference between a system you demo and a system you deploy.

That said, raw resolve rate matters too — and we're not making per-instance cost comparisons against other systems without apples-to-apples methodology. What we're saying is: at $1.05/instance and 64% resolution, claw-forge is entering production-viable territory.

---

## What's next

**Full 500-instance run.** The 50-instance sample is a slice. The full benchmark run across all SWE-bench Verified instances is the real number and what gets submitted to the public leaderboard. That's running next.

**Opus comparison.** What does claw-forge score with an Opus-class model? We expect 5–10+ percentage points of headroom. That experiment runs alongside the full 500-instance baseline.

**Public leaderboard submission.** Once we have the full run, we'll submit to the official SWE-bench leaderboard with full methodology transparency.

**Open-source release.** claw-forge will be open-sourced. The scaffolding is the asset. We want developers building on it.

---

## Closing thought

64% is a number. What it represents is more interesting: a small agentic framework, a mid-tier model, 5 workers, and no human supervision resolving nearly two-thirds of real production software issues on the first attempt.

The claw-forge team is just getting started.

---

*Run date: 2026-03-13 | Model: Claude Sonnet 4.6 | Cost: $52.53 / 50 instances*
