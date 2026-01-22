#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch convert Traditional Chinese -> Simplified Chinese for .md/.json/.yaml/.yml files.

Fix:
- opencc-python-reimplemented expects config name WITHOUT '.json' (e.g. 't2s', 'tw2s').
  This script accepts both 't2s' and 't2s.json' safely.

Features:
- Recursively scans a directory.
- Markdown: avoids converting fenced code blocks ```...``` and inline code `...`.
- JSON: preserves structure; converts only string values (optionally keys too).
- YAML: preserves comments and formatting using ruamel.yaml; converts only string scalars (optionally keys too).
- Creates .bak backups by default.

Dependencies:
  pip install opencc-python-reimplemented ruamel.yaml

Usages:
  py -3.12 scripts/t2s_batch.py output\zhCN\lithium-supply-demand-gap-radar --opencc-config tw2s --no-backup
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Tuple

from opencc import OpenCC
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

SUPPORTED_EXTS = {".md", ".json", ".yaml", ".yml"}

# Markdown: protect code fences and inline code
FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


@dataclass
class Stats:
    scanned: int = 0
    converted: int = 0
    skipped: int = 0
    failed: int = 0


class T2SConverter:
    def __init__(self, config: str = "t2s") -> None:
        """
        opencc-python-reimplemented expects config name WITHOUT '.json':
          - 't2s'  : Traditional -> Simplified
          - 'tw2s' : Taiwan Traditional -> Simplified

        This wrapper accepts both 't2s' and 't2s.json'.
        """
        config = (config or "t2s").strip()
        if config.lower().endswith(".json"):
            config = config[:-5]
        self.cc = OpenCC(config)

    def convert_text(self, s: str) -> str:
        return self.cc.convert(s)

    def convert_markdown_preserve_code(self, text: str) -> str:
        """
        Convert markdown but skip:
          - fenced code blocks ```...```
          - inline code `...`
        """
        placeholders: list[Tuple[str, str]] = []

        def _stash(match: re.Match) -> str:
            key = f"__PLACEHOLDER_{len(placeholders)}__"
            placeholders.append((key, match.group(0)))
            return key

        temp = FENCE_RE.sub(_stash, text)
        temp = INLINE_CODE_RE.sub(_stash, temp)

        converted = self.convert_text(temp)

        for key, original in placeholders:
            converted = converted.replace(key, original)

        return converted

    def convert_json_obj(self, obj: Any, convert_keys: bool = False) -> Any:
        """Convert strings inside JSON object recursively."""
        if isinstance(obj, str):
            return self.convert_text(obj)
        if isinstance(obj, list):
            return [self.convert_json_obj(x, convert_keys=convert_keys) for x in obj]
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                new_k = self.convert_text(k) if (convert_keys and isinstance(k, str)) else k
                new_dict[new_k] = self.convert_json_obj(v, convert_keys=convert_keys)
            return new_dict
        return obj

    def convert_yaml_obj(self, obj: Any, convert_keys: bool = False) -> Any:
        """Convert strings inside YAML (ruamel) structures recursively."""
        if isinstance(obj, str):
            return self.convert_text(obj)

        if isinstance(obj, (CommentedSeq, list)):
            for i in range(len(obj)):
                obj[i] = self.convert_yaml_obj(obj[i], convert_keys=convert_keys)
            return obj

        if isinstance(obj, (CommentedMap, dict)):
            if convert_keys:
                items = list(obj.items())
                obj.clear()
                for k, v in items:
                    new_k = self.convert_text(k) if isinstance(k, str) else k
                    obj[new_k] = self.convert_yaml_obj(v, convert_keys=convert_keys)
            else:
                for k in list(obj.keys()):
                    obj[k] = self.convert_yaml_obj(obj[k], convert_keys=convert_keys)
            return obj

        return obj


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file(path: Path) -> Path:
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak)
    return bak


def iter_files(root: Path, exts: set[str]) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def guess_json_indent(text: str, fallback: int = 2) -> int:
    m = re.search(r"\n( +)\"", text)
    return len(m.group(1)) if m else fallback


