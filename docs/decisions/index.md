# Architectural Decision Records (ADRs)

An Architectural Decision (AD) is a justified software design choice that addresses a functional or non-functional requirement that is architecturally significant. An Architectural Decision Record (ADR) captures a single AD and its rationale.

For more information [see](https://adr.github.io/)

## How to Create an ADR

1. Copy `adr-template.md` to `NNNN-title-with-dashes.md`, where NNNN indicates the next number in sequence.
   - Check for existing PR's to make sure you use the correct sequence number.
   - There is also a short form template `adr-short-template.md` for smaller decisions.
2. Edit `NNNN-title-with-dashes.md`.
   - Status must initially be `proposed`
   - List `deciders` who will sign off on the decision
   - List people who were `consulted` or `informed` about the decision
3. For each option, list the good, neutral, and bad aspects of each considered alternative.
4. Share your PR with the deciders and other interested parties.
   - The status must be updated to `accepted` once a decision is agreed and the date must also be updated.
5. Decisions can be changed later and superseded by a new ADR.

## When to Create an ADR

Create ADRs for:

- Architecture patterns (tool registration, dependency injection, callbacks)
- Technology choices (framework selection, library decisions)
- Design patterns (component interaction, abstraction layers)
- API designs (public interfaces, method signatures, response formats)
- Naming conventions (class names, module structure, terminology)
- Testing strategies (test organization, mocking patterns, coverage targets)
- Performance trade-offs (caching strategies, optimization choices)
- Security decisions (authentication methods, data handling)

**Rule of thumb**: If the decision could be made differently and the alternative would be reasonable, document it with an ADR.

## Templates

- **Full Template**: [`adr-template.md`](./adr-template.md) - Comprehensive template with all sections
- **Short Template**: [`adr-short-template.md`](./adr-short-template.md) - Simplified template for smaller decisions

## ADR Index

!!! info "Superseded ADRs"
    Superseded ADRs are kept for historical context. The replacement ADR is linked in the Status column.

### Deployment Architecture

| ADR | Title | Status |
|-----|-------|--------|