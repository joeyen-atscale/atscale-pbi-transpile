# Coverage table

This file is **auto-generated** from `src/atscale_pbi_transpile/coverage/dax_functions.yaml` at every release. Do not edit by hand.

Last generated: 0.0.1 (skeleton)

## Status legend

- ✅ **supported** — full faithful translation; all known forms covered.
- 🟡 **partial** — some forms translate, others refuse. See partial_reasons.
- 🔴 **unsupported** — no lowering yet; on the roadmap.
- ⛔️ **refused-by-design** — cannot be faithfully translated. Workaround documented.

## Functions

| Function | Status | Lowering | Notes |
|---|---|---|---|
| `CALCULATE` | ✅ supported | `lower/calculate.py:CalculateLowering` | Pure dimension overrides → tuples; composite/REMOVEFILTERS → synthesized WITH MEMBER. |
| `SUM` / `AVERAGE` / `COUNT` / `DISTINCTCOUNT` | ✅ supported | `lower/aggregations.py` | Standard aggregations. |
| `SUMX` / `AVERAGEX` | 🟡 partial | `lower/iterators.py` | Refuses on fact-table iteration. |
| `FILTER` | 🟡 partial | `lower/iterators.py:FilterLowering` | Only over dimension tables. |
| `ALL` / `ALLEXCEPT` | ✅ supported | `lower/calculate.py` | Lower to Remove context modification. |
| `RELATED` | ✅ supported | `lower/relationships.py:RelatedLowering` | Navigate relationship to related column. |
| `USERELATIONSHIP` | 🟡 partial | `lower/relationships.py` | One inactive relationship per measure in v1.0. |
| `IF` / `SWITCH` | ✅ supported | `lower/scalar.py` | Maps to MDX IIF / nested IIF. |
| `SAMEPERIODLASTYEAR` | ✅ supported | `lower/time_intelligence.py` | Requires marked Date table. |
| `TOTALYTD` | ✅ supported | `lower/time_intelligence.py` | Requires marked Date table. |
| `DATEADD` | ✅ supported | `lower/time_intelligence.py:DateAddLowering` | |
| `PARALLELPERIOD` | ✅ supported | `lower/time_intelligence.py` | |
| `TOPN` | ✅ supported | `lower/sets.py:TopNLowering` | Maps to MDX TOPCOUNT. |
| `VALUES` | ✅ supported | `lower/sets.py:ValuesLowering` | Maps to MDX dimension.Members. |
| `RANKX` | ⛔️ refused-by-design | — | Row-context ranking has no clean MDX analog. Workaround: AtScale-native MDX RANK() in manually-authored calc member. |
| `EARLIER` | ⛔️ refused-by-design | — | EARLIER's nested row-context semantics have no MDX equivalent. Workaround: refactor DAX to VAR/RETURN before transpiling. |

## Coverage by category (skeleton)

| Category | Supported | Partial | Refused | Total |
|---|---|---|---|---|
| Aggregations | 4 | 0 | 0 | 4 |
| Context modifiers | 3 | 0 | 0 | 3 |
| Iterators | 0 | 3 | 1 (`EARLIER`) | 4 |
| Time intelligence | 4 | 0 | 0 | 4 |
| Relationships | 1 | 1 | 0 | 2 |
| Scalar control flow | 2 | 0 | 0 | 2 |
| Sets / ranking | 2 | 0 | 1 (`RANKX`) | 3 |

(Numbers expand as the coverage table grows.)
