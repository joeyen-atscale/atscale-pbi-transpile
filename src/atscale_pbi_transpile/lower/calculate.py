"""Lowering for DAX CALCULATE / CALCULATETABLE.

CALCULATE is the most semantically rich DAX function. Its general shape is:

    CALCULATE(<expression>, <filter1>, <filter2>, ...)

Each filter modifies the evaluation context, then `<expression>` evaluates
under the modified context. Filters can be:
- Dimension constraints (Product[Category] = "Electronics") -> Override modification
- ALL(...) / REMOVEFILTERS -> Remove modification
- USERELATIONSHIP(...) -> UseRelationship modification
- Time-intelligence functions (SAMEPERIODLASTYEAR, etc.) -> TimeShift modification

This module produces a WithContext IR node from a parsed CALCULATE call.
The MDX emitter (in emit/mdx/) decides whether to emit a tuple or a
synthesized WITH MEMBER based on the structure of the modifications and body.

Skeleton — real lowering depends on the ANTLR-generated DAX AST.
"""

from __future__ import annotations

from atscale_pbi_transpile.ir.types import (
    ContextModification,
    Diagnostic,
    Node,
    Severity,
    SourceSpan,
    WithContext,
)


class CalculateLowering:
    """Lowers a DAX CALCULATE(...) call to a WithContext IR node."""

    DAX_FUNCTION = "CALCULATE"

    def lower(self, args: list[object], source: SourceSpan) -> tuple[Node | None, list[Diagnostic]]:
        """Lower a parsed CALCULATE call.

        args[0] is the body expression. args[1:] are the filter arguments.

        Returns (ir_node, diagnostics). If ir_node is None, the lowering refused;
        diagnostics will contain at least one Severity.UNSUPPORTED entry.
        """
        diagnostics: list[Diagnostic] = []

        if len(args) < 1:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.FATAL,
                    code="CALCULATE_NO_ARGS",
                    message="CALCULATE called with no arguments.",
                    source=source,
                )
            )
            return None, diagnostics

        # TODO: dispatch each args[1:] entry through the modification-classifier.
        # Each filter argument becomes a ContextModification. Filter classification
        # is the hard part — dimension-equality, ALL(), USERELATIONSHIP(), and
        # time-intel functions all produce different ContextModification subclasses.

        # PLACEHOLDER: return None to signal "not yet implemented" — real lower()
        # walks the parsed AST. The downstream pipeline must not see a None IR
        # without an accompanying FATAL diagnostic.
        diagnostics.append(
            Diagnostic(
                severity=Severity.UNSUPPORTED,
                code="NOT_YET_IMPLEMENTED",
                message="CalculateLowering.lower() is not yet implemented.",
                source=source,
                suggestion="See lower/calculate.py for the TODO list.",
            )
        )
        return None, diagnostics


class AllLowering:
    """Lowers a DAX ALL(...) call as a context-modification (Remove or filter-set).

    ALL has two meanings depending on syntactic position:
    - Inside CALCULATE filter slot: REMOVE the dimension's filter context.
    - As a set expression: produce the AllMembers set of a dimension.

    This class implements both; the dispatching is done by the parent CALCULATE
    lowering (when ALL appears in a filter slot) or by an enclosing set context.
    """

    DAX_FUNCTION = "ALL"
    # TODO: implement


class AllExceptLowering:
    """Lowers ALLEXCEPT(<table>, <col1>, <col2>, ...) into a Remove modification."""

    DAX_FUNCTION = "ALLEXCEPT"
    # TODO: implement
