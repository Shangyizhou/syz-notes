#!/usr/bin/env python3
"""Generate MkDocs navigation from the GitBook SUMMARY and run MkDocs."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "notes"
SUMMARY = DOCS / "SUMMARY.md"
CONFIG = ROOT / "mkdocs.yml"
GENERATED_CONFIG = ROOT / ".mkdocs.generated.yml"
MARKER = "# NAV_FROM_SUMMARY"

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
ITEM = re.compile(r"^(?P<indent> *)[*+-]\s+\[(?P<title>.+?)\]\((?P<target>[^)]+)\)\s*$")


def parse_summary() -> list[dict[str, object]]:
    """Read GitBook's heading and nested-list structure as MkDocs nav."""
    nav: list[dict[str, object]] = []
    current_list = nav
    stack: list[tuple[int, dict[str, object]]] = []
    seen_targets: set[str] = set()

    for line_number, line in enumerate(SUMMARY.read_text(encoding="utf-8").splitlines(), 1):
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            if level == 2:
                title = heading.group(2).strip()
                section: list[object] = []
                nav.append({title: section})
                current_list = section  # type: ignore[assignment]
                stack.clear()
            elif level > 2:
                raise ValueError(f"SUMMARY.md:{line_number}: 目前不支持三级及更深标题")
            continue

        match = ITEM.match(line)
        if not match:
            if line.strip().startswith(("* ", "- ", "+ ")):
                raise ValueError(f"SUMMARY.md:{line_number}: 无法识别目录项：{line.strip()}")
            continue

        indent = len(match.group("indent"))
        if indent % 2:
            raise ValueError(f"SUMMARY.md:{line_number}: 目录缩进应为两个空格的倍数")
        title = match.group("title").strip()
        target = match.group("target").strip()
        if "://" in target or target.startswith(("#", "/")):
            raise ValueError(f"SUMMARY.md:{line_number}: 目录目标必须是 notes/ 下的相对路径：{target}")
        if target in seen_targets:
            raise ValueError(f"SUMMARY.md:{line_number}: 重复目录目标：{target}")
        seen_targets.add(target)

        resolved = (DOCS / target).resolve()
        if DOCS.resolve() not in resolved.parents and resolved != DOCS.resolve():
            raise ValueError(f"SUMMARY.md:{line_number}: 目录目标越出 notes/：{target}")
        if not resolved.is_file():
            raise FileNotFoundError(f"SUMMARY.md:{line_number}: 找不到目录目标：{target}")

        node: dict[str, object] = {"title": title, "target": target, "children": []}
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if indent == 0:
            parent_list = current_list
        else:
            if not stack:
                raise ValueError(f"SUMMARY.md:{line_number}: 找不到缩进层级对应的父目录项")
            previous_indent, parent = stack[-1]
            if indent <= previous_indent:
                raise ValueError(f"SUMMARY.md:{line_number}: 目录层级缩进不正确")
            parent_list = parent["children"]
        parent_list.append(node)  # type: ignore[union-attr]
        stack.append((indent, node))

    return [convert_node(item, depth=0) for item in nav]


def convert_node(item: object, depth: int) -> object:
    """Convert parser nodes to MkDocs' nested title/page structure."""
    if not isinstance(item, dict) or "title" not in item:
        if isinstance(item, dict):
            return {key: [convert_node(child, depth=0) for child in value] for key, value in item.items()}
        return item

    title = str(item["title"])
    target = str(item["target"])
    children = item["children"]
    if children:
        landing_title = "课程首页" if depth == 0 else "章节首页"
        entries = [{landing_title: target}]
        entries.extend(convert_node(child, depth + 1) for child in children)
        return {title: entries}
    return {title: target}


def write_generated_config(nav: list[dict[str, object]]) -> None:
    source = CONFIG.read_text(encoding="utf-8")
    if source.count(MARKER) != 1:
        raise ValueError(f"mkdocs.yml 必须且只能包含一次 {MARKER}")
    generated_nav = yaml.safe_dump(
        {"nav": nav},
        allow_unicode=True,
        sort_keys=False,
        width=120,
    ).rstrip()
    GENERATED_CONFIG.write_text(
        source.replace(MARKER, generated_nav, 1),
        encoding="utf-8",
    )


def main() -> int:
    args = sys.argv[1:] or ["serve"]
    if args[0] not in {"build", "serve", "gh-deploy"}:
        print("用法：python scripts/mkdocs.py [serve|build|gh-deploy] [MkDocs 参数…]", file=sys.stderr)
        return 2
    try:
        nav = parse_summary()
        write_generated_config(nav)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"MkDocs 导航准备失败：{error}", file=sys.stderr)
        return 1

    command = [
        sys.executable,
        "-m",
        "mkdocs",
        *args,
        "--config-file",
        str(GENERATED_CONFIG),
    ]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
