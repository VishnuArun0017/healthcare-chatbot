from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def compute_id(path: Path, root: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    return relative.as_posix().lower().replace("/", "-")


def _replace_id_line(front_raw: str, new_id: str) -> str | None:
    lines = front_raw.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("id:"):
            current_value = stripped[len("id:") :].strip()
            if current_value == new_id:
                return None
            prefix = line[: line.index("i")]
            lines[idx] = f"{prefix}id: {new_id}"
            return "\n".join(lines).strip("\n")
    return None


def normalise_frontmatter(path: Path, root: Path, dry_run: bool = False) -> bool:
    """Return True if file updated."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False

    parts = text.split("---", 2)
    if len(parts) < 3:
        return False

    front_raw = parts[1]
    body = parts[2].lstrip("\n")

    new_id = compute_id(path, root)

    try:
        data = yaml.safe_load(front_raw) or {}
    except yaml.YAMLError:
        front_replaced = _replace_id_line(front_raw, new_id)
        if front_replaced is None:
            return False
        if front_replaced is not None and not dry_run:
            path.write_text(f"---\n{front_replaced}\n---\n\n{body}", encoding="utf-8")
            return True
        return front_replaced is not None

    if data.get("id") == new_id:
        return False

    data["id"] = new_id
    front_dump = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
    ).strip()

    if not dry_run:
        path.write_text(f"---\n{front_dump}\n---\n\n{body}", encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalise id field in markdown frontmatter."
    )
    parser.add_argument(
        "--root",
        default="api/rag/data",
        help="Root directory containing markdown files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show files that would change without modifying them.",
    )
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    if not root_path.is_dir():
        raise SystemExit(f"Root path {root_path} does not exist.")

    updated = 0
    for md_path in sorted(root_path.rglob("*.md")):
        if normalise_frontmatter(md_path, root_path, dry_run=args.dry_run):
            updated += 1
            print(f"Updated id -> {md_path.relative_to(root_path)}")

    suffix = " (dry run)" if args.dry_run else ""
    print(f"Total files updated: {updated}{suffix}")


if __name__ == "__main__":
    main()

