"""SemanticIR — the load-bearing IR for the DAX -> MDX transpiler.

This is the swap-point that future-proofs the design. Today, stage 5 (the MDX
emitter) consumes these types. When OSI standardizes a calc-extension grammar,
only stage 5 needs to change — every other stage targets the IR directly.

Three node families:
- Scalar nodes — Literal, MeasureRef, ColumnRef, Arithmetic, If, Coalesce, Cast.
- Set nodes — MemberSet, AllMembers, TopN, Filter, RowSet (the unsupported
  escape hatch).
- Context nodes — WithContext(modifications, body) where each modification is
  one of Override, Remove, UseRelationship, TimeShift.

Every node carries EvaluationContext so "DAX filter context vs MDX
current-member context" is a typed concept, not implicit pattern matching.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal as TypingLiteral
from typing import Union


# ── Source spans + diagnostics ────────────────────────────────────────────


@dataclass(frozen=True)
class SourceSpan:
    """Lexical span in the original DAX source. Carried through every node."""

    file: str
    line_start: int
    col_start: int
    line_end: int
    col_end: int
    original_text: str


class Severity(Enum):
    FATAL = "fatal"  # Stops the pipeline.
    UNSUPPORTED = "unsupported"  # Records a TODO; pipeline continues.
    WARNING = "warning"  # Pipeline continues; emitted in the diagnostics sidecar.
    INFO = "info"


@dataclass(frozen=True)
class Diagnostic:
    severity: Severity
    code: str  # e.g. "REFUSE_ROW_CTX_FACT_TABLE", "UNKNOWN_DAX_FUNCTION"
    message: str
    source: SourceSpan
    suggestion: str | None = None


# ── Evaluation context ────────────────────────────────────────────────────


@dataclass(frozen=True)
class EvaluationContext:
    """The semantic context every IR node evaluates within.

    `filter_ctx` mirrors DAX filter context — a map from dimension to
    constraining set. `row_ctx` mirrors DAX row context — the current row
    bindings when inside an iterator. `current_member_bindings` is the
    MDX-side equivalent expression of the same state.

    The transpiler refuses to emit MDX when row_ctx requires fact-table-row
    semantics that MDX cannot express.
    """

    filter_ctx: dict[str, "SetNode"] = field(default_factory=dict)
    row_ctx: dict[str, "ColumnRef"] = field(default_factory=dict)
    current_member_bindings: dict[str, str] = field(default_factory=dict)


# ── Scalar nodes ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Literal:
    value: float | int | str | bool
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class MeasureRef:
    name: str
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class ColumnRef:
    table: str
    column: str
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class Arithmetic:
    op: TypingLiteral["+", "-", "*", "/"]
    left: "ScalarNode"
    right: "ScalarNode"
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class If:
    cond: "ScalarNode"
    then_: "ScalarNode"
    else_: "ScalarNode"
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class Coalesce:
    args: tuple["ScalarNode", ...]
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class Cast:
    expr: "ScalarNode"
    target_type: TypingLiteral["INT", "DECIMAL", "STRING", "BOOLEAN", "DATE"]
    source: SourceSpan
    ctx: EvaluationContext


# ── Set nodes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MemberSet:
    dimension: str
    predicate: "ScalarNode | None"  # None means all members.
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class AllMembers:
    dimension: str
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class TopN:
    n: int
    over: "SetNode"
    order_by: "ScalarNode"
    descending: bool
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class FilterSet:
    over: "SetNode"
    predicate: "ScalarNode"
    source: SourceSpan
    ctx: EvaluationContext


@dataclass(frozen=True)
class RowSet:
    """The unsupported escape hatch.

    When a DAX construct requires fact-table row-by-row evaluation that has no
    clean MDX equivalent, lower it to a RowSet and let the emitter refuse with
    a structured diagnostic. RowSet should never reach the MDX emitter without
    triggering a Diagnostic.UNSUPPORTED.
    """

    table: str
    predicate: "ScalarNode | None"
    source: SourceSpan
    ctx: EvaluationContext


# ── Context-modification nodes ────────────────────────────────────────────


class ContextModification:
    """Abstract — concrete subclasses are Override / Remove / UseRelationship / TimeShift."""


@dataclass(frozen=True)
class Override(ContextModification):
    """Replace filter context for a dimension."""

    dimension: str
    new_set: "SetNode"


@dataclass(frozen=True)
class Remove(ContextModification):
    """Remove any filter on a dimension (the ALL() / REMOVEFILTERS pattern)."""

    dimension: str


@dataclass(frozen=True)
class UseRelationship(ContextModification):
    """Switch active relationship between two tables.

    The transpiler maps this to SML role-play-name navigation when emitting.
    """

    from_table: str
    from_column: str
    to_table: str
    to_column: str


@dataclass(frozen=True)
class TimeShift(ContextModification):
    """Time-intelligence modifier — emitted as MDX ParallelPeriod / Lag / YTD / etc.

    `scope` is the time-hierarchy level (YEAR / QUARTER / MONTH / DAY).
    `n` is the shift amount (negative for prior, 0 for to-date).
    `kind` distinguishes shift-vs-to-date.
    """

    scope: TypingLiteral["YEAR", "QUARTER", "MONTH", "WEEK", "DAY"]
    n: int
    kind: TypingLiteral["SHIFT", "TO_DATE", "PARALLEL"]


@dataclass(frozen=True)
class WithContext:
    """The CALCULATE / CALCULATETABLE / time-intel parent node.

    Wraps a body expression with one or more context modifications. The MDX
    emitter chooses between tuple emission (pure overrides on a MeasureRef body)
    and synthesized WITH MEMBER emission (composite bodies, REMOVE filters, or
    multi-modification stacks).
    """

    modifications: tuple[ContextModification, ...]
    body: "Node"
    source: SourceSpan
    ctx: EvaluationContext


# ── Union types ───────────────────────────────────────────────────────────


ScalarNode = Union[Literal, MeasureRef, ColumnRef, Arithmetic, If, Coalesce, Cast]
SetNode = Union[MemberSet, AllMembers, TopN, FilterSet, RowSet]
Node = Union[ScalarNode, SetNode, WithContext]
