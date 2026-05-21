# OSI Status & Engagement Plan

Background research on AtScale's Open Semantic Interchange (OSI) position, generated 2026-05-21. Used to scope the transpiler's standards strategy.

## AtScale's membership status

**Full member.** Joined the third cohort on 2026-01-27, alongside Databricks, Qlik, JetBrains, Lightdash, Coalesce, and Credible.

- **CTO David Mariani** is the public OSI champion (per AtScale press release).
- **CEO Chris Lynch** is publicly quoted endorsing the initiative.
- **No specific Technical Steering Committee (TSC) representative** is publicly named — this is worth confirming internally.
- Luis Maldonado (CPO, joined from dbt Labs in Feb 2026) likely has cross-org OSI relationships from his dbt tenure.

## OSI spec state

- **OSI v1.0 finalized January 2026.** (My earlier local artifacts said v0.1.1 — that's from the ontology README which predates the v1.0 release.)
- **v0.2 dev branch active** in the GitHub repo.
- **Three-phase roadmap:**
  1. Specification finalization — complete (Q1 2026).
  2. Native platform support + domain-specific extensions — Q2–Q4 2026.
  3. De facto industry standard + shared semantic-model marketplace — 2027+.
- **Governance:** Apache-style TSC, 2+ approvals required, no vetoes.
- **Working groups:** Advanced Metrics & Expression Language; Composability; Catalog Integration; Ontology Representation; Model Converters & Developer Tools.

## The opening for our calc-IR proposal

**No calc-member / formula-language proposal currently exists in the public OSI repo.** The Advanced Metrics & Expression Language working group is live but underspecified. v1.0 covers simple aggregations (SUM, AVG, COUNT DISTINCT, MIN, MAX) and field-level computations across SQL / Snowflake / Databricks / MDX / Tableau dialects, but **not** calculated members, hierarchies, semi-additive measures, or composite metrics.

The local AtScale ontology (`ontology/osi-bfo.ttl`) already lists "calculated members" as future work — AtScale has implicitly staked the claim, but not yet formalized it.

**This is the opening.** AtScale can propose the `SemanticIR` from this transpiler as the calc-member standardization, with the transpiler itself as the reference implementation.

## Strategic window

The Advanced Metrics & Expression Language working group is live but underspecified. AtScale has the opportunity to anchor the calc-IR proposal before competitors (Databricks, Cube) propose their own. Calendar is engineering and AR's call — the strategic point is **act before competing proposals appear**, not "by a specific date."

## Recommended engagement plan (ordered, not time-bound)

1. **Internal alignment.** Confirm with David Mariani that:
   - AtScale's OSI TSC seat is filled / will be filled.
   - The transpiler-as-calc-IR-reference-implementation positioning aligns with the broader OSI strategy.
   - The OSI proposal can publish under an AtScale org GitHub repo (`github.com/atscaleinc/atscale-pbi-transpile`) with a PR to the OSI specs repo when ready.

2. **Public artifact prep.**
   - Ship the transpiler M1 milestone (stages 1-3 working) with the published `osi-ir-spec.md` as the public draft.
   - Write a short blog post on the AtScale site framing the IR as a community proposal, not an AtScale-internal thing.

3. **OSI RFC filing.**
   - File at `github.com/open-semantic-interchange/OSI` as a Discussion + linked Pull Request.
   - Attach: the IR spec, the reference implementation link, the conformance-suite design, and the 2-3 supporting use cases (Power BI migration, MDX↔SML interop, future Cortex/Genie publisher).
   - Champion: David Mariani as named sponsor.
   - Trigger: after M1 ships (reference implementation is more credible than a paper proposal).

4. **Working group engagement.**
   - Join the Advanced Metrics & Expression Language working group officially.
   - Iterate the IR proposal through working group cycles.
   - Aim for v0.2 inclusion (or v1.1 if it slips).

5. **Marketing alignment.**
   - Coordinate with AtScale marketing on the OSI blog cadence — every milestone in the transpiler should also be an OSI moment.
   - The standard-setter narrative is the strategic payoff; the engineering project is the substantive proof.

## Sources

- [AtScale joins OSI — press release (2026-01-27)](https://www.atscale.com/press/atscale-joins-open-semantic-interchange-open-standards/)
- [AtScale blog: Why we joined OSI](https://www.atscale.com/blog/atscale-joins-osi-open-semantic-infrastructure/)
- [Open Semantic Interchange](https://open-semantic-interchange.org)
- [OSI GitHub repository](https://github.com/open-semantic-interchange/OSI)
- [Snowflake blog: OSI v1.0 finalized](https://www.snowflake.com/en/blog/open-semantic-interchanges-specs-finalized/)
- [dbt Labs blog: OSI spec updates](https://www.getdbt.com/blog/the-osi-spec-updates)
- Local: `/Users/jsy/projects/product/ontology/osi-bfo.ttl` + README (AtScale's formal ontology contribution)
