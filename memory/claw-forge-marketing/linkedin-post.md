# LinkedIn Post — claw-forge SWE-bench Verified

---

**64% on SWE-bench Verified. Here's what that means.**

claw-forge — an agentic coding framework I've been building — just scored 64% on SWE-bench Verified, resolving 32 out of 50 real GitHub issues autonomously.

SWE-bench Verified is a human-validated benchmark of 500 real software engineering tasks: actual GitHub issues from production open-source Python repos, graded against the original test suite. No partial credit. Either your patch passes CI or it doesn't.

The breakdown: astropy at 59% (13/22), django at 68% (19/28). Django is the one I'm most proud of — it's a mature, complex codebase where subtle semantic errors fail hard.

**The cost angle is what I keep coming back to:** this run cost $52.53 for 50 instances — roughly $1.05 per resolved issue. We used a Sonnet-class model, not a frontier flagship. The state-of-the-art results you see on leaderboards often use the most expensive models available. claw-forge's 64% comes from the scaffolding: parallel workers, structured task delegation, test-driven iteration, and an agent loop that doesn't quit until the patch is green.

The benchmark score is a number. The real proof is production. But $1.05/instance for autonomous software engineering at this resolution rate is a different class of economics.

Next step: full 500-instance run and a public leaderboard submission.

**Question for the builders here:** what's your threshold for trusting an agent to touch production code unsupervised — is it a benchmark number, a cost model, or something else entirely?

---

*#SoftwareEngineering #AIAgents #BenchmarkResults #OpenSource #DeveloperTools*
