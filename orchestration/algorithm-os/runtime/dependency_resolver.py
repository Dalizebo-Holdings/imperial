from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import csv


class DependencyResolverError(ValueError):
    pass


def load_dependency_graph(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def resolve_dependencies(
    rows: list[dict[str, str]],
    requested_capability_ids: list[str],
) -> dict:
    canonical_edges: dict[str, list[str]] = defaultdict(list)
    platform_prerequisites: dict[str, list[str]] = defaultdict(list)
    external_prerequisites: dict[str, list[str]] = defaultdict(list)
    known_ids: set[str] = set()

    for row in rows:
        source = row["source_id"]
        known_ids.add(source)
        kind = row["dependency_kind"]

        if kind == "CANONICAL_OS":
            target = row["target_id"]
            if target:
                known_ids.add(target)
                if target not in canonical_edges[source]:
                    canonical_edges[source].append(target)
        elif kind == "PLATFORM_PRIMITIVE":
            value = row["dependency_raw"]
            if value not in platform_prerequisites[source]:
                platform_prerequisites[source].append(value)
        elif kind == "EXTERNAL_DEPENDENCY":
            value = row["dependency_raw"]
            if value not in external_prerequisites[source]:
                external_prerequisites[source].append(value)
        else:
            raise DependencyResolverError(
                f"Unknown dependency kind: {kind}"
            )

    requested = [
        item.removeprefix("OS-").zfill(3)
        for item in requested_capability_ids
    ]

    missing = [cid for cid in requested if cid not in known_ids]
    if missing:
        raise DependencyResolverError(
            "Unknown canonical capabilities: "
            + ", ".join(f"OS-{cid}" for cid in missing)
        )

    ordered: list[str] = []
    permanent: set[str] = set()
    temporary: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if node in permanent:
            return

        if node in temporary:
            try:
                start = stack.index(node)
                cycle = stack[start:] + [node]
            except ValueError:
                cycle = [node, node]
            if cycle not in cycles:
                cycles.append(cycle)
            return

        temporary.add(node)
        stack.append(node)

        for dependency in canonical_edges.get(node, []):
            visit(dependency)

        stack.pop()
        temporary.remove(node)
        permanent.add(node)

        if node not in ordered:
            ordered.append(node)

    for cid in requested:
        visit(cid)

    closure = set(ordered)

    return {
        "requested_capabilities": [f"OS-{cid}" for cid in requested],
        "ordered_canonical_capabilities": [f"OS-{cid}" for cid in ordered],
        "platform_prerequisites": {
            f"OS-{cid}": platform_prerequisites[cid]
            for cid in sorted(closure)
            if platform_prerequisites.get(cid)
        },
        "external_prerequisites": {
            f"OS-{cid}": external_prerequisites[cid]
            for cid in sorted(closure)
            if external_prerequisites.get(cid)
        },
        "cycles": [
            [f"OS-{cid}" for cid in cycle]
            for cycle in cycles
        ],
    }
