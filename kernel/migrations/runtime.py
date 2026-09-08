from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


class MigrationError(ValueError):
    pass


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    path: Path
    checksum: str
    transactional: bool = True

    def validate(self) -> None:
        if not isinstance(self.version, int) or self.version < 1:
            raise MigrationError(
                "migration version must be an integer >= 1"
            )

        if not re.fullmatch(
            r"[a-z0-9][a-z0-9_-]{2,127}",
            self.name,
        ):
            raise MigrationError(
                f"invalid migration name: {self.name}"
            )

        if not self.path.exists():
            raise MigrationError(
                f"migration file does not exist: {self.path}"
            )

        if not re.fullmatch(r"[a-f0-9]{64}", self.checksum):
            raise MigrationError(
                "migration checksum must be SHA-256 hex"
            )

        if not self.transactional:
            raise MigrationError(
                "Kernel P0 migrations must be transactional"
            )


def checksum_file(path: str | Path) -> str:
    target = Path(path)
    return sha256(target.read_bytes()).hexdigest()


def discover_migrations(
    directory: str | Path,
) -> list[Migration]:
    root = Path(directory)

    if not root.exists():
        raise MigrationError(
            f"migration directory does not exist: {root}"
        )

    migrations: list[Migration] = []

    for path in sorted(root.glob("*.sql")):
        match = re.fullmatch(
            r"(\d{4})_([a-z0-9][a-z0-9_-]+)\.sql",
            path.name,
        )

        if match is None:
            raise MigrationError(
                f"invalid migration filename: {path.name}"
            )

        migration = Migration(
            version=int(match.group(1)),
            name=match.group(2),
            path=path,
            checksum=checksum_file(path),
            transactional=True,
        )
        migration.validate()
        migrations.append(migration)

    if not migrations:
        raise MigrationError(
            "no migration files discovered"
        )

    versions = [item.version for item in migrations]
    names = [item.name for item in migrations]

    if len(versions) != len(set(versions)):
        raise MigrationError(
            "duplicate migration versions detected"
        )

    if len(names) != len(set(names)):
        raise MigrationError(
            "duplicate migration names detected"
        )

    if versions != sorted(versions):
        raise MigrationError(
            "migrations are not ordered by version"
        )

    return migrations


@dataclass(frozen=True)
class AppliedMigration:
    version: int
    name: str
    checksum: str


def plan_migrations(
    *,
    available: list[Migration],
    applied: list[AppliedMigration],
) -> list[Migration]:
    available_by_version = {
        item.version: item
        for item in available
    }

    applied_versions: set[int] = set()

    for record in sorted(applied, key=lambda item: item.version):
        if record.version in applied_versions:
            raise MigrationError(
                f"duplicate applied migration version: {record.version}"
            )

        applied_versions.add(record.version)

        migration = available_by_version.get(record.version)

        if migration is None:
            raise MigrationError(
                f"historical migration missing from source: {record.version}"
            )

        if migration.name != record.name:
            raise MigrationError(
                f"migration name drift detected at version {record.version}"
            )

        if migration.checksum != record.checksum:
            raise MigrationError(
                f"migration checksum drift detected at version {record.version}"
            )

    if applied_versions:
        max_applied = max(applied_versions)
        expected_history = {
            item.version
            for item in available
            if item.version <= max_applied
        }

        if applied_versions != expected_history:
            raise MigrationError(
                "applied migration history contains a gap"
            )

    return [
        item
        for item in available
        if item.version not in applied_versions
    ]
