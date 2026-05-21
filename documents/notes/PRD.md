# PRD: DAX → MDX Transpiler

> Build-time translator: Power BI Tabular Model files (`.tmdl` / `.bim`) → SML YAML. Reference implementation of an OSI-aligned calc-IR proposal. Open-source Apache 2.0.

**Status:** Draft (2026-05-21). Ownership not yet assigned.

**Author:** Joe Yen. **Contributors expected:** TBD engineering DRI + David Mariani (OSI sponsor).

**Companion artifacts:**
- Repo skeleton: `/Users/jsy/projects/atscale-pbi-transpile/` (now standalone repo)
- One-pager: `atscale-pbi-transpile/docs/ONE_PAGER.md`
- Full design plan: `/Users/jsy/.claude/plans/ok-think-through-the-encapsulated-feather.md`
- OSI engagement plan: `atscale-pbi-transpile/docs/OSI_STATUS.md`

---

## TL;DR

- **What:** Open-source Python transpiler. `.tmdl` / `.bim` → SML YAML. Reference implementation of an OSI calc-IR proposal.
- **Why:** Power BI migration use case + OSI standard-setter narrative.
- **Scope:** 4 ordered milestones to v1.0 (see below). Sizing and sequencing are engineering's call.
- **Footprint:** Python-only; doesn't touch AtScale's core engine.
- **Ask:** Name a DRI, find 2-5 customer `.tmdl` files under NDA, confirm AtScale's OSI TSC representation.

---

## OSI engagement status (load-bearing context)

Research conducted 2026-05-21. Full detail in `atscale-pbi-transpile/docs/OSI_STATUS.md`.

- **AtScale joined OSI on 2026-01-27** — full member (third cohort), alongside Databricks, Qlik, JetBrains, Lightdash, Coalesce, and Credible.
- **OSI v1.0 was finalized January 2026.** v0.2 dev branch active.
- **No calc-member / formula-language working-group proposal currently exists** in the public OSI repo. The Advanced Metrics & Expression Language working group is live but underspecified. **This is the opening.**
- **Strategic window: open today.** The Advanced Metrics & Expression Language working group is live but underspecified; AtScale has the opportunity to anchor the calc-IR proposal before competitors (Databricks, Cube) propose their own. Calendar is engineering and AR's call.
- **Internal champion:** David Mariani (CTO). No specific TSC representative is publicly named — worth confirming.
- **Filing target:** `github.com/open-semantic-interchange/OSI`.

Strategic implication: **the transpiler is both a feature (Power BI migration) and a flag-planting standards play (OSI calc-IR reference implementation).** They reinforce each other.

---

## Problem

AtScale's MDX-only serving protocol blocks Power BI customers from migrating to AtScale. Power BI Tabular Model files contain DAX expressions; AtScale's engine evaluates MDX. Today, migration requires hand-rewriting every measure — a non-starter for any model larger than a few dozen measures.

A full DAX engine in AtScale's runtime is a significantly larger project than this transpiler. A build-time DAX → MDX transpiler is **a bounded engineering project that unlocks Power BI migration** and creates the artifact AtScale needs to anchor the OSI calc-IR standard. Sizing is engineering's call.

## Approach

Six-stage Python pipeline. Reads `.tmdl` / `.bim`, parses DAX through ANTLR4 (DaxStudio grammar fork), lowers through a typed Semantic IR, emits SML YAML with MDX calc-member fragments.

```
.tmdl/.bim → TomModel → DaxUnit[] → DaxAst → SemanticIR → MdxExpr + SmlModel (YAML)
```

The Semantic IR is the swap-point that future-proofs the design: when OSI standardizes a calc-extension grammar (which AtScale is proposing), only the emitter (stage 5) changes.

## Three governing principles

1. **Refuse, don't lie.** Untranslatable DAX → structured `Severity.Unsupported` diagnostic, never silent mistranslation. P0 invariant.
2. **Lossless re-emission.** Source spans + original DAX text survive into the SML output as provenance.
3. **Standards-anchored.** Output validates against OSI v1.0 schema. MDX fragments stay within the documented "SML-MDX profile" subgrammar.

## Pipeline architecture

| Stage | I/O contract | Module |
|---|---|---|
| 1. Ingest | bytes → `TomModel` | `transpiler/ingest/` |
| 2. Extract | `TomModel` → `DaxUnit[]` | `transpiler/extract/` |
| 3. Parse | `DaxUnit` → `DaxAst` | `transpiler/parser/` |
| 4. Lower | `DaxAst` → `SemanticIR` | `transpiler/lower/` |
| 5. Emit MDX | `SemanticIR` → `MdxExpr` | `transpiler/emit/mdx/` |
| 6. Assemble SML | `MdxExpr` + structural model → `SmlModel` YAML | `transpiler/emit/sml/` |

Each stage emits `Diagnostics`. `Severity.Fatal` short-circuits. `Severity.Unsupported` accumulates — partial model still emits with TODO stubs.

## The Semantic IR

Three node families: scalar (Literal, MeasureRef, ColumnRef, Arithmetic, If, Coalesce, Cast); set (MemberSet, AllMembers, TopN, FilterSet, RowSet); context (`WithContext(modifications, body)` with Override / Remove / UseRelationship / TimeShift modifications).

Every node carries `EvaluationContext { filter_ctx, row_ctx, current_member_bindings }` so "DAX filter context vs MDX current-member context" is a typed concept.

Reference implementation: `atscale-pbi-transpile/src/atscale_pbi_transpile/ir/types.py`. Proposed for OSI v0.2 inclusion.

## Hard semantic problems

