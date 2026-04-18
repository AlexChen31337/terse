name: simmer-pipeline
# Simmer Prediction Markets — full trading pipeline with approval gate.
# brief → score → [APPROVE] → execute
#
# Usage:
#   { "action": "run", "pipeline": "/home/bowen/clawd/skills/simmer/workflows/simmer-pipeline.lobster" }
#   { "action": "run", "pipeline": "...", "argsJson": "{\"since\": \"8h\", \"top\": \"3\", \"dry_run\": \"true\"}" }
#
# Args:
#   since      - briefing lookback window (default: 4h)
#   top        - max picks to show/execute (default: 5)
#   sim_amount - $SIM per trade (default: 100)
#   dry_run    - "true" to preview without executing (default: false)

args:
  since:
    default: "4h"
  top:
    default: "5"
  sim_amount:
    default: "100"
  dry_run:
    default: "false"

steps:
  - id: brief
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/simmer/scripts/brief.py
      --since {{ args.since }}
      --limit 50

  - id: score
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/simmer/scripts/score.py
      --top {{ args.top }}
      --sim-amount {{ args.sim_amount }}
    stdin: $brief.stdout

  - id: review
    approval: required
    command: >
      echo "Simmer pipeline ready. Review picks above — approve to execute, reject to cancel."
    stdin: $score.stdout

  - id: execute
    command: >
      cd /home/bowen/clawd &&
      uv run python skills/simmer/scripts/execute.py
      {{ "--dry-run" if args.dry_run == "true" else "" }}
      --top {{ args.top }}
    stdin: $score.stdout
    condition: $review.approved
