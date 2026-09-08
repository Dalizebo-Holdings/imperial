#!/usr/bin/env python3

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "source" / "IMPERIAL_ARCHITECT_RAW.md"

if not SOURCE.exists():
    raise SystemExit("Missing source/IMPERIAL_ARCHITECT_RAW.md")

text = SOURCE.read_text(encoding="utf-8")

# --------------------------------------------------
# Extract raw constitutional and OS sections
# --------------------------------------------------

if "## PILLARS" not in text or "## OPERATING SYSTEMS" not in text:
    raise SystemExit("Required source headings not found.")

pillars_section = (
    text.split("## PILLARS", 1)[1]
        .split("## OPERATING SYSTEMS", 1)[0]
        .strip()
)

os_section = (
    text.split("## OPERATING SYSTEMS", 1)[1]
        .split("## INTEGRATIONS", 1)[0]
        .strip()
)

(ROOT / "constitution" / "207_PILLARS_SOURCE.md").write_text(
    "# 207 Pillars — Source Edition\n\n"
    "> Verbatim source extraction. No normalization or implementation approval is implied.\n\n"
    + pillars_section
    + "\n",
    encoding="utf-8",
)

(ROOT / "operating-systems" / "OPERATING_SYSTEMS_SOURCE.md").write_text(
    "# Operating Systems — Source Edition\n\n"
    "> Verbatim source extraction. No normalization or implementation approval is implied.\n\n"
    + os_section
    + "\n",
    encoding="utf-8",
)

# --------------------------------------------------
# Parse 207 Pillars
# --------------------------------------------------

pillar_pattern = re.compile(
    r"Pillar\s+(\d{3})\s+\(([^)]+)\):\s*([^*\n]+)"
)

pillars = pillar_pattern.findall(pillars_section)

pillar_registry = ROOT / "constitution" / "pillar-registry.csv"

with pillar_registry.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "pillar_id",
        "name",
        "source_statement",
        "review_status",
    ])

    for pillar_id, name, statement in pillars:
        writer.writerow([
            pillar_id,
            name.strip(),
            statement.strip(),
            "UNREVIEWED",
        ])

# --------------------------------------------------
# Parse Operating Systems
# --------------------------------------------------

cluster_pattern = re.compile(
    r"CLUSTER\s+([A-Z]):\s*(.+?)\s+\((\d{3})[–-](\d{3})\)"
)

entry_pattern = re.compile(
    r"\*\*\s*(\d+)\.\s*(.+?):\s*(.*?)\*\*"
)

os_entries = []
current_cluster = None
current_start = None
current_end = None

for line in os_section.splitlines():

    cluster = cluster_pattern.search(line)

    if cluster:
        current_cluster = cluster.group(1)
        current_name = cluster.group(2).strip()
        current_start = int(cluster.group(3))
        current_end = int(cluster.group(4))
        continue

    for match in entry_pattern.finditer(line):

        local_id = int(match.group(1))
        name = match.group(2).strip()
        statement = match.group(3).strip()

        declared_id = None

        if current_start is not None:
            candidate = current_start + local_id - 1

            if candidate <= current_end:
                declared_id = f"{candidate:03d}"

        os_entries.append({
            "source_sequence": len(os_entries) + 1,
            "cluster": current_cluster,
            "cluster_name": current_name,
            "local_id": local_id,
            "declared_id": declared_id or "UNRESOLVED",
            "name": name,
            "statement": statement,
        })

registry = ROOT / "operating-systems" / "source-os-registry.csv"

with registry.open("w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow([
        "source_sequence",
        "cluster",
        "cluster_name",
        "local_id",
        "declared_id",
        "name",
        "source_statement",
        "review_status",
    ])

    for entry in os_entries:
        writer.writerow([
            f"{entry['source_sequence']:03d}",
            entry["cluster"],
            entry["cluster_name"],
            entry["local_id"],
            entry["declared_id"],
            entry["name"],
            entry["statement"],
            "UNREVIEWED",
        ])

# --------------------------------------------------
# Source reconciliation audit
# --------------------------------------------------

unresolved = [
    entry for entry in os_entries
    if entry["declared_id"] == "UNRESOLVED"
]

audit = ROOT / "operating-systems" / "SOURCE_AUDIT.md"

lines = [
    "# Imperial Architect Source Audit",
    "",
    "## Detected Counts",
    "",
    f"- Pillars detected: **{len(pillars)}**",
    f"- Raw Operating System entries detected: **{len(os_entries)}**",
    f"- OS entries outside declared cluster ranges: **{len(unresolved)}**",
    "",
    "## Canonical Declarations",
    "",
    "- Source declares 207 Strategic Pillars.",
    "- Source declares Operating Systems index 001–269.",
    "",
]

if unresolved:
    lines.extend([
        "## OS Range Conflict",
        "",
        "The source contains entries that exceed their declared cluster range.",
        "These have not been deleted or renumbered.",
        "",
        "| Source Sequence | Cluster | Local ID | Name |",
        "|---:|---|---:|---|",
    ])

    for entry in unresolved:
        lines.append(
            f"| {entry['source_sequence']:03d} "
            f"| {entry['cluster']} "
            f"| {entry['local_id']} "
            f"| {entry['name']} |"
        )

lines.extend([
    "",
    "## Governance Rule",
    "",
    "Source material is preserved verbatim.",
    "",
    "Canonical IDs, implementation classifications, and any reframing decisions "
    "must be approved separately.",
    "",
])

audit.write_text("\n".join(lines), encoding="utf-8")

# --------------------------------------------------
# Validation
# --------------------------------------------------

print(f"Pillars detected: {len(pillars)}")
print(f"OS entries detected: {len(os_entries)}")
print(f"Unresolved OS IDs: {len(unresolved)}")

if len(pillars) != 207:
    raise SystemExit(
        f"ERROR: expected 207 Pillars, detected {len(pillars)}"
    )

print("OK: Imperial Architect source imported.")