1. **`CALCULATE(expr, filter)` → MDX.** Pure overrides → tuple; composite or `Remove(ALL)` → synthesized `WITH MEMBER`.
2. **Row vs filter context.** Iterators (`SUMX`, `AVERAGEX`, `FILTER`) over dim tables → MDX `Aggregate`/`Generate`. Over fact tables → refuse.
3. **`USERELATIONSHIP`.** v1 supports one inactive relationship per measure; multi-inactive deferred to v1.1.
4. **Time intelligence.** ~25 functions, closed dispatch table. Requires marked Date table; refuse otherwise.
5. **Calc columns + RLS.** Restricted to scalar arithmetic, `RELATED`, `IF`, `SWITCH`; RLS bounded to `USERNAME()`, `LOOKUPVALUE`, dimension-attribute comparisons.

## Coverage tracking

`src/atscale_pbi_transpile/coverage/dax_functions.yaml` — single source of truth. Statuses: `supported` / `partial` / `unsupported` / `refused-by-design`. CI enforces. Published `coverage-table.md` regenerates from the YAML each release.

## Test architecture

- **Golden dataset.** Four-file tuples (`.dax` / `.mdx` / `.sml` / `.diag`). `pytest` + `syrupy`.
- **Real-world corpus.** Public Power BI samples (AdventureWorks, Contoso) in open repo; 2-5 NDA customer models in private satellite repo.
- **SML-MDX-profile validation.** CI round-trips emitted MDX through a live AtScale dev instance.

## OSI alignment plan

1. **`SemanticIR` as OSI v0.2 calc-interchange IR.** Submit as working-group proposal once M1 ships (reference implementation makes the proposal credible).
2. **DAX dialect extension to OSI-BFO ontology.** PR back to OSI ontology repo.
3. **Conformance suite.** Golden dataset becomes the OSI conformance test for any future DAX importer.

## Milestones (ordered by dependency; engineering sizes and sequences)

| # | Milestone |
|---|---|
| M1 | Stages 1-3 working on real `.tmdl`. IR types defined. Coverage table published. |
| M2 | Stages 4-6 for top-50 DAX functions (~70% coverage). Golden dataset. OSI IR draft submitted. |
| M3 | Time intelligence + iterators + calc columns + RLS basics. Design Center integration. |
| M4 | Full v1.0 release. OSI calc-IR RFC filed. |

## v1 scope

**In:** measures + calc columns + calc tables + RLS roles + perspectives + relationships (active + one inactive).

**Out (v1.1):** multi-inactive-relationship graphs; `EARLIER`, `RANKX` over fact tables (refused-by-design with workarounds).

## Technology choices

| Decision | Choice |
|---|---|
| Language | Python 3.11+ |
| DAX parser | ANTLR4 + DaxStudio grammar fork |
| TMDL ingest | Hand-written; BIM is JSON via stdlib |
| YAML | `ruamel.yaml` |
| Tests | `pytest` + `syrupy` |
| Validation | OSI JSON Schema (pydantic) + SHACL via `pyshacl` |

## Reuse from existing AtScale work

| Existing file | Role |
|---|---|
| `dialect-translator/dax_mdx_translator.py` | Pattern lookup → promote to `Lowering` subclasses |
| `dialect-translator/dialect_translator.py` | Same |
| `dbt-to-sml/dbt_to_sml.py` | YAML emission foundation; replace hand-rolled `yaml_dump` with `ruamel.yaml` |
| `ontology/osi-bfo.ttl` | Validation pass; extend with `osi:DaxDialect` + calc-member classes |
| `time-intelligence-patterns` skill (PTC/4736319542) | Reference for time-intel dispatch table |

## Risks

| Risk | Mitigation |
|---|---|
| ANTLR community DAX grammar drift | Regular upstream diff cadence + "unknown function" CI diagnostic |
| MDX engine accepts smaller subgrammar than assumed | `spec/sml-mdx-profile.md` written contract; CI round-trips against live engine |
| OSI calc-IR lands with different shape | IR is the swappable boundary; emitters <2K LOC each |
| Full Tabular surface balloons in scope | Coverage table publishes what's in/out |
| OSI velocity vs market velocity | Ship reference implementation now; OSI ratifies at its own pace |
| Microsoft never adopts OSI calc-IR | Most likely outcome. Transpiler still solves Power BI migration regardless |

## Ask

1. **Engineering DRI** named to start M1.
2. **Tabular Editor / DAX Studio community contacts.**
3. **2-5 NDA customer `.tmdl` files** for the private test corpus.
4. **OSI TSC representation confirmation** internally.

## Verification (acceptance criteria for v1.0)

1. `pytest tests/golden/` — ~500 golden tuples pass.
2. `python -m atscale_pbi_transpile.coverage.check` — YAML consistent with tests.
3. `atscale-pbi-transpile tests/corpus/AdventureWorks.tmdl -o /tmp/aw.sml` — exits 0; diagnostics list only known unsupported constructs.
4. `python -m atscale_pbi_transpile.validate /tmp/aw.sml` — passes JSON Schema + SHACL/OWL.
5. Live MDX engine round-trip — emitted SML deploys + queries match Power BI fixtures.
6. `make docs/coverage-table.md` — regenerates.

---

## Companion documents

- Full technical plan: `/Users/jsy/.claude/plans/ok-think-through-the-encapsulated-feather.md`
- One-pager for leadership conversation: `atscale-pbi-transpile/docs/ONE_PAGER.md`
- OSI engagement plan: `atscale-pbi-transpile/docs/OSI_STATUS.md`
- Reference implementation skeleton: `atscale-pbi-transpile/`
