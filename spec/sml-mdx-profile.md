# SML-MDX Profile

The subgrammar of MDX that AtScale's MDX engine contractually accepts as the body of an SML `calc-member` definition. The DAX → MDX transpiler emits MDX fragments strictly within this profile; anything outside is a bug.

**Status: skeleton.** This spec is the single source of truth that the CI round-trip validator checks against a live AtScale dev instance. Treat it as load-bearing.

## Why we need this

Full MDX is a sprawling language. AtScale's engine accepts a known subset — not always the same subset as Microsoft SSAS or Mondrian. Writing this down explicitly:
- Gives the transpiler emitter a precise target.
- Gives the AtScale engine team a contract they can hold steady.
- Gives OSI a reference for what "OSI MDX profile" means (a published, vendor-neutral subset).

## Profile rules (draft)

### Allowed expressions

- Tuple expressions: `([Measures].[<measure>], [<dim>].[<member>], ...)`
- Calculated members: `WITH MEMBER [Measures].[__calc_N] AS <expr> ...`
- Aggregation: `Aggregate(<set>, <numeric expr>)`
- Set comprehensions over dimensions: `Generate(<set>, <expr>)`, `Filter(<set>, <predicate>)`, `Order(<set>, <expr>, ASC|DESC)`
- Time navigation: `PrevMember`, `NextMember`, `Lag(<n>)`, `Lead(<n>)`, `ParallelPeriod`, `YTD()`, `QTD()`, `MTD()`
- Hierarchy navigation: `CurrentMember`, `Parent`, `FirstChild`, `Lag(n)`, `.Members`, `.AllMembers`
- Scalar: `IIF(<cond>, <then>, <else>)`, arithmetic `+ - * /`, `CoalesceEmpty`
- Member properties: `<member>.Properties("PROPERTY")`

### Disallowed (refused by emitter)

- MDX DDL: `CREATE`, `DROP`, `ALTER`.
- Server-side scripts / stored procedures.
- Cell calculations referencing other cube cells (cell-by-cell evaluation).
- `Strtomember` / `Strtoset` dynamic resolution (security risk; non-deterministic).
- Arbitrary recursion in calculated-member definitions.

### Examples

Pure dimension override (DAX `CALCULATE([Sales], Product[Cat] = "Elec")`):
```mdx
([Measures].[Sales], [Product].[Category].[Electronics])
```

Composite with REMOVEFILTERS (DAX `CALCULATE([Sales], ALL(Product))`):
```mdx
([Measures].[Sales], [Product].[All Products])
```

Time intelligence (DAX `SAMEPERIODLASTYEAR(Sales)`):
```mdx
WITH MEMBER [Measures].[__spy_Sales] AS
  ([Measures].[Sales], ParallelPeriod([Date].[Calendar].[Year], 1, [Date].[Calendar].CurrentMember))
```

## Open questions

1. **`Generate` over fact-row sets:** the engine may or may not support. Needs validation.
2. **Cell calculations vs calc members:** confirm the engine prefers calc members for our use case.
3. **MDX functions added quarterly:** keep a CI test that enumerates every supported function and round-trips a known-good fragment.

## Source of truth

This file is the spec. The CI workflow at `tests/integration/test_engine_round_trip.py` validates every emitted fragment against a live AtScale dev instance and reports drift.
