# Algorithm OS Dependency Resolver

## Purpose

The Dependency Resolver converts capability dependency declarations into a machine-readable graph for Algorithm OS planning.

## Dependency Classes

### CANONICAL_OS
A dependency resolves directly to one of OS-001 through OS-269.

### PLATFORM_PRIMITIVE
A dependency refers to a platform capability not represented by a canonical OS name in the current catalogue.

### EXTERNAL_DEPENDENCY
A dependency requires an external provider, licensed data source, regulated service, or other explicitly integrated external system.

## Resolution Rules

1. Canonical dependencies resolve by normalized canonical name.
2. Algorithm OS must not invent canonical IDs for unresolved names.
3. External and platform prerequisites remain explicit plan requirements.
4. Cycles are detected and returned to the planner; they are never silently flattened.
5. Duplicate canonical dependencies are deduplicated.
6. The resolver does not execute dependencies.
7. Final execution still requires Pillars OS and Kernel authorization.

## Runtime Output

- requested capability IDs
- ordered canonical capability IDs
- external prerequisites
- platform prerequisites
- detected cycles
