# atscale-pbi-transpile

DAX → MDX transpiler for Power BI Tabular Model files. Translates `.tmdl` / `.bim` model definitions into SML (Semantic Modeling Language) YAML, conforming to the [Open Semantic Interchange (OSI)](https://open-semantic-interchange.org) v1.0 schema.

**Status:** v0.0 — repo skeleton. See `docs/ONE_PAGER.md` for the strategic frame and `/Users/jsy/.claude/plans/ok-think-through-the-encapsulated-feather.md` for the full design plan.

## What it does

Build-time translation of Power BI Tabular Model artifacts into SML calc-member expressions that AtScale's MDX engine can evaluate at query time. This is **not** an extension of any query engine — it is a definition-layer transpiler that runs once per model.

## Quick architecture

```
.tmdl/.bim ──[Ingest]──▶ TomModel ──[Extract]──▶ DaxUnit[]
                                                    │
                          ┌──[Parse: ANTLR]─────────┘
                          ▼
                       DaxAst ──[Lower]──▶ SemanticIR ──[Emit MDX]──▶ MdxExpr
                                                │                       │
                                                └────[Assemble SML]─────┘
                                                          ▼
                                                       SmlModel (YAML)
```

Six stages. Each emits a typed `Diagnostics` channel. Untranslatable DAX produces a `Severity.Unsupported` diagnostic with a TODO marker in the SML output — **never** a silent mistranslation.

## Three governing principles

1. **Refuse, don't lie.** Untranslatable DAX emits a structured diagnostic, never a silent mistranslation. P0 invariant.
2. **Lossless re-emission.** Source spans, original DAX text, and comments survive into the SML output as provenance.
3. **Standards-anchored.** Output validates against OSI v1.0 schema. MDX fragments restricted to the documented "SML-MDX profile" subgrammar.

## Repo layout

See [the design plan](/Users/jsy/.claude/plans/ok-think-through-the-encapsulated-feather.md) for the full module layout.

## Coverage

[`src/atscale_pbi_transpile/coverage/dax_functions.yaml`](src/atscale_pbi_transpile/coverage/dax_functions.yaml) is the single source of truth for what DAX is supported. Every PR that adds or changes a lowering must update this file. The published coverage table at [`spec/coverage-table.md`](spec/coverage-table.md) regenerates from it at every release.

## Installation (will work once stages 1-3 land)

```bash
pip install atscale-pbi-transpile
atscale-pbi-transpile path/to/model.tmdl -o output.sml
```

## License

Apache 2.0. See [LICENSE](LICENSE).

## Status of each pipeline stage

| Stage | Status |
|---|---|
| 1. Ingest (TMDL + BIM) | Skeleton only |
| 2. Extract (TomModel → DaxUnit) | Not started |
| 3. Parse (DAX → AST via ANTLR) | Grammar placeholder; needs DaxStudio grammar fork |
| 4. Lower (AST → SemanticIR) | One example lowering (`calculate`) |
| 5. Emit MDX (SemanticIR → MdxExpr) | Skeleton |
| 6. Assemble SML | Skeleton; reuses `dbt-to-sml/dbt_to_sml.py` foundation |

## Where the IR lives

[`src/atscale_pbi_transpile/ir/types.py`](src/atscale_pbi_transpile/ir/types.py) is the load-bearing file. The `SemanticIR` types here are the swap-point that future-proofs the design: when OSI standardizes a calc-extension grammar, only stage 5 (MDX emitter) needs to change. Everything upstream stays.