def convert_file(
    path: Path,
    conv: T2SConverter,
    dry_run: bool,
    no_backup: bool,
    convert_keys: bool,
    yaml_preserve_quotes: bool,
) -> Tuple[bool, str]:
    """Returns (changed, message)"""
    try:
        suffix = path.suffix.lower()

        if suffix == ".md":
            original = read_text(path)
            converted = conv.convert_markdown_preserve_code(original)

            if converted == original:
                return (False, "no change")

            if not dry_run:
                if not no_backup:
                    backup_file(path)
                write_text(path, converted)
            return (True, "converted markdown")

        if suffix == ".json":
            original_text = read_text(path)
            try:
                data = json.loads(original_text)
            except json.JSONDecodeError as e:
                return (False, f"json parse error: {e}")

            converted_data = conv.convert_json_obj(data, convert_keys=convert_keys)

            indent = guess_json_indent(original_text, fallback=2)
            converted_text = json.dumps(converted_data, ensure_ascii=False, indent=indent)

            # preserve trailing newline
            if original_text.endswith("\n") and not converted_text.endswith("\n"):
                converted_text += "\n"

            if converted_text == original_text:
                return (False, "no change")

            if not dry_run:
                if not no_backup:
                    backup_file(path)
                write_text(path, converted_text)
            return (True, "converted json")

        if suffix in {".yaml", ".yml"}:
            yaml = YAML()
            yaml.preserve_quotes = yaml_preserve_quotes
            yaml.width = 10**9  # reduce auto line-wrapping

            original_text = read_text(path)
            try:
                data = yaml.load(original_text)
            except Exception as e:
                return (False, f"yaml parse error: {e}")

            if data is None:
                return (False, "empty yaml")

            converted_data = conv.convert_yaml_obj(data, convert_keys=convert_keys)

            from io import StringIO

            buf = StringIO()
            yaml.dump(converted_data, buf)
            converted_text = buf.getvalue()

            if original_text.endswith("\n") and not converted_text.endswith("\n"):
                converted_text += "\n"

            if converted_text == original_text:
                return (False, "no change")

            if not dry_run:
                if not no_backup:
                    backup_file(path)
                write_text(path, converted_text)
            return (True, "converted yaml")

        return (False, "unsupported ext")

    except Exception as e:
        return (False, f"failed: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Batch Traditional->Simplified conversion for md/json/yaml files."
    )
    ap.add_argument("root", type=str, help="Root directory to scan")
    ap.add_argument("--dry-run", action="store_true", help="Preview only, do not write files")
    ap.add_argument("--no-backup", action="store_true", help="Do not create .bak backups")
    ap.add_argument("--convert-keys", action="store_true", help="Also convert JSON/YAML keys (default: only values)")
    ap.add_argument(
        "--opencc-config",
        type=str,
        default="t2s",
        help="OpenCC config: t2s or tw2s (you may also pass t2s.json; it will be handled)",
    )
    ap.add_argument("--yaml-preserve-quotes", action="store_true", help="Preserve YAML quotes (recommended)")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root directory not found or not a directory: {root}")

    conv = T2SConverter(config=args.opencc_config)

    stats = Stats()
    for f in iter_files(root, SUPPORTED_EXTS):
        stats.scanned += 1
        changed, msg = convert_file(
            f,
            conv,
            dry_run=args.dry_run,
            no_backup=args.no_backup,
            convert_keys=args.convert_keys,
            yaml_preserve_quotes=args.yaml_preserve_quotes,
        )

        if "failed" in msg or "parse error" in msg:
            stats.failed += 1
            print(f"[FAIL] {f} -> {msg}")
        elif changed:
            stats.converted += 1
            print(f"[OK]   {f} -> {msg}")
        else:
            stats.skipped += 1
            print(f"[SKIP] {f} -> {msg}")

    print("\n--- Summary ---")
    print(f"Scanned:   {stats.scanned}")
    print(f"Converted: {stats.converted}")
    print(f"Skipped:   {stats.skipped}")
    print(f"Failed:    {stats.failed}")
    if args.dry_run:
        print("Dry-run mode: no files were written.")


if __name__ == "__main__":
    main()
