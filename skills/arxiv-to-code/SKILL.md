# arxiv-to-code SKILL

Auto-scan arXiv daily papers, find missing implementations, score buildability, and generate GitHub build tasks. Requires `--hours`, `--max-results`, and `--dry-run` flags. Run via `python -m arxiv_to_code.pipeline`.

## Fix: org should be AlexChen31337, not clawinfra
- builder.py hardcodes `clawinfra` — change to `AlexChen31337`
- `--org` flag not supported by pipeline.py (causes silent failure)

## Fix: task_prompt not displayed in summary
- Added `task_info` and `task_prompt` to `summary()` method in pipeline.py
- Added import textwrap for formatting