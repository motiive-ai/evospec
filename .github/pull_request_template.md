## Summary

<!-- What does this PR do? One paragraph. -->

## Change Type

<!-- Check one -->
- [ ] 🧪 Experiment (edge zone — hypothesis-driven)
- [ ] 🏗️ Improvement (known need — deliberate)
- [ ] 🐛 Bug fix
- [ ] 📚 Documentation
- [ ] 🔧 Tooling / CI

## Zone

<!-- Auto-detected from spec.yaml if available -->
- [ ] Edge (discovery layer)
- [ ] Hybrid (crosses boundary)
- [ ] Core (engine layer)

## Spec Artifacts

<!-- List the spec directory and artifacts created/updated -->
- **Spec path**: `specs/changes/...`
- [ ] `spec.yaml`
- [ ] `discovery-spec.md`
- [ ] `domain-contract.md`
- [ ] `tasks.md`
- [ ] `implementation-spec.md`

## Invariant Impact

<!-- Output of `evospec check` or MCP check_invariant_impact -->
- [ ] No invariant conflicts
- [ ] Conflicts resolved (see spec.yaml → invariant_impact.conflicts)

## Domain Changes

<!-- Were domain files updated? -->
- [ ] `specs/domain/entities.yaml`
- [ ] `specs/domain/contexts.yaml`
- [ ] `specs/domain/features.yaml`
- [ ] `specs/domain/glossary.md`
- [ ] `specs/domain/context-map.md`
- [ ] No domain changes

## Fitness Functions

<!-- For core/hybrid zone -->
- [ ] All fitness functions pass (`evospec check --run-fitness`)
- [ ] New fitness functions added
- [ ] N/A (edge zone)

## Checklist

- [ ] `evospec check` passes
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Agent files regenerated (`evospec generate agents`) if workflows changed
- [ ] Documentation updated if user-facing behavior changed

## Screenshots / Examples

<!-- Optional: UI screenshots, CLI output, workflow examples -->
