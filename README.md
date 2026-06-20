# atscale-pbi-transpile

A build-time transpiler that turns the DAX measures in a Power BI Tabular Model into SML calc members that an MDX engine can evaluate — so a model migrates without re-authoring every measure by hand.

## Why it exists

Moving a Power BI model onto an MDX-serving semantic layer normally means rewriting its DAX measures one at a time. That is slow, and worse, it is silent: a measure rewritten slightly wrong still runs and still returns a number — the wrong number. The expensive failure isn't the measure that won't translate; it's the one that translates incorrectly and no one notices until a dashboard has been trusted for a quarter.

This project takes the other path. It reads `.tmdl` / `.bim`, parses each DAX measure, lowers it through a typed intermediate representation, and emits SML YAML with MDX calc-member fragments — once, at build time, not as a runtime DAX engine. Its first principle is the one that makes the output trustworthy: **a measure it cannot translate faithfully is refused with a structured diagnostic, never guessed at.** A refusal you can see beats a wrong answer you can't.

## Status

**v0.0 — a design skeleton, not a working transpiler.** What exists today:

- A complete, typed Semantic IR (`src/atscale_pbi_transpile/ir/types.py`) — scalar, set, and context-modification nodes, each carrying its source span and evaluation context. This is the worked-out part.
- A CLI entry point (`atscale-pbi-transpile`) that parses its arguments and prints what it *would* do. It does not yet translate anything.
- One example lowering (`lower/calculate.py`) that demonstrates the refusal contract: it returns no IR plus an `UNSUPPORTED` diagnostic rather than a half-correct translation.
- One end-to-end golden tuple (`tests/golden/calculate/g_calc_001.*`) showing the intended DAX → MDX → SML shape.
- A coverage registry (`coverage/dax_functions.yaml`) and spec documents that describe the **target** surface. The registry names lowering modules and golden tests that are not built yet — read it as the plan, not as implemented coverage.

The ingest, extract, parse, and emit stages are empty packages. If you are evaluating whether this does what you need today, the honest answer is: not yet. If you are evaluating the design, start with the IR.

## How it will work

Six stages, each emitting a typed diagnostics channel:

```
.tmdl/.bim ──[ingest]──▶ TomModel ──[extract]──▶ DaxUnit[]
                                                    │
                          ┌──[parse: ANTLR]─────────┘
                          ▼
                       DaxAst ──[lower]──▶ SemanticIR ──[emit MDX]──▶ MdxExpr
                                                │                       │
                                                └────[assemble SML]─────┘
                                                          ▼
                                                       SmlModel (YAML)
```

The Semantic IR is the pivot of the design. Every stage upstream targets the IR; only the MDX emitter reads it. That boundary is deliberate: when the Open Semantic Interchange standardizes a calc-extension grammar, the emitter changes and nothing upstream does.

Three principles govern every translation:

1. **Refuse, don't lie.** Untranslatable DAX produces a structured `Severity.UNSUPPORTED` diagnostic and a TODO marker in the output — never a silent mistranslation. Every lowering carries a test for *when it refuses*.
2. **Lossless re-emission.** Source spans, original DAX text, and comments survive into the SML output as provenance, so a customer can audit what their model became.
3. **Standards-anchored.** Output is meant to validate against the Open Semantic Interchange (OSI) schema, with MDX fragments restricted to a documented "SML-MDX profile" subgrammar (`spec/sml-mdx-profile.md`).

## Install

Requires Python 3.11+. The package isn't published to PyPI yet; install from source:

```bash
git clone https://github.com/joeyen-atscale/atscale-pbi-transpile
cd atscale-pbi-transpile
pip install -e .
```

## Run

The CLI runs today, but every stage is a placeholder — it prints its plan and exits:

```bash
$ atscale-pbi-transpile path/to/model.tmdl -o output.sml
[skeleton] would translate: path/to/model.tmdl
[skeleton] would write SML to: output.sml
[skeleton] would validate: True
Not yet implemented. See README.md for status.
```

`--diagnostics PATH` chooses where the diagnostics sidecar will be written (defaults to `<output>.diag.yaml`); `--no-validate` will skip OSI schema validation. Neither does anything yet beyond being parsed.

## Key concepts

The IR is worth understanding before the rest, because it is where the hard decisions live.

- **Scalar nodes** — `Literal`, `MeasureRef`, `ColumnRef`, `Arithmetic`, `If`, `Coalesce`, `Cast`.
- **Set nodes** — `MemberSet`, `AllMembers`, `TopN`, `FilterSet`, and `RowSet`, the escape hatch for fact-table row-by-row semantics that MDX cannot express. A `RowSet` is never meant to reach the emitter without triggering a refusal.
- **Context nodes** — `WithContext` wraps a body expression with one or more `ContextModification`s (`Override`, `Remove`, `UseRelationship`, `TimeShift`). This is how DAX's `CALCULATE` is modeled: filters reshape the evaluation context, then the body evaluates under it.

Every node carries an `EvaluationContext`, so the distinction between DAX filter context and MDX current-member context is a typed concept rather than implicit pattern-matching. That is what lets a lowering decide, by inspection, whether a construct can be translated or must be refused.

The single source of truth for what DAX is meant to be supported is `coverage/dax_functions.yaml`. Each entry has a status — `supported`, `partial`, `unsupported`, or `refused-by-design` — and points to its lowering module and golden tests. The intent is that CI enforces it: no test or corpus reference without a matching entry. Today the registry describes the target; the enforcement and most of the entries are not yet built.

## Where it fits

This is meant to be the reference implementation of an OSI-aligned semantic-model translator: open-source under Apache 2.0, sitting in the OSI / SML toolchain. The strategic frame — Power BI migration as the use case, standards alignment as the long game — is in `docs/ONE_PAGER.md`. The IR and profile specs are in `spec/`.

## Contributing

`CONTRIBUTING.md` has the rules. The short version: every new DAX lowering ships three artifacts in one PR — the `Lowering` subclass, its `coverage/dax_functions.yaml` entry, and a golden test tuple (`.dax` / `.mdx` / `.sml` / `.diag`). The three principles above are P0; a lowering without a refusal test does not merge.

## License

Apache 2.0. See [LICENSE](LICENSE).
