# DAX → MDX Transpiler — Technical Design Plan

## Context

**Why this exists.** AtScale's MDX-only serving protocol blocks a clean import path for Power BI Tabular Model files (`.tmdl`, `.bim`) whose measures, calc columns, and calc tables are written in DAX. Customers with existing Power BI investments cannot move to AtScale without re-authoring every measure by hand. Implementing a full DAX engine in AtScale's runtime is a multi-year effort. Implementing a build-time DAX → MDX transpiler that emits SML calc-member expressions is a bounded engineering project that unlocks Power BI migration today and aligns with AtScale's larger strategic play: **owning the open semantic-interchange (OSI) standard**.

**Strategic frame.** This is not just a feature — it is the reference implementation of an OSI-aligned semantic-model translator. Distribution model (decided): open-source under the OSI / SML toolchain (Apache 2.0). The transpiler's IR, DAX grammar fork, conformance suite, and SML emitter all become public artifacts. AtScale benefits twice: customers get Power BI migration, and AtScale gets the standard-setter credibility OSI requires.

**v1 scope (decided): full Tabular model surface** — measures + calculated columns + calculated tables + RLS roles + perspectives + relationships (including inactive / `USERELATIONSHIP`). Sequencing and effort sizing are engineering's call; the plan below describes milestones in dependency order, not time.

**Intended outcome.** A working `atscale_pbi_transpile` Python package (CLI + library) that can read a real-world `.tmdl` or `.bim` file, emit valid SML YAML conforming to the OSI v0.1.1 schema, with structured diagnostics for the unsupported long tail, and a published coverage table that customers and the community can audit.

---

## Architecture

### Six-stage pipeline

```
.tmdl/.bim ──[1. Ingest]──▶ TomModel ──[2. Extract]──▶ DaxUnit[]
                                                          │
                              ┌──[3. Parse]───────────────┘
                              ▼
                           DaxAst ──[4. Lower]──▶ SemanticIR ──[5. Emit]──▶ MdxExpr
                                                       │                       │
                                                       └────[6. Assemble]──────┘
                                                                 ▼
                                                              SmlModel (YAML)
```

