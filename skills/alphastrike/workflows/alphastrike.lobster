# AlphaStrike v2 Trading Pipeline
# Technical analysis + Hyperliquid execution with approval gate

pipeline "alphastrike" {
  title = "AlphaStrike v2 - Technical Analysis Trading"
  description = "Generate signals using technical indicators, review, execute on Hyperliquid"

  # Step 1: Generate signals
  step "generate_signals" {
    title = "Generate Trading Signals"
    description = "Analyze BTC/ETH/SOL using RSI, MACD, EMA, BB, volume"
    executable = "python3"
    arguments = [
      "skills/alphastrike/scripts/signal.py",
      "--assets", "BTC", "ETH", "SOL",
      "--interval", "1h",
      "--min-confidence", "0.4",
      "--output", "json"
    ]
    output = "signals.json"
  }

  # Step 2: Review signals (APPROVAL GATE)
  step "review" {
    title = "Review Trading Signals"
    description = "Review generated signals before execution"
    type = "approval"

    approval_message = """
🤖 AlphaStrike v2 Trading Signals

${steps.generate_signals.output}

Execute these trades?
- Reply YES to execute
- Reply NO to cancel
- Modify trade size with: SIZE=50 (USDC)
"""
  }

  # Step 3: Execute trades
  step "execute" {
    title = "Execute Trades on Hyperliquid"
    description = "Place approved orders on Hyperliquid DEX"
    executable = "python3"
    arguments = [
      "skills/alphastrike/scripts/execute.py",
      "--max-trades", "3",
      "--position-size", "${env.POSITION_SIZE:-10}",
      "--dry-run=${env.DRY_RUN:-false}",
      "--log"
    ]
    input = "signals.json"
    output = "execution_result.json"

    depends_on = ["review"]
  }

  # Final output
  output {
    signals = "steps.generate_signals.output"
    execution = "steps.execute.output"
    timestamp = "${timestamp}"
  }
}
