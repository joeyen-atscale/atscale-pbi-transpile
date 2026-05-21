# DAX → MDX Transpiler — One-pager

## The problem

AtScale's MDX-only serving protocol blocks Power BI customers from migrating to AtScale-managed semantic layers without re-authoring every measure by hand. Power BI Tabular Model files (`.tmdl` / `.bim`) contain DAX expressions that AtScale cannot evaluate. Implementing a full DAX engine in AtScale's runtime is a significantly larger project than this transpiler. Implementing a build-time DAX → MDX transpiler is **a bounded engineering project that unlocks Power BI migration** and gives AtScale the standard-setter narrative. Sizing is engineering's call.

## The approach

A six-stage Python pipeline that reads `.tmdl` / `.bim`, parses DAX measure expressions through an ANTLR grammar, lowers them through a typed Semantic IR, and emits SML YAML with MDX calc-member fragments AtScale's existing engine can evaluate.

```
.tmdl/.bim → TomModel → DaxUnit[] → DaxAst → SemanticIR → MdxExpr + SmlModel (YAML)
```

The Semantic IR is the load-bearing decision. It's the swap-point that future-proofs the design: when OSI standardizes a calc-extension grammar, only the emitter (stage 5) needs to change.

## Three governing principles

1. **Refuse, don't lie.** Untranslatable DAX emits a structured diagnostic, never a silent mistranslation. Wrong numbers destroy trust in the toolchain.
2. **Lossless re-emission.** Source spans + original DAX text survive into the SML output as provenance. The translation is auditable.
3. **Standards-anchored.** Output validates against OSI v1.0 schema. MDX fragments stay within a documented "SML-MDX profile" subgrammar.

## Strategic frame: standards-setter, not feature catch-up

This project is the reference implementation of an OSI-aligned semantic-model translator. Distribution: open-source under Apache 2.0 in the OSI / SML toolchain. AtScale's IR proposal becomes part of OSI v0.2. AtScale benefits twice — customers get Power BI migration, AtScale gets the credibility OSI requires to win the long game vs platform-bundled semantic layers (Genie, Cortex Analyst, Unity Catalog Metric Views).

## Milestones (ordered by dependency; engineering sizes and sequences)

| # | Milestone | Demonstrates |
|---|---|---|
| M1 | Stages 1-3 (ingest + extract + parse) on real `.tmdl`. SemanticIR types defined. Coverage table published. | "We can read Power BI models." |
| M2 | Stages 4-6 for the top-50 DAX functions (~70% coverage). Golden dataset bootstrapped. OSI IR draft submitted. | "We can translate the common case end-to-end." |
| M3 | Time intelligence + iterators + calc columns. RLS basic patterns. Design Center integration. | "We can translate full Tabular models with the common long-tail." |
| M4 | Inactive relationships, perspectives, edge-case CALCULATE patterns. Public v1.0 release. OSI calc-IR RFC filed. | "Production ready; OSI calc-IR proposal in flight." |

## Scope (v1)

**In:** measures + calculated columns + calculated tables + RLS roles + perspectives + relationships (active + one inactive via `USERELATIONSHIP`).

**Out (deferred to v1.1):** arbitrary multi-inactive-relationship graphs; row-context functions that don't have MDX equivalents (`EARLIER`, `RANKX` over fact tables) — refused-by-design with documented workarounds.

## Coverage commitment

Published `coverage-table.md` generated from a YAML registry. Every DAX function has a status: `supported`, `partial`, `unsupported`, or `refused-by-design`. CI enforces — no test or corpus reference without a matching coverage entry. Customers and OSI reviewers can audit support without reading code.

## What we need to kick off

1. **A DRI / engineering team.** Python project; doesn't need to live inside the core engine team. New "platform & interop" group is a natural home.
2. **Tabular Editor / DAX Studio community contacts.** Cheap engagement if we know the maintainers.
3. **2-5 NDA customer `.tmdl` files** for the private test corpus. Dramatically de-risks the long-tail discovery.
4. **OSI committee status & rep.** Faster IR ratification if AtScale already has a seat.

## Risks

| Risk | Mitigation |
|---|---|
| ANTLR community DAX grammar drift (Microsoft adds functions quietly) | Regular upstream diff cadence + "unknown function" CI diagnostic |
| MDX engine accepts smaller subgrammar than assumed | `spec/sml-mdx-profile.md` is a written contract, CI round-trips against live engine |
| OSI calc-extension lands with different IR shape | IR is the swappable boundary; emitters are <2K LOC each |
| "Full Tabular surface" balloons in scope | Coverage table publishes what's in/out; under-promise in public |
| OSI velocity vs market velocity | AtScale ships reference implementation now; OSI ratifies at its own pace |

## TL;DR

- **What:** Open-source Python transpiler. `.tmdl/.bim` → SML YAML. Reference implementation of OSI calc-IR proposal.
- **Why:** Power BI migration use case + OSI standard-setter narrative.
- **Scope:** 4 ordered milestones to v1.0 (see below). Sizing and calendar are engineering's call.
- **Footprint:** Python-only; doesn't touch AtScale's core engine.
- **Asked of you:** Name a DRI, find 2-5 customer `.tmdl` files under NDA, confirm AtScale's OSI committee status.

## Pointer to the full plan

`/Users/jsy/.claude/plans/ok-think-through-the-encapsulated-feather.md` has the complete technical design — IR types, module layout, hard semantic problems, coverage tracking, test architecture, validation strategy.
