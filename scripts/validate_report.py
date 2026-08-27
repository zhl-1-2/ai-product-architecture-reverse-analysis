#!/usr/bin/env python3
"""Validate a final single-file AI product architecture report."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path


REQUIRED_SECTIONS = [
    "executive-summary", "scope-gaps", "evidence-index", "user-journey",
    "functional-domains", "agent-contracts", "tools-context-dataflow",
    "end-to-end-flows", "layered-architecture", "knowledge-assets",
    "model-routing", "technology-options", "data-entities-er",
    "state-sequence", "panorama", "as-is-to-be",
    "risks-traceability", "unknowns",
]
LEVELS = {"all", "confirmed", "inferred", "suggested", "unknown"}


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.sections: list[str] = []
        self.section_text: dict[str, list[str]] = {}
        self.current_section: str | None = None
        self.copy_targets: list[str] = []
        self.download_targets: list[str] = []
        self.diagram_sources: list[str] = []
        self.diagram_renders: list[str] = []
        self.filters: set[str] = set()
        self.export_targets: list[str] = []
        self.evidence_ids: set[str] = set()
        self.evidence_links: set[str] = set()
        self.has_search = False
        self.has_print_button = False
        self.has_aria_live = False
        self.has_csp = False
        self.has_charset = False
        self.has_viewport = False
        self.has_lang = False
        self.has_title = False
        self.in_title = False
        self.table_count = 0
        self.table_header_count = 0
        self.form_actions: list[str] = []

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = self.attrs_dict(attrs)
        element_id = data.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)

        if tag == "html" and data.get("lang", "").lower() == "zh-cn":
            self.has_lang = True
        if tag == "meta":
            if data.get("charset", "").lower() == "utf-8":
                self.has_charset = True
            if data.get("name", "").lower() == "viewport":
                self.has_viewport = True
            if data.get("http-equiv", "").lower() == "content-security-policy":
                self.has_csp = True
        if tag == "title":
            self.in_title = True
        if tag == "section":
            section_id = element_id
            self.current_section = section_id
            if section_id:
                self.sections.append(section_id)
                self.section_text.setdefault(section_id, [])

        if data.get("data-diagram-type") == "mermaid" and element_id:
            self.diagram_sources.append(element_id)
        if "data-diagram-id" in data:
            self.diagram_renders.append(data["data-diagram-id"])
        if "data-copy-target" in data:
            self.copy_targets.append(data["data-copy-target"])
        if "data-download-target" in data:
            self.download_targets.append(data["data-download-target"])
        if "data-filter" in data:
            self.filters.add(data["data-filter"])
        if "data-export-table" in data:
            self.export_targets.append(data["data-export-table"])
        if "data-evidence-id" in data:
            self.evidence_ids.add(data["data-evidence-id"])
        if tag == "a" and data.get("href", "").startswith("#evidence-"):
            self.evidence_links.add(data["href"][1:])
        if tag == "input" and data.get("type", "").lower() == "search":
            self.has_search = True
        if element_id == "print-report" or data.get("data-action") == "print":
            self.has_print_button = True
        if "aria-live" in data:
            self.has_aria_live = True
        if tag == "table":
            self.table_count += 1
        if tag == "th":
            self.table_header_count += 1
        if tag == "form" and data.get("action"):
            self.form_actions.append(data["action"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "section":
            self.current_section = None

    def handle_data(self, data: str) -> None:
        if self.in_title and data.strip():
            self.has_title = True
        if self.current_section and data.strip():
            self.section_text[self.current_section].append(data.strip())


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"无法以 UTF-8 读取文件：{exc}"], warnings

    parser = ReportParser()
    try:
        parser.feed(raw)
    except Exception as exc:  # HTMLParser failures should still be reported clearly.
        errors.append(f"HTML 解析失败：{exc}")
        return errors, warnings

    if not raw.lstrip().lower().startswith("<!doctype html>"):
        errors.append("缺少 <!doctype html>。")
    for ok, message in [
        (parser.has_lang, "<html> 缺少 lang=\"zh-CN\"。"),
        (parser.has_charset, "缺少 UTF-8 charset。"),
        (parser.has_viewport, "缺少 viewport meta。"),
        (parser.has_csp, "缺少 Content-Security-Policy。"),
        (parser.has_title, "缺少非空 <title>。"),
        (parser.has_search, "缺少全局搜索框。"),
        (parser.has_print_button, "缺少打印 / 另存 PDF 按钮。"),
        (parser.has_aria_live, "缺少 aria-live 交互反馈区。"),
    ]:
        if not ok:
            errors.append(message)

    missing_sections = [section for section in REQUIRED_SECTIONS if section not in parser.sections]
    if missing_sections:
        errors.append("缺少必备章节：" + ", ".join(missing_sections))
    section_positions = [parser.sections.index(s) for s in REQUIRED_SECTIONS if s in parser.sections]
    if section_positions != sorted(section_positions):
        errors.append("18 个必备章节顺序不符合报告契约。")
    for section in REQUIRED_SECTIONS:
        if section in parser.section_text:
            text = " ".join(parser.section_text[section])
            if len(text) < 40:
                errors.append(f"章节 {section} 内容过少，可能仍是空章节。")

    placeholder_patterns = [r"\{\{[^{}]+\}\}", r"\bPLACEHOLDER\b", r"\bTODO\b", r"\[待填[^\]]*\]"]
    if any(re.search(pattern, raw, re.IGNORECASE) for pattern in placeholder_patterns):
        errors.append("报告中仍存在未替换占位符。")

    if parser.duplicate_ids:
        errors.append("存在重复 HTML id：" + ", ".join(sorted(parser.duplicate_ids)))
    if len(parser.diagram_sources) < 4:
        errors.append("完整报告至少需要 4 张带可见源码的 Mermaid 图。")
    for source_id in parser.diagram_sources:
        if source_id not in parser.copy_targets:
            errors.append(f"Mermaid 源码 {source_id} 缺少复制按钮。")
        if source_id not in parser.download_targets:
            errors.append(f"Mermaid 源码 {source_id} 缺少 .mmd 下载按钮。")
        diagram_id = source_id.removesuffix("-source")
        if diagram_id not in parser.diagram_renders:
            errors.append(f"Mermaid 源码 {source_id} 缺少对应渲染容器。")
    for target in parser.copy_targets + parser.download_targets:
        if target not in parser.ids:
            errors.append(f"交互按钮指向不存在的目标：{target}")

    missing_levels = LEVELS - parser.filters
    if missing_levels:
        errors.append("证据筛选不完整，缺少：" + ", ".join(sorted(missing_levels)))
    if not parser.evidence_ids:
        errors.append("缺少 data-evidence-id 证据记录。")
    if not parser.evidence_links:
        errors.append("缺少指向 #evidence-* 的证据深链接。")
    for link in parser.evidence_links:
        if link not in parser.ids:
            errors.append(f"证据深链接指向不存在的 ID：{link}")
    if not parser.export_targets:
        errors.append("缺少关键表格 CSV 导出按钮。")
    for target in parser.export_targets:
        if target not in parser.ids:
            errors.append(f"CSV 导出按钮指向不存在的表格：{target}")
    if parser.table_count and not parser.table_header_count:
        errors.append("表格存在但没有 <th> 表头。")
    if "@media print" not in raw:
        errors.append("缺少 @media print 打印样式。")
    if "window.print" not in raw:
        errors.append("打印按钮未连接 window.print()。")
    if parser.form_actions:
        errors.append("报告不应包含可提交的 form action。")
    if "已确认" not in raw or "合理推断" not in raw or "建议设计" not in raw or "未知" not in raw:
        errors.append("缺少完整的四类证据等级文字图例。")

    if "https://" in raw and "Content-Security-Policy" not in raw:
        warnings.append("报告引用外部 HTTPS 资源，但未找到 CSP。")
    return errors, warnings


def build_self_test_html() -> str:
    evidence_table = "<table id='evidence-table'><tr><th>证据</th></tr><tr id='evidence-E001' data-evidence-id='E001' data-evidence-level='confirmed'><td>E001</td></tr></table>"
    section_parts = []
    for section in REQUIRED_SECTIONS:
        extra = evidence_table if section == "evidence-index" else ""
        section_parts.append(
            f'<section id="{section}"><h2>{section}</h2><p>这是用于校验器自测的完整示例内容，包含足够的结论、证据、解释与限制说明。</p>{extra}</section>'
        )
    sections = "".join(section_parts)
    diagrams = "".join(
        f'<div data-diagram-id="d{i}"></div><pre id="d{i}-source" data-diagram-type="mermaid">flowchart TD; A--&gt;B</pre><button data-copy-target="d{i}-source">复制</button><button data-download-target="d{i}-source">下载</button>'
        for i in range(4)
    )
    filters = "".join(f'<button data-filter="{level}">{level}</button>' for level in sorted(LEVELS))
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src 'self'"><title>校验自测</title><style>@media print{{button{{display:none}}}}</style></head><body><input type="search">{filters}<button id="print-report">打印</button><button data-export-table="evidence-table">导出</button><a href="#evidence-E001">E001</a><p>已确认 合理推断 建议设计 未知</p>{sections}{diagrams}<div aria-live="polite"></div><script>document.getElementById('print-report').onclick=()=>window.print()</script></body></html>'''


def main() -> int:
    argument_parser = argparse.ArgumentParser(description="校验单文件 AI 产品架构报告")
    argument_parser.add_argument("report", nargs="?", type=Path)
    argument_parser.add_argument("--self-test", action="store_true")
    args = argument_parser.parse_args()

    if args.self_test:
        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as handle:
            handle.write(build_self_test_html())
            test_path = Path(handle.name)
        errors, warnings = validate(test_path)
        test_path.unlink(missing_ok=True)
        if errors:
            print("SELF-TEST FAIL")
            for error in errors:
                print(f"  - {error}")
            return 1
        print("SELF-TEST PASS")
        return 0

    if not args.report:
        argument_parser.error("请提供要校验的 HTML 文件，或使用 --self-test。")
    errors, warnings = validate(args.report)
    for warning in warnings:
        print(f"WARN: {warning}")
    if errors:
        print(f"FAIL: {args.report}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS: {args.report}")
    print("已通过结构、章节、证据、图源码、复制/下载、筛选、CSV 导出和打印能力校验。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