| Stage | I/O contract | Module |
|---|---|---|
| 1. Ingest | bytes → `TomModel` (typed mirror of Microsoft's Tabular Object Model) | `transpiler/ingest/` |
| 2. Extract | `TomModel` → `DaxUnit[]` (one per measure / calc-column / calc-table / RLS expression) | `transpiler/extract/` |
| 3. Parse | `DaxUnit` → `DaxAst` (typed AST from ANTLR) | `transpiler/parser/` |
| 4. Lower | `DaxAst` → `SemanticIR` (context-aware, normalized, OSI-aligned) | `transpiler/lower/` |
| 5. Emit MDX | `SemanticIR` → `MdxExpr` (SML-MDX-profile string + bound refs) | `transpiler/emit/mdx/` |
| 6. Assemble SML | `MdxExpr` + structural model (dims, relationships, perspectives, RLS) → `SmlModel` YAML | `transpiler/emit/sml/` |

Each stage emits a `Diagnostics` channel. `Severity.Fatal` short-circuits. `Severity.Unsupported` accumulates — a partial model still emits with TODO stubs and a structured `_diagnostics.yaml` sidecar listing every refused construct with source line, function name, reason, and link to the coverage-table row.

### Three governing principles

1. **Refuse, don't lie.** Untranslatable DAX emits a typed diagnostic, never a silent mistranslation. This is a P0 invariant.
2. **Lossless re-emission.** `SemanticIR` carries source span + original DAX text + comments. SML output carries provenance comments referencing the original measure name and source position.
3. **Standards-anchored.** Output validates against the OSI v0.1.1 JSON Schema. MDX fragments are restricted to a documented sub-grammar ("SML-MDX profile") that AtScale's MDX engine contractually accepts.

### The load-bearing decision: `SemanticIR`

The IR is the **swap point** that future-proofs the design. Today the emitter targets MDX. When OSI standardizes a calc-extension grammar, stage 5 swaps to emit the new grammar without touching stages 1-4. The IR is also the open OSI artifact — published in the OSI spec as the canonical interchange representation.

Three node families:

- **Scalar nodes** — `Literal`, `MeasureRef`, `ColumnRef`, `Arithmetic`, `If`, `Coalesce`, `Cast`.
- **Set nodes** — `MemberSet(dim, predicate)`, `AllMembers(dim)`, `TopN(n, set, orderBy)`, `Filter(set, predicate)`, `RowSet(table, predicate)` (the unsupported escape hatch — emits refuse).
- **Context nodes** — `WithContext(modifications, body)` where `ContextModification ∈ {Override, Remove, UseRelationship, TimeShift}`.

Every node carries `EvaluationContext { filter_ctx, row_ctx, current_member_bindings }`. This makes "DAX filter context vs MDX current-member context" a first-class IR concept rather than implicit pattern matching — the structural lift from `dialect-translator/dialect_translator.py` lines 97-113 ("DAX's filter context propagation is unique") from prose into types.

---

## Module layout

```
atscale-pbi-transpile/
├── src/atscale_pbi_transpile/
│   ├── ingest/             # TMDL parser (hand-written, indentation-scoped) + BIM JSON loader
│   ├── extract/            # TomModel → DaxUnit[]
│   ├── parser/
│   │   └── grammar/Dax.g4  # Forked from community ANTLR grammar; we own versioning
│   ├── lower/              # DaxAst → SemanticIR (one Lowering subclass per DAX function family)
│   ├── ir/                 # SemanticIR types + EvaluationContext + Diagnostics
│   ├── emit/
│   │   ├── mdx/            # SemanticIR → MdxExpr (SML-MDX profile)
│   │   └── sml/            # MdxExpr + structural model → SML YAML (extends dbt-to-sml serializer)
│   ├── coverage/
│   │   └── dax_functions.yaml  # Function-by-function support registry; CI enforces
│   └── cli.py              # `atscale-pbi-transpile model.tmdl -o model.sml`
├── tests/
│   ├── golden/<feature>/<id>.{dax,mdx,sml,diag}.txt   # Four-file tuples; syrupy snapshots
│   └── corpus/             # Anonymized real-world .tmdl files (AdventureWorks, Contoso, NDA customer set in private repo)
└── spec/
    ├── sml-mdx-profile.md  # The MDX sub-grammar AtScale's engine guarantees to accept
    ├── osi-ir-spec.md      # SemanticIR definition (published as OSI artifact)
    └── coverage-table.md   # Generated from coverage/dax_functions.yaml; published per release
```

### Reuse map

| Existing file | Role in new repo | Action |
|---|---|---|
| `/Users/jsy/projects/product/dialect-translator/dax_mdx_translator.py` | Pattern lookup tables for `lower/` Lowering subclasses | Promote each entry to a `Lowering` subclass with its golden-test ID |
| `/Users/jsy/projects/product/dialect-translator/dialect_translator.py` | Same — additional patterns + the filter-context-propagation note | Same — promote to typed lowerings |
| `/Users/jsy/projects/product/dbt-to-sml/dbt_to_sml.py` | YAML emission foundation for `emit/sml/` | Extract into `emit/sml/serializer.py`; replace hand-rolled `yaml_dump` with `ruamel.yaml` (round-trip safe, comment-preserving). The `[Measures].[X]` reference convention and dataset/metric split carry over. |
| `/Users/jsy/projects/product/ontology/osi-bfo.ttl` | Validation pass after stage 6 | Run SHACL/OWL validation post-emit; emit fails if structural typing wrong. Add `osi:DaxDialect` + calc-member class to the ontology (currently noted as Future Work). |
| `time-intelligence-patterns` skill (`PTC/4736319542`) | Reference spec for time-intel dispatch table | Translate the skill's heuristics into the time-intel dispatch table in `lower/time_intelligence.py`. |

---

## Technology choices

| Decision | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Matches all existing prior art (`dialect-translator/`, `dbt-to-sml/`, OSI tooling); ANTLR has first-class Python runtime; perf is not the bottleneck for build-time work. |
| DAX parser | ANTLR4 + forked community grammar (DaxStudio-derived) | Hand-written recursive descent for ~250 DAX functions = 6-9 person-months + perpetual maintenance. Tree-sitter lacks a mature DAX grammar and has weaker batch error-recovery than ANTLR. |
| TMDL ingest | Hand-written line-oriented parser (TMDL is indentation-scoped, small grammar) | ANTLR overkill for a small format; BIM is JSON via stdlib. |
| YAML | `ruamel.yaml` | Round-trip safe, preserves comments. Replaces `dbt-to-sml`'s prototype hand-rolled emitter. |
| Snapshot tests | `pytest` + `syrupy` | Standard. Four-file golden tuples per case. |
| Validation | OSI JSON Schema (pydantic) + SHACL via `pyshacl` against `osi-bfo.ttl` | Two independent validators; structural + semantic. Runs post-emit, pre-write. |

---

## Hard semantic problems

The five problem clusters that determine ship/no-ship:

**(a) `CALCULATE(expr, filter)` → MDX.** Lower to `WithContext(modifications=[Override(...)], body=lower(expr))`. Stage 5 chooses: pure dimension overrides → tuple `([Measures].[X], [Dim].[Member])`; composite or `Remove(ALL)` → `WITH MEMBER [Measures].[__calc_N] AS ... ` with synthesized name. Anchors: `dialect-translator/dax_mdx_translator.py` rows 13-16 and 55-58.

**(b) Row vs filter context.** Iterators (`SUMX`, `AVERAGEX`, `FILTER`) introduce row context. Decision rule: if the iterated table is a dimension hierarchy → lower to MDX `Aggregate(set, expr)` / `Generate(set, expr)`. If it's a fact table or arbitrary `FILTER(...)` predicate over rows → **refuse**. The principle: MDX evaluates over a cube space; if the DAX construct needs a row scan that can't be re-expressed as a set comprehension over a dimension, it's unfaithful.

**(c) `USERELATIONSHIP` and inactive relationships.** SML supports multiple relationships via `role_play_name`. v1 supports the common pattern (one active relationship + one inactive used in `USERELATIONSHIP`). Arbitrary multi-inactive graphs deferred to v1.1 with a tracked diagnostic.

**(d) Time intelligence.** Closed dispatch table for ~25 time functions (`SAMEPERIODLASTYEAR`, `TOTALYTD`, `DATEADD`, `PARALLELPERIOD`, `DATESBETWEEN`, `DATESYTD`, etc.). Each entry: DAX signature → IR `TimeShift(scope, n, period)` → MDX emission (`PrevMember`, `Lag(n)`, `YTD()`, `ParallelPeriod(...)`). Hard prerequisite: a date dimension must be present with a known time-hierarchy structure. Absent → refuse with a structured diagnostic telling the user to mark the date table.

**(e) Calculated columns + RLS.** Calc columns introduce row context that binds to a single column. Lower to SML `column_calc` (per OSI grammar) and emit as a column-level MDX expression — restricted to scalar arithmetic, `RELATED`, `IF`, `SWITCH`. RLS DAX expressions become SML `security_rule` predicates; coverage is bounded to the common patterns (`USERNAME()`, `LOOKUPVALUE`, dimension-attribute comparisons). RLS edge cases (filter functions in security predicates) refuse to v1.1.

---

## Coverage tracking

`src/atscale_pbi_transpile/coverage/dax_functions.yaml` — single registry, the source of truth.

```yaml
- function: CALCULATE
  status: supported    # supported | partial | unsupported | refused-by-design
  arity: 2+            # 2 args + N modifier args
  lowering: lower/calculate.py:CalculateLowering
  golden_tests: [g_calc_001, g_calc_002, ..., g_calc_017]
  partial_reasons: []  # populated when status == partial

- function: SUMX
  status: partial
  lowering: lower/iterators.py:SumxLowering
  golden_tests: [g_sumx_001, g_sumx_002]
  partial_reasons:
    - "Only supported when first arg is VALUES(Dim[Attr]) or a dimension table"
    - "Refused for fact-table iteration"

- function: RANKX
  status: refused-by-design
  reason: "Row-context ranking over arbitrary tables has no clean MDX analog"
  workaround: "Use AtScale-native calc member with MDX RANK() function manually"
```

CI fails if a DAX function appears in a test or corpus file but lacks a coverage-table entry. The published `spec/coverage-table.md` is generated from this YAML at every release — customers and OSI reviewers can audit support without reading code.

---

## Test architecture

**Golden dataset.** Four-file tuples at `tests/golden/<feature>/<id>.{dax,mdx,sml,diag}.txt`:
- `.dax` — input DAX expression
- `.mdx` — expected MDX fragment (the SML-MDX profile output)
- `.sml` — expected full SML YAML (includes structural context)
- `.diag` — expected diagnostics (empty for successful translations)

`syrupy` snapshot runner. Every PR must include a new golden tuple for any new lowering or coverage row.

**Real-world corpus.** Anonymized public Power BI samples (AdventureWorks, Contoso) in the public repo. NDA customer models in a private satellite repo, CI'd against the public transpiler via a separate workflow. Corpus failures are tolerated (long-tail signal) but golden failures block.

**SML-MDX-profile validation.** Stage 5 emits MDX; CI round-trips it through a live AtScale dev instance to confirm the engine accepts it. This catches the "we emit MDX the engine actually rejects" failure mode early.

---

## OSI alignment plan

The transpiler is a referenced implementation of the OSI standard, not a downstream consumer. Three contributions back to OSI:

1. **`SemanticIR` as the OSI calc-interchange IR.** Submit the IR (node families, evaluation-context model) as a proposed addition to OSI v0.2. AtScale ships the reference implementation while the spec ratifies.
2. **DAX dialect extension to OSI-BFO ontology.** The `ontology/osi-bfo.ttl` notes calc-member + DAX dialect as future work; this project ships them. PR back to the OSI ontology repo.
3. **Conformance suite.** The golden dataset becomes the OSI conformance test for any future DAX-importing semantic-layer tool. AtScale runs it; dbt SL, Cube, Coalesce, etc. can run it against their own translators if they build them.

This is the standard-setter narrative made concrete: AtScale doesn't just lobby for OSI extensions, it ships the artifacts.

---

## Milestones (ordered by dependency; sequencing and timing TBD by engineering)

| # | Milestone | Demonstrates |
|---|---|---|
| M1 | Stages 1-3 (ingest + extract + parse) on real `.tmdl`. SemanticIR types defined. Coverage table published with all DAX functions listed (most `unsupported` at this milestone). | "We can read Power BI models." |
| M2 | Stages 4-6 for the top-50 DAX functions (covers ~70% of common measures). Golden dataset bootstrapped. Public corpus runs. OSI IR draft submitted. | "We can translate the common case end-to-end." |
| M3 | Time intelligence + iterators + calc columns. RLS basic patterns. AtScale Design Center integration (CLI shell-out). | "We can translate full Tabular models with the common long-tail." |
| M4 | Inactive relationships, perspectives, edge-case CALCULATE patterns. Public v1.0 release with published coverage table. OSI calc-IR RFC filed. | "Production ready; OSI calc-IR proposal in flight." |

Dependencies: M2 requires M1's IR types stable; M3 requires M2's lowering framework; M4 is consolidation. The DRI sizes each milestone and proposes calendar.

---

## Verification (how we test end-to-end)

After implementation, validate by running:

1. **Unit tests.** `pytest tests/golden/` — all four-file tuples pass. ~500 golden tests at v1.0.
2. **Coverage table consistency.** `python -m atscale_pbi_transpile.coverage.check` — every DAX function referenced in tests has a coverage entry; every coverage entry has at least one golden test.
3. **Real-world corpus.** `python -m atscale_pbi_transpile.cli tests/corpus/AdventureWorks.tmdl -o /tmp/aw.sml` — exits 0, emits valid SML, diagnostics file lists known unsupported constructs and nothing else.
4. **OSI schema validation.** `python -m atscale_pbi_transpile.validate /tmp/aw.sml` — passes JSON Schema + SHACL/OWL ontology validation against `ontology/osi-bfo.ttl`.
5. **Live MDX engine round-trip.** CI workflow deploys `/tmp/aw.sml` to a dev AtScale instance via the model-deployment API, runs a representative MDX query for each translated measure, compares result to a known-good fixture computed against the original Power BI model.
6. **Coverage table publication.** `make docs/coverage-table.md` — regenerates from `dax_functions.yaml`; documentation site picks it up.

---

## Critical files to modify or reference

**New repo (to be created at `github.com/atscaleinc/atscale-pbi-transpile`):** see Module layout above.

**Files in this product repo to migrate / reuse:**
- `/Users/jsy/projects/product/dialect-translator/dax_mdx_translator.py` — promote pattern entries to `Lowering` subclasses
- `/Users/jsy/projects/product/dialect-translator/dialect_translator.py` — same
- `/Users/jsy/projects/product/dbt-to-sml/dbt_to_sml.py` — extract YAML emission as `emit/sml/serializer.py` foundation; replace `yaml_dump` with `ruamel.yaml`
- `/Users/jsy/projects/product/ontology/osi-bfo.ttl` — extend with `osi:DaxDialect` + calc-member classes; PR back to OSI ontology repo

**Confluence references for spec authoring:**
- Time intelligence reference: `PTC/4736319542` (time-intelligence-patterns skill)
- Existing DAX→SQL lowering tickets: ATSCALE-48688, ATSCALE-48654, ATSCALE-48561 (orthogonal but informative about DAX edge cases)

---

## Risks

1. **ANTLR community DAX grammar drift.** Microsoft adds DAX functions quietly; our fork lags. *Mitigation:* quarterly grammar diff vs upstream; "unknown function" diagnostic surfaces in CI before customers do.
2. **MDX engine accepts a smaller sub-grammar than assumed.** *Mitigation:* `spec/sml-mdx-profile.md` is written down and validated continuously by CI round-trip against a real AtScale instance.
3. **OSI calc-extension lands with a different IR shape than ours.** *Mitigation:* the IR is the swappable boundary; emitters are <2K LOC each. Pivot cost is bounded.
4. **"Full Tabular surface" balloons in scope.** *Mitigation:* coverage table publishes what's in and out; under-promising in public is the only honest move. Milestone scoping above is the budget; engineering proposes calendar against it.
5. **OSI committee velocity vs market velocity.** OSI ratification operates on committee timelines that the project does not control. *Mitigation:* AtScale ships the reference implementation independently of ratification status. The transpiler is useful from day 1 even without OSI ratification.

---

## What I'd want from the user before kickoff

1. **Engineering team / DRI.** Who owns this? It's a Python project; doesn't have to live inside AtScale's Java/Scala engine team. Could be a new "platform & interop" group.
2. **Tabular Editor / DAX Studio team contacts.** Open-source community engagement starts cheap if we know the maintainers.
3. **NDA-customer models for the private test corpus.** Two-to-five real-world `.tmdl` files would dramatically de-risk the long-tail discovery.
4. **OSI committee status.** Is AtScale already on the committee? Who's the rep? The IR proposal goes faster if AtScale already has a seat.
