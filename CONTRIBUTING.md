# Contributing to atscale-pbi-transpile

This is an open-source project aligned with the [Open Semantic Interchange (OSI)](https://open-semantic-interchange.org) initiative. Contributions from outside AtScale are welcome.

## The three invariants

These are P0 — every PR is evaluated against them:

1. **Refuse, don't lie.** Any DAX construct that cannot be faithfully translated to MDX must emit a structured `Severity.Unsupported` diagnostic. Silent mistranslation is the worst possible outcome — it produces a working pipeline that yields wrong numbers, which destroys trust in the entire toolchain. Every lowering must have a "when does this refuse" test case.
2. **Lossless re-emission.** Source spans, original DAX text, and comments must survive into the SML output as provenance. The transpiler is auditable by the customer who imported the model.
3. **Standards-anchored.** Output is meant to validate against the Open Semantic Interchange (OSI) schema. MDX fragments stay within the documented "SML-MDX profile" subgrammar (`spec/sml-mdx-profile.md`).

## Adding a DAX function

Every new lowering ships with **three artifacts** in the same PR:

1. **A `Lowering` subclass** in the appropriate `src/atscale_pbi_transpile/lower/<family>.py`.
2. **A coverage entry** in `src/atscale_pbi_transpile/coverage/dax_functions.yaml`. Status must be one of `supported`, `partial`, `unsupported`, `refused-by-design`. If `partial`, list every `partial_reason`.
3. **A golden test tuple** in `tests/golden/<family>/<id>.{dax,mdx,sml,diag}.txt`. Four files. The `.diag` file lists expected diagnostics (empty if none).

The intent is that CI enforces this — a PR adding a function without all three artifacts should not pass. The workflow that checks it is part of the build-out, not yet wired up, so until then the rule is enforced by review.

## Pull request flow

1. Fork the repo.
2. Branch from `main`.
3. Make changes; ensure tests pass (`pytest tests/golden/`).
4. Update `spec/coverage-table.md` if your change affects the coverage table — it's generated from the YAML, but the generated file is also committed for browsing.
5. Open a PR. The CI workflow validates: tests, coverage-table consistency, OSI schema validation on emitted SML, MDX engine round-trip (if you have a dev AtScale instance configured).

## Style

- Python 3.11+, type hints everywhere, `mypy --strict` clean.
- `ruff` for lint + format.
- Docstrings on public APIs.

## License

Apache 2.0. By contributing, you agree your contributions are released under the same license.

## Code of conduct

Be kind. We're trying to build something that lots of people will rely on.
