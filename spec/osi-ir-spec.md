# OSI Semantic IR — Proposal

The intermediate representation used by `atscale-pbi-transpile` between DAX parsing (stage 3) and MDX/SML emission (stage 5/6). This document is the proposed contribution to OSI v0.2.

**Status: draft.** This spec ships as a proposal to the Open Semantic Interchange (OSI) committee. AtScale ships the reference implementation while ratification happens.

## Motivation

OSI v1.0 (released January 2026) defines a YAML model serialization (SML) but does not standardize a vendor-neutral expression IR for calculation logic. The Advanced Metrics & Expression Language working group exists but has no published calc-member proposal yet — this proposal is intended to fill that slot. As more semantic-layer products participate in OSI (Cube, dbt, Coalesce, etc.), interop requires translating between vendor-specific calc languages (DAX, MetricFlow YAML, LookML, MDX, Cube CalcExpressions). Without a shared IR, every translator is an N-to-M problem.

**Proposal: OSI standardizes a shared `SemanticIR` for calc expressions.** Vendor frontends parse to the IR; vendor backends emit from it. The IR becomes the canonical interchange representation alongside the SML model schema.

## Design

The IR has three node families:

### Scalar nodes

- `Literal(value, type)` — numeric / string / boolean / date literal.
- `MeasureRef(name)` — reference to a defined measure.
- `ColumnRef(table, column)` — reference to a model column.
- `Arithmetic(op, left, right)` — `+`, `-`, `*`, `/`.
- `If(cond, then, else)` — conditional.
- `Coalesce(args)` — null-coalesce.
- `Cast(expr, target_type)` — type coercion.

### Set nodes

- `MemberSet(dimension, predicate)` — set of dimension members matching a predicate.
- `AllMembers(dimension)` — all members of a dimension.
- `TopN(n, over, order_by, descending)` — top-N selection over a set.
- `FilterSet(over, predicate)` — set filtered by a scalar predicate.
- `RowSet(table, predicate)` — fact-table row set (the unsupported escape hatch for vendors whose backends don't support row-level evaluation).

### Context nodes

- `WithContext(modifications, body)` — wraps a body expression with one or more context modifications. Each modification is:
  - `Override(dimension, new_set)` — replace filter context for a dimension.
  - `Remove(dimension)` — remove filter context for a dimension.
  - `UseRelationship(from_table, from_col, to_table, to_col)` — switch active relationship.
  - `TimeShift(scope, n, kind)` — time-intelligence modifier.

## Evaluation context

Every node carries an `EvaluationContext` that explicitly tracks:
- `filter_ctx` — map from dimension to constraining set
- `row_ctx` — map from column name to row binding (when inside iterators)
- `current_member_bindings` — MDX-side equivalent expression of the same state

This makes "filter context vs row context" — the trickiest semantic concept in DAX — a typed concept rather than implicit. Backends can refuse cleanly when row context cannot be satisfied (e.g., MDX has no fact-table row notion).

## Diagnostics

Lowerings produce `Diagnostic(severity, code, message, source, suggestion)` alongside the IR. Severities:
- `FATAL` — pipeline stops.
- `UNSUPPORTED` — record TODO; pipeline continues with partial output.
- `WARNING` — pipeline continues; emitted in diagnostics sidecar.
- `INFO` — informational only.

The IR carries `SourceSpan(file, line_start, col_start, line_end, col_end, original_text)` on every node so diagnostics and emitted output can reference the original source location.

## Reference implementation

[`src/atscale_pbi_transpile/ir/types.py`](../src/atscale_pbi_transpile/ir/types.py) in this repo is the proposed reference. It mirrors this spec exactly.

## Submission target

OSI v0.2 — proposed for inclusion alongside the existing SML model serialization. PR draft will be opened against the OSI specs repo once the IR has been validated against the DAX → MDX round-trip CI here.

## Open questions for the committee

1. **Should the IR be serializable (YAML/JSON), or only an in-memory representation?** Serialization helps with debugging and ecosystem tooling, but adds a versioning surface.
2. **Should `RowSet` be in the standard, or vendor-specific?** Including it forces backends that don't support row-level evaluation to refuse explicitly (good). Excluding it makes the IR cleaner (bad for vendors that DO support row-level eval, like dbt SL via warehouse pushdown).
3. **Should the IR include type-checking rules?** A type system catches more errors at IR construction time but increases the spec surface.
4. **How are vendor-specific extensions added?** Annotation slots? Namespaced extension nodes?
