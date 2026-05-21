# OSI RFC: Semantic Calc-IR for OSI v0.2

| Field | Value |
|---|---|
| **Title** | Semantic Calc-IR for OSI v0.2 |
| **Status** | Draft (pre-submission) |
| **Submitter** | AtScale, Inc. — David Mariani (CTO, sponsor); Joe Yen (PM, author) |
| **Date** | 2026-05-21 |
| **Target OSI version** | v0.2 |
| **Working group** | Advanced Metrics & Expression Language |
| **Reference implementation** | [`atscale-pbi-transpile`](https://github.com/atscaleinc/atscale-pbi-transpile) — Apache 2.0 |
| **Companion ontology PR** | extension of `osi-bfo.ttl` adding `osi:DaxDialect` + calc-member classes |

---

## Abstract

OSI v1.0 standardized the SML model serialization across the 50+ semantic-layer products in the consortium, but did not standardize a vendor-neutral expression IR for the calculation logic those models contain. As participants grow, every pair of products that wants to interoperate at the calculation level faces an N-to-M translation problem (DAX ↔ MetricFlow YAML ↔ LookML ↔ MDX ↔ Cube CalcExpressions). This RFC proposes that OSI standardize a **Semantic Calc-IR** as a shared intermediate representation for calc-member, metric, and time-intelligence expressions. Frontends parse to the IR; backends emit from it. The IR is published alongside the SML schema as a normative part of the OSI specification.

This RFC is accompanied by a reference implementation — `atscale-pbi-transpile` — that uses the proposed IR to translate Power BI Tabular Model (`.tmdl` / `.bim`) files into OSI-conformant SML. The reference implementation is intended to validate the IR design through a real translation pipeline before the spec is ratified.

---

## 1. Motivation

### 1.1 The N-to-M interop problem

OSI v1.0 lets two semantic layers describe the same model in a shared YAML format. But the *calculation* layer remains vendor-specific:

| Product | Calc language |
|---|---|
| Power BI / SSAS Tabular | DAX |
| dbt Semantic Layer | MetricFlow YAML |
| Looker | LookML |
| AtScale / OLAP | MDX |
| Cube | Cube CalcExpressions |
| Coalesce | Coalesce expressions |

Every translator written between any two of these is a vendor-pair-specific effort. With 50+ OSI members, the number of pairwise translations is combinatorial. Without a shared IR, the calc-language layer remains an interop wall.

### 1.2 Concrete near-term use case

AtScale's `atscale-pbi-transpile` project (companion to this RFC) translates Power BI Tabular Model files into SML. It needs to translate DAX measure expressions into MDX-flavored SML calc members. Building one DAX-aware parser feeding one MDX-targeted emitter solves the AtScale case, but the same problem will recur for every OSI member adding any new frontend or backend. If the IR is standardized:

- AtScale's DAX parser feeds the shared IR.
- dbt's MetricFlow translator can also emit to / consume from the same IR.
- Cube's CalcExpression evaluator can target the IR for export.
- Future LLM-based metric translators have a typed target rather than freeform text-to-text.

### 1.3 Goal of this RFC

Standardize the IR. Make AtScale's reference implementation the canonical example. Establish a conformance suite (the golden dataset) that any vendor can run against their own translator.

---

## 2. Proposal

### 2.1 IR shape

The IR is a typed expression tree with three node families and explicit evaluation context attached at every node.

#### Scalar nodes

Pure-value expressions evaluating to a single cell.

| Node | Fields |
|---|---|
| `Literal` | `value`, `type` (number / string / boolean / date) |
| `MeasureRef` | `name` |
| `ColumnRef` | `table`, `column` |
| `Arithmetic` | `op ∈ {+, -, *, /}`, `left`, `right` |
| `If` | `cond`, `then`, `else` |
| `Coalesce` | `args[]` |
| `Cast` | `expr`, `target_type ∈ {INT, DECIMAL, STRING, BOOLEAN, DATE}` |

#### Set nodes

Multi-row / multi-member expressions evaluating to a set.

| Node | Fields |
|---|---|
| `MemberSet` | `dimension`, `predicate` (optional scalar) |
| `AllMembers` | `dimension` |
| `TopN` | `n`, `over` (set), `order_by` (scalar), `descending` (bool) |
| `FilterSet` | `over` (set), `predicate` (scalar) |
| `RowSet` | `table`, `predicate` — the unsupported-on-some-backends escape hatch |

#### Context nodes

Wrap a body expression with modifications to its evaluation context.

| Node | Fields |
|---|---|
| `WithContext` | `modifications[]`, `body` |

Modifications:

| Modification | Fields | Semantics |
|---|---|---|
| `Override` | `dimension`, `new_set` | Replace filter context for the dimension. |
| `Remove` | `dimension` | Remove any filter on the dimension (ALL / REMOVEFILTERS). |
| `UseRelationship` | `from_table`, `from_column`, `to_table`, `to_column` | Switch active relationship between two tables. |
| `TimeShift` | `scope ∈ {YEAR, QUARTER, MONTH, WEEK, DAY}`, `n`, `kind ∈ {SHIFT, TO_DATE, PARALLEL}` | Time-intelligence modifier. |

### 2.2 Evaluation context

Every node carries:

```
EvaluationContext {
  filter_ctx: map<dimension, SetNode>,
  row_ctx: map<column, ColumnRef>,
  current_member_bindings: map<dimension, str>
}
```

This makes "filter context vs row context" — the trickiest semantic concept in DAX, the implicit pivot in MDX, and the source of most translator bugs — a **typed concept rather than implicit pattern matching**. Backends can refuse cleanly when row context cannot be satisfied (e.g., MDX has no fact-table row notion).

### 2.3 Source provenance

Every node carries:

```
SourceSpan {
  file: str,
  line_start, col_start, line_end, col_end: int,
  original_text: str
}
```

This enables three things:

- **Diagnostics** that point to the original source location.
- **Provenance comments** in emitted output linking back to source.
- **Round-trip auditability** — the customer can see what the translator did with each piece of their model.

### 2.4 Diagnostics channel

Lowerings emit `Diagnostic` records alongside the IR:

```
Diagnostic {
  severity: FATAL | UNSUPPORTED | WARNING | INFO,
  code: str,
  message: str,
  source: SourceSpan,
  suggestion: str?
}
```

`UNSUPPORTED` is the load-bearing severity: it lets a backend refuse a specific construct without aborting the whole pipeline. This is how the **"refuse, don't lie"** invariant gets enforced: a translator emits an `UNSUPPORTED` diagnostic instead of producing semantically-wrong output. Conformant implementations MUST refuse rather than silently mistranslate.

### 2.5 Conformance suite

The reference implementation publishes a golden dataset of four-file tuples (`.input` / `.ir` / `.expected_emission_for_each_target` / `.diagnostics`). Any vendor's IR implementation can be conformance-tested against this dataset. The conformance suite is the operational definition of "correctly implements OSI Calc-IR."

---

## 3. Rationale

### 3.1 Why an IR and not a calc-language standard?

Standardizing a new calc language ("OSI Calc") would compete with existing vendor languages and be adopted by nobody. Standardizing the **IR between languages** lets every vendor keep its frontend / backend while sharing the translation surface. The IR is the "calc layer's USB-C" — vendor frontends and backends are the wall-plug adapters.

### 3.2 Why explicit context as a first-class concept?

The two most common failure modes of cross-language calc translation are:

1. **Filter-context confusion** — DAX's `CALCULATE(expr, filter)` modifies filter context; MDX's slicer modifies current-member context. These are different operations with different semantics. Conflating them produces wrong numbers.
2. **Row-context unfaithfulness** — DAX iterators (`SUMX`, `AVERAGEX`, `FILTER`) introduce row context that has no clean MDX equivalent for arbitrary fact-table rows. Translators that paper over this produce wrong numbers.

Making `EvaluationContext` part of the IR's type system forces these to be explicit. A translator that wants to convert from DAX row-context-iteration must either lower to `Aggregate(SetNode, ScalarNode)` (faithful) or emit an `UNSUPPORTED` diagnostic (refuse). The IR makes the choice unavoidable rather than implicit.

### 3.3 Why an escape hatch (`RowSet`)?

Not all backends support every construct. `RowSet` is the "this requires row-level evaluation" node. Backends that can evaluate fact-table row sets (dbt SL via warehouse pushdown, Cube via Cube Store) can implement it. Backends that cannot (MDX engines, in-memory column stores without row-iteration semantics) emit an `UNSUPPORTED` diagnostic when they see a `RowSet`. This makes the boundary explicit and auditable rather than buried in vendor-specific edge-case handling.

### 3.4 Why no execution semantics?

The RFC defines the IR as a structural representation. **Execution semantics are vendor-specific** — DAX's actual evaluation order, MDX's hierarchical cube space, MetricFlow's compile-then-pushdown — and the IR does not try to standardize them. Translators are responsible for emitting target code with correct semantics for that target. The IR is the lingua franca; the semantics are still the target's responsibility.

This is intentional. Standardizing execution semantics is a 5-year project and would block adoption. Standardizing the structural representation is the high-leverage win.

---

## 4. Reference implementation

`atscale-pbi-transpile` ([repo](https://github.com/atscaleinc/atscale-pbi-transpile)) is the reference. Key files:

| File | Role |
|---|---|
| `src/atscale_pbi_transpile/ir/types.py` | Concrete Python types implementing this RFC's IR. |
| `src/atscale_pbi_transpile/lower/` | DAX-AST → IR lowering. One subclass per DAX function family. |
| `src/atscale_pbi_transpile/emit/mdx/` | IR → MDX emitter (the first backend; targets AtScale's MDX engine). |
| `src/atscale_pbi_transpile/coverage/dax_functions.yaml` | Coverage registry — every DAX function tracked with status (supported / partial / unsupported / refused-by-design). |
| `tests/golden/` | Golden dataset, becomes the OSI conformance suite. |

The reference implementation is Apache 2.0 and developed in public.

---

## 5. Adoption path

1. **OSI ratification.** This RFC moves through the Advanced Metrics & Expression Language working group. Two-approval-no-veto governance per OSI's TSC process.
2. **Reference implementation matures.** AtScale ships `atscale-pbi-transpile` v1.0 with full DAX → MDX coverage validated by the golden dataset.
3. **Second-backend validation.** A second backend implementation (dbt MetricFlow emit, Cube CalcExpression emit, or LookML emit) proves the IR is not MDX-shaped.
4. **OSI v0.2 includes the IR spec.** Released alongside the existing SML schema as a normative part of OSI.
5. **Conformance suite published.** Any vendor's translator can be conformance-tested.

---

## 6. Open questions

For working-group discussion before ratification:

1. **Serializable IR?** Should the IR have a YAML / JSON serialization in addition to in-memory representation? Pro: debugging, ecosystem tooling, cross-process translation. Con: another versioning surface; conformance suite is already executable.
2. **`RowSet` in the standard?** Including it forces backends without row-evaluation to refuse explicitly (good for safety). Excluding it makes the IR cleaner but pushes the row-vs-set distinction into vendor-specific handling.
3. **Type system.** Should the IR include type-checking rules (e.g. `Arithmetic` operands must be numeric)? Pro: catches errors at IR construction. Con: larger spec surface; competes with each language's own type system.
4. **Vendor-specific extensions.** Annotation slots vs namespaced extension nodes vs both? How does a vendor add an IR node that's specific to its product without polluting the shared spec?
5. **Execution semantics where they overlap.** Some semantics (`Override` should produce a filter exactly matching the dimension's filter context after the override) feel universal. Should those be normative? Or is everything vendor-specific?

---

## 7. Compatibility with OSI v1.0

The IR is **additive**. SML v1.0 models that use only the existing calc-member fields continue to validate against the v0.2 spec. New IR-based calc-member representations are an opt-in alternative. The migration story is gentle:

- Existing OSI v1.0 implementations: no breakage. Continue using vendor-native calc representations inside SML.
- New v0.2-aware implementations: opt in to producing IR-shaped calc members; gain interop.
- Mixed environments: the IR is the interchange format; vendor-native representations remain valid storage.

---

## 8. Acknowledgments

- **Open Semantic Interchange community** for the SML model spec that this RFC extends.
- **DaxStudio** for the open-source ANTLR4 DAX grammar that the reference implementation forks.
- **AtScale's `dialect-translator` and `dbt-to-sml` prior art** for the pattern library this RFC formalizes into types.

---

## 9. Filing checklist

Pre-submission to `github.com/open-semantic-interchange/OSI`:

- [ ] Internal review: David Mariani signs off as sponsor.
- [ ] Internal review: AtScale engineering DRI confirms IR shape is implementable.
- [ ] Reference implementation: M1 ships (stages 1-3 working on real `.tmdl`).
- [ ] Companion ontology PR drafted against `osi-bfo.ttl`.
- [ ] OSI Discussions post drafted with links.
- [ ] OSI PR drafted against the specs repo with this RFC as the proposal text.
- [ ] Second-backend feasibility note (which vendor will implement first non-MDX emit?).

When all checked: file the Discussion + PR.
