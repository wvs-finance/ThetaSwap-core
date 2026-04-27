# Un-Archive Rollback Map

**Date:** 2026-04-15
**Purpose:** If any of the five un-archived reviewer agents needs to be reverted (charter drift unfixable, breaking internal cross-references, etc.), this file records the original archived paths so the rename is mechanically reversible.

## Mapping

| Clean active path (after move) | Original archived path (before move) |
|---|---|
| `/home/jmsbpp/.claude/agents/brand-guardian.md` | `/home/jmsbpp/.claude/agents/_archived/design/design-brand-guardian.md` |
| `/home/jmsbpp/.claude/agents/executive-summary-generator.md` | `/home/jmsbpp/.claude/agents/_archived/support/support-executive-summary-generator.md` |
| `/home/jmsbpp/.claude/agents/content-creator.md` | `/home/jmsbpp/.claude/agents/_archived/marketing/marketing-content-creator.md` |
| `/home/jmsbpp/.claude/agents/proposal-strategist.md` | `/home/jmsbpp/.claude/agents/_archived/sales/sales-proposal-strategist.md` |
| `/home/jmsbpp/.claude/agents/cultural-intelligence-strategist.md` | `/home/jmsbpp/.claude/agents/_archived/specialized/specialized-cultural-intelligence-strategist.md` |

## File metadata (pre-move)

All five archived files were last modified on 2026-04-01 09:11. Sizes: brand-guardian 11641 bytes, content-creator 3129 bytes, proposal-strategist 14295 bytes, cultural-intelligence-strategist 6643 bytes, executive-summary-generator 8992 bytes.

## Post-move frontmatter changes

Each moved file had its `name:` frontmatter field updated from its prefixed original (e.g., `design-brand-guardian`) to its clean basename (e.g., `brand-guardian`). To revert, also revert the `name:` field.

## Rollback procedure

For a single file:
```
mv /home/jmsbpp/.claude/agents/<clean-name>.md /home/jmsbpp/.claude/agents/_archived/<category>/<prefixed-name>.md
```
Then revert the frontmatter `name:` field to the prefixed form.

For all five: reverse each row of the table.
