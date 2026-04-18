name: rsi-cycle
# Recursive Self-Improvement cycle as a Lobster pipeline.
# Runs: shim scan → observe → analyze → propose → [APPROVE] → deploy
# Resumable: if session resets mid-run, resume token survives.
#
# Usage (via lobster tool):
#   { "action": "run", "pipeline": "/home/bowen/clawd/skills/rsi-loop/workflows/rsi-cycle.lobster" }
#   { "action": "run", "pipeline": "...", "argsJson": "{\"since\": \"8h\", \"auto_deploy\": \"false\"}" }

args:
  since:
    default: "4h"
  auto_deploy:
    default: "false"

steps:
  - id: shim_scan
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/rsi-loop/scripts/openclaw_shim.py scan --since {{ args.since }}

  - id: rsi_cycle
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/rsi-loop/scripts/rsi_cli.py cycle --auto

  - id: status
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/rsi-loop/scripts/rsi_cli.py status

  - id: proposals
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/rsi-loop/scripts/rsi_cli.py propose --json 2>/dev/null || echo "[]"

  - id: review
    approval: required
    command: >
      echo "RSI cycle complete. Review proposals above — approve to deploy safe ones, reject to skip."
    stdin: $proposals.stdout

  - id: deploy
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/rsi-loop/scripts/rsi_cli.py deploy --safe-only
    condition: $review.approved
