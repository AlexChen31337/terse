---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'skill-manage')"
---


# Skill Manage — Agent Procedural Memory

## When to Use
- After completing a complex task (5+ tool calls) successfully — save the workflow as a reusable skill
- When the user corrects the agent's approach — update the relevant skill with the fix
- When the user explicitly asks to create, modify, or delete a skill
- When the agent discovers a non-trivial workflow worth remembering for future use

## Procedure — CREATE

1. **Assess** if the task is worth saving:
   - 5+ tool calls used
   - Errors were hit and resolved
   - User corrections were applied
   - User explicitly requested it
   - Non-obvious workflow that would be hard to reconstruct

2. **Extract** the workflow:
   - What was done, in what order
   - What failed and how it was fixed
   - Key decisions and why

3. **Generate** SKILL.md using the template at `templates/SKILL_TEMPLATE.md`:
   ```bash
   uv run python skills/skill-manage/scripts/skill_crud.py create \
     --name "my-new-skill" \
     --description "What this skill does"
   ```

4. **Edit** the generated SKILL.md to fill in:
   - When to Use (trigger conditions)
   - Procedure (numbered steps)
   - Pitfalls (failure modes encountered)
   - Verification (how to confirm it worked)

5. **Add** supporting files if needed:
   - `scripts/` — helper scripts
   - `references/` — documentation, patterns, data files
   - `templates/` — output templates

6. **Verify**: read back the skill, confirm it parses correctly:
   ```bash
   uv run python skills/skill-manage/scripts/skill_crud.py validate --name "my-new-skill"
   ```

## Procedure — UPDATE

1. Read existing SKILL.md
2. Identify what needs updating (new steps, corrected pitfalls, updated verification)
3. Edit the SKILL.md preserving existing structure
4. Bump version (patch for fixes, minor for new steps)
5. Verify: diff shows expected changes

## Procedure — DELETE (Archive)

1. Archive the skill (never hard delete):
   ```bash
   uv run python skills/skill-manage/scripts/skill_crud.py delete --name "old-skill"
   ```
2. Skill moves to `~/.openclaw/workspace/skills/.archive/old-skill/`
3. Verify: skill no longer appears in active skills list

## Procedure — LIST

```bash
uv run python skills/skill-manage/scripts/skill_crud.py list
```

Outputs a markdown table: name, description, version, has scripts, has references.

## Procedure — VALIDATE

```bash
uv run python skills/skill-manage/scripts/skill_crud.py validate --name "skill-name"
```

Checks: SKILL.md exists, frontmatter is valid, required sections present.

## Pitfalls
- Don't create skills for trivial one-off tasks (answering a question, simple file reads)
- Keep skill names kebab-case (lowercase, hyphens)
- Always include Verification steps — "I think it works" is not verification
- Skills should be self-contained — don't depend on ephemeral state

## Verification
- Created skill appears in `skill_crud.py list` output
- SKILL.md parses correctly via `skill_crud.py validate`
- Skill shows up in OpenClaw's skill index on next session
