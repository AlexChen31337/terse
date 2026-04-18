#!/bin/bash
# Batch create LSP skills from Anthropic's official plugins

SKILL_CREATOR="/home/bowen/.local/share/fnm/node-versions/v22.22.0/installation/lib/node_modules/openclaw/skills/skill-creator/scripts/init_skill.py"
SKILLS_DIR="/home/bowen/clawd/skills"

# rust-analyzer-lsp
python3 "$SKILL_CREATOR" rust-analyzer-lsp --path "$SKILLS_DIR" --resources scripts

# clangd-lsp
python3 "$SKILL_CREATOR" clangd-lsp --path "$SKILLS_DIR" --resources scripts

echo "✅ All LSP skill directories created!"
