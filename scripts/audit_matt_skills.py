"""Repository audit entrypoint for the Matt Pocock skill adoption contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from urllib.parse import unquote


REQUIRED_TARGET_SKILLS = frozenset(
    {
        "ask-matt",
        "code-review",
        "codebase-design",
        "diagnosing-bugs",
        "domain-modeling",
        "grilling",
        "implement",
        "research",
        "resolving-merge-conflicts",
        "to-spec",
        "to-tickets",
        "update-matt-skills",
        "wayfinder",
        "writing-great-skills",
    }
)
LEGACY_ACTIVE_SKILLS = frozenset({"diagnose", "to-issues", "to-prd", "write-a-skill"})
TEXT_SUFFIXES = frozenset({".md", ".yaml", ".yml", ".json"})


@dataclass
class AuditReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def audit_repository(root: Path) -> AuditReport:
    """Audit public skill-package behavior under *root*.

    The initial seam is intentionally minimal; TDD cycles add contract checks one at a time.
    """

    report = AuditReport()
    skills_root = root / "skills"
    for name in sorted(REQUIRED_TARGET_SKILLS):
        skill_file = skills_root / name / "SKILL.md"
        if not skill_file.is_file():
            report.errors.append(f"missing required target skill: skills/{name}/SKILL.md")
    for name in sorted(LEGACY_ACTIVE_SKILLS):
        if (skills_root / name / "SKILL.md").is_file():
            report.errors.append(f"legacy active skill must be removed: skills/{name}")
    if skills_root.is_dir():
        declared_paths: dict[str, list[str]] = {}
        for skill_file in sorted(skills_root.glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*[\"']?([^\"'\r\n]+)[\"']?\s*$", text)
            declared_name = match.group(1).strip() if match else "<missing>"
            folder_name = skill_file.parent.name
            declared_paths.setdefault(declared_name, []).append(folder_name)
            if declared_name != folder_name:
                report.errors.append(
                    f"skill name mismatch: folder {folder_name!r} declares {declared_name!r}"
                )
            if re.search(r"(?m)^disable-model-invocation:\s*true\s*$", text):
                codex_policy = skill_file.parent / "agents" / "openai.yaml"
                policy_text = (
                    codex_policy.read_text(encoding="utf-8") if codex_policy.is_file() else ""
                )
                if not re.search(
                    r"(?m)^\s*allow_implicit_invocation:\s*false\s*$", policy_text
                ):
                    report.errors.append(
                        f"missing Codex explicit-only policy for skill {folder_name!r}: "
                        f"agents/openai.yaml must set allow_implicit_invocation: false"
                    )
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                target = target.strip().split()[0].strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if relative.lower() in {"link", "path", "url", "target"}:
                    continue
                if relative and not (skill_file.parent / relative).exists():
                    report.errors.append(
                        f"missing linked resource from skills/{folder_name}/SKILL.md: {relative}"
                    )
        for declared_name, folders in sorted(declared_paths.items()):
            if declared_name != "<missing>" and len(folders) > 1:
                report.errors.append(
                    f"duplicate skill name {declared_name!r}: {', '.join(folders)}"
                )
        upstreams = root / "UPSTREAMS.md"
        if upstreams.is_file():
            ownership_text = upstreams.read_text(encoding="utf-8")
            classified = {
                match.group(1)
                for match in re.finditer(
                    r"(?m)^\|\s*`([^`]+)`\s*\|\s*(?:upstream-derived|local-adapted|local-owned)\s*\|",
                    ownership_text,
                )
            }
            for skill_file in sorted(skills_root.glob("*/SKILL.md")):
                name = skill_file.parent.name
                if name not in classified:
                    report.errors.append(
                        f"active skill {name!r} is missing an ownership classification in UPSTREAMS.md"
                    )
        for name, artifact in (("to-spec", "spec.md"), ("to-tickets", "tickets.md")):
            skill_file = skills_root / name / "SKILL.md"
            if not skill_file.is_file():
                continue
            text = skill_file.read_text(encoding="utf-8")
            required_tokens = (
                "docs/agents/issue-tracker.md",
                "local_markdown",
                "docs/plans/",
                artifact,
                "gitignored",
                "remote",
            )
            if any(token not in text for token in required_tokens):
                report.errors.append(
                    f"skill {name!r} is missing its local_markdown publish contract "
                    f"for durable {artifact} without remote tracker operations"
                )
    gitignore = root / ".gitignore"
    if gitignore.is_file():
        ignore_text = gitignore.read_text(encoding="utf-8")
        if not re.search(r"(?m)^/docs/plans/\s*$", ignore_text):
            report.errors.append(
                "the entire docs/plans tree must be gitignored with /docs/plans/"
            )

    route_contract = {
        "init.md": ("diagnosing-bugs", "grill-with-docs", "domain-modeling", "prototype", "research", "improve-codebase-architecture", "codebase-design", "to-spec"),
        "ready.md": ("to-tickets",),
        "run.md": ("/goal", "tdd", "diagnosing-bugs"),
        "close.md": ("code-review", "improve-codebase-architecture"),
    }
    modes_root = skills_root / "work-packet" / "modes"
    if modes_root.is_dir():
        for filename, tokens in route_contract.items():
            path = modes_root / filename
            mode_text = path.read_text(encoding="utf-8") if path.is_file() else ""
            for token in tokens:
                if token not in mode_text:
                    report.errors.append(
                        f"missing Work Packet route {token!r} in skills/work-packet/modes/{filename}"
                    )
    active_files: list[Path] = []
    for active_root in (skills_root, root / "docs" / "agents"):
        if active_root.is_dir():
            active_files.extend(
                path
                for path in active_root.rglob("*")
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
            )
    active_files.extend(
        path for path in (root / "AGENTS.md", root / "CLAUDE.md", root / "README.md") if path.is_file()
    )
    for path in sorted(set(active_files)):
        text = path.read_text(encoding="utf-8")
        for name in sorted(LEGACY_ACTIVE_SKILLS):
            patterns = (
                rf"`{re.escape(name)}`",
                rf"(?<![\w-])/{re.escape(name)}(?![\w-])",
                rf"\${re.escape(name)}(?![\w-])",
                rf"skills[\\/]{re.escape(name)}(?![\w-])",
            )
            if any(re.search(pattern, text) for pattern in patterns):
                relative = path.relative_to(root).as_posix()
                report.errors.append(
                    f"legacy active reference {name!r} in {relative}"
                )
    return report


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
    report = audit_repository(root)
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")
    if report.errors:
        print(f"Matt skill audit failed: {len(report.errors)} error(s)")
        return 1
    print("Matt skill audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
