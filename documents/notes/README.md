# documents/notes/

Consolidated planning notes for the `atscale-pbi-transpile` project. These are **copies** captured for easy reference; the source-of-truth files live elsewhere.

| File here | Source of truth |
|---|---|
| `PLAN.md` | `/Users/jsy/.claude/plans/ok-think-through-the-encapsulated-feather.md` — the full technical design plan (engineering-RFC-style) |
| `ONE_PAGER.md` | `docs/ONE_PAGER.md` — leadership-conversation framing |
| `OSI_STATUS.md` | `docs/OSI_STATUS.md` — OSI committee engagement plan + research findings |
| `PRD.md` | `docs/PRD_DRAFT_for_confluence.md` — local backup of the published Confluence PRD |
| `OSI_RFC.md` | `spec/osi-rfc-calc-ir.md` — the OSI RFC draft (pre-submission to github.com/open-semantic-interchange/OSI) |

## When to use which

- **PLAN.md** — when you need the full design rationale, IR types, hard semantic problems, and risk register. Most detailed; ~13KB.
- **ONE_PAGER.md** — when pitching to a single decision-maker (engineering lead, OSI sponsor, exec) and you want the shortest credible artifact.
- **PRD.md** — when you need a product-management-shaped version with TL;DR, scope, asks, verification criteria. Confluence-rendered version at [PTC/4743069701](https://atscale.atlassian.net/wiki/spaces/PTC/pages/4743069701).
- **OSI_STATUS.md** — when discussing OSI engagement specifically: AtScale's membership status, the strategic window, the engagement playbook.
- **OSI_RFC.md** — when ready to file the proposal at OSI. Pre-submission. Confluence-rendered version at [PTC/4743593987](https://atscale.atlassian.net/wiki/spaces/PTC/pages/4743593987).

## Stale-copy risk

These are copies. If you edit `docs/ONE_PAGER.md`, the `ONE_PAGER.md` here does **not** auto-update. Treat the source-of-truth files (column 2 in the table above) as canonical; refresh the copies here when materially out of sync.

Refresh command:

```bash
cd /Users/jsy/projects/atscale-pbi-transpile
cp /Users/jsy/.claude/plans/ok-think-through-the-encapsulated-feather.md documents/notes/PLAN.md
cp docs/ONE_PAGER.md docs/OSI_STATUS.md documents/notes/
cp docs/PRD_DRAFT_for_confluence.md documents/notes/PRD.md
cp spec/osi-rfc-calc-ir.md documents/notes/OSI_RFC.md
```
