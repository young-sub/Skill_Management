#!/usr/bin/env python3
"""Audit deterministic packaging rules for the work-packet skill."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "SKILL.md",
    "REFERENCE.md",
    "modes/init.md",
    "modes/ready.md",
    "modes/issue.md",
    "modes/run.md",
    "modes/pr.md",
    "modes/close.md",
    "modes/next.md",
    "modes/publish.md",
    "modes/auto.md",
    "scripts/read-reference-section.py",
    "templates/agent-env.template.md",
    "templates/korean-summary.md",
    "templates/local-work-packet.md",
    "templates/implementation-confirmation.md",
    "templates/grill-decision-map.md",
    "templates/issue-body.md",
    "templates/pr-body.md",
    "templates/codex-goal.md",
    "templates/close-report.md",
    "templates/issue-close-capsule.md",
]

KOREAN_SUMMARY_TEMPLATES = [
    "templates/korean-summary.md",
    "templates/local-work-packet.md",
    "templates/issue-body.md",
    "templates/pr-body.md",
    "templates/close-report.md",
]

MOJIBAKE_MARKERS = [
    "\ufffd",
    "\uf9de",
    "\uf9cf",
    "\u79fb\ub304",
    "?\uc493",
    "?\ub4ed",
    "?\uafa9",
    "??\u4ee5",
    "\u00c3",
    "\u00c2",
]

FORBIDDEN_BRANCH_EXAMPLES = [
    "wp/<",
    "issue/<",
    "wp/{",
    "issue/{",
    "origin/main",
    "Final default-branch refresh policy",
    "final default-branch refresh",
]

REQUIRED_TEXT = [
    "Approval needed to export/create PR:",
    "wp-<work-packet-id>-<slug>",
    "issue-<issue-number>-<slug>",
    "Final active-branch refresh policy",
    "Stay on the current branch by default",
    "Codex sandboxed environments",
    "git pull --ff-only",
    "--no-auto-merge",
    "--confirmed",
    "needs-confirmation",
    "Implementation Confirmation Brief",
    "Implementation Contract",
    "Scoped Overrides",
    "Proposed Shared Doc Updates",
    "Decision Map",
    "present a compact Decision Map before every direct grill/preflight question",
    "Decision Map may be written in Korean",
    "For `targeted_grill`, present a compact Decision Map",
    "Progress: [category n/m, question z of estimated x-y]",
    "Question intent:",
    "Recommended answer:",
    "parallel-safe init",
    "branchless ideation",
    "If GitHub Issues are configured",
    "parent issue",
    "local Work Packet seed",
    "Do not satisfy `issue` mode by writing only to `.scratch/` when GitHub Issues are configured",
    "docs_grill_preflight",
    "full_grill_with_docs",
    "Intent confidence",
    "Ask one question at a time",
    "variable-length compact, executive-readable Korean brief",
    "business/review decision first",
    "business meaning before technical identifiers",
    "explain unavoidable technical terms",
    "implementation impact",
    "Full Grill Decision Tree Protocol",
    "decision branches",
    "Do not use bullet lists",
    "must not introduce facts",
    "### 핵심 구현 결과",
    "TBD: fill after implementation is complete",
    "Phase handoff capsule",
    "capsule is an index, not a conclusion",
    "scripts/read-reference-section.py",
    "Model routing policy",
    "Quality preservation outranks fast/small model use",
    "Model class",
    "Allowed model use",
    "Forbidden decisions",
    "Direct Fix Lane",
    "workflow gates",
    "verification policy",
    "git diff --stat",
    "metadata-first, body-once, capsule-only",
    "Metadata-first Tracker I/O",
    "Durable Body Ownership",
    "Right-sized Grill Routing",
    "published_body_ref",
    "grill_route",
    "grill_route_reason",
    "short closure capsule",
    "issue-close-capsule.md",
    "no ready issue found",
    "full-grill bias",
    "delegate command execution by default",
    # Upgrade invariants: tool-neutral access path, local-doc mode, publish, base reflection
    "Access path resolution",
    "agent-env.<slug>.md",
    "Owner gate",
    "tracker_publish_state",
    "git_publish_state",
    "local_pending",
    "handoff_pending",
    "mcp_pat",
    "never performs live tracker writes",
    "Base reflection and protected-branch policy",
    "git push/pull over SSH",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter_ok(text: str) -> bool:
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---\n", 4)
    if end == -1:
        return False
    body = text[4:end]
    return all(re.search(rf"^{key}:\s*.+$", body, re.M) for key in ["name", "description"])


def code_fences_balanced(text: str) -> bool:
    return text.count("```") % 2 == 0


def korean_summary_shape_errors(rel: str, text: str) -> list[str]:
    heading = "## Korean Summary (non-normative)"
    disclaimer = "> This Korean summary is for review speed only."
    if heading not in text:
        return [f"{rel} missing Korean Summary heading"]
    start = text.index(heading)
    try:
        end = text.index(disclaimer, start)
    except ValueError:
        return [f"{rel} missing Korean Summary disclaimer"]
    section = text[start:end]
    errors: list[str] = []
    if "### 목적" not in section:
        errors.append(f"{rel} Korean Summary missing purpose subheading")
    if "### 핵심 구현 사항" not in section:
        errors.append(f"{rel} Korean Summary missing core implementation subheading")
    if rel == "templates/pr-body.md":
        if "### 핵심 구현 결과" not in section:
            errors.append(f"{rel} Korean Summary missing implementation result subheading")
        if "TBD: fill after implementation is complete" not in section:
            errors.append(f"{rel} Korean Summary missing draft implementation placeholder")
    if re.search(r"(?m)^- ", section):
        errors.append(f"{rel} Korean Summary uses bullet-list shape")
    return errors


def mojibake_scan_paths() -> list[Path]:
    paths = list((ROOT / "templates").glob("*.md"))
    paths.extend([
        ROOT / "REFERENCE.md",
        ROOT / "scripts" / "audit-work-packet-skill.py",
    ])
    return paths


def mojibake_errors() -> list[str]:
    errors: list[str] = []
    for path in mojibake_scan_paths():
        text = read(path)
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                errors.append(f"mojibake marker {marker!r} found in {path.relative_to(ROOT)}")
                break
    return errors


def mode_read_order_errors() -> list[str]:
    errors: list[str] = []
    modes = list((ROOT / "modes").glob("*.md"))
    for mode in modes:
        text = read(mode)
        if "scripts/read-reference-section.py" not in text:
            errors.append(f"{mode.relative_to(ROOT)} does not use read-reference-section.py")
        for line in text.splitlines():
            if (
                re.search(r"(?i)^\d+\.\s+Read .*`REFERENCE\.md`", line)
                and "escalation, not default" not in line
                and "Do not read `REFERENCE.md`" not in line
            ):
                errors.append(f"{mode.relative_to(ROOT)} appears to default to raw REFERENCE.md reads")
                break
    for rel in ["modes/pr.md", "modes/close.md", "modes/next.md"]:
        text = read(ROOT / rel)
        for required in ["Phase handoff capsule", "git status --short", "escalation, not default"]:
            if required not in text:
                errors.append(f"{rel} missing read-order text: {required}")
    for rel in ["modes/pr.md", "modes/close.md"]:
        if "git diff --stat" not in read(ROOT / rel):
            errors.append(f"{rel} missing git diff --stat read order")
    for rel in ["modes/ready.md", "modes/issue.md", "modes/pr.md", "modes/close.md", "modes/next.md"]:
        text = read(ROOT / rel)
        if "Metadata-first Tracker I/O" not in text and "metadata-first" not in text:
            errors.append(f"{rel} missing metadata-first tracker I/O hook")
    for rel in ["modes/issue.md", "modes/pr.md"]:
        text = read(ROOT / rel)
        if "body file" not in text and "body-file" not in text:
            errors.append(f"{rel} missing body-file publishing guidance")
    for rel in ["modes/init.md", "modes/auto.md"]:
        text = read(ROOT / rel)
        if "Right-sized Grill Routing" not in text:
            errors.append(f"{rel} missing right-sized grill routing hook")
        if "skill-maintenance" not in text or "full_grill_with_docs" not in text:
            errors.append(f"{rel} missing process/skill-maintenance full-grill bias guidance")
    verification_text = read(ROOT / "REFERENCE.md")
    run_text = read(ROOT / "modes/run.md")
    if "delegate command execution by default" not in verification_text or "verification locally only" not in verification_text:
        errors.append("REFERENCE.md missing default verification delegation guidance")
    if "delegate exact command execution by default" not in run_text:
        errors.append("modes/run.md missing default delegated test execution guidance")
    close_text = read(ROOT / "modes/close.md")
    if "owner surface" not in close_text and "owner-surface" not in close_text:
        errors.append("modes/close.md missing owner-surface persistence guidance")
    if "Link secondary surfaces instead of duplicating full close reports" not in close_text:
        errors.append("modes/close.md missing close-report de-duplication guidance")
    for rel in ["modes/issue.md", "modes/pr.md", "modes/close.md", "modes/next.md"]:
        text = read(ROOT / rel)
        if re.search(r"fetch the full (issue|pr) body", text, re.I) and "Do not" not in text and "Never" not in text:
            errors.append(f"{rel} appears to allow full body fetch by default")
    return errors


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    skill_path = ROOT / "SKILL.md"
    if skill_path.exists():
        skill_text = read(skill_path)
        if not frontmatter_ok(skill_text):
            errors.append("SKILL.md frontmatter is invalid or incomplete")
        line_count = len(skill_text.splitlines())
        if line_count > 100:
            errors.append(f"SKILL.md has {line_count} lines; expected <= 100")

    all_text = "\n".join(read(p) for p in ROOT.rglob("*.md"))
    for stale in ["1-2 Korean lines", "5-7 Korean prose lines"]:
        if stale in all_text:
            errors.append(f"stale fixed-length summary policy found: {stale}")
    for branch_example in FORBIDDEN_BRANCH_EXAMPLES:
        if branch_example in all_text:
            errors.append(f"forbidden slash-style branch example found: {branch_example}")
    for required in REQUIRED_TEXT:
        if required not in all_text:
            errors.append(f"required text missing: {required}")

    for path in ROOT.rglob("*.md"):
        if not code_fences_balanced(read(path)):
            errors.append(f"unbalanced code fences: {path.relative_to(ROOT)}")

    for rel in KOREAN_SUMMARY_TEMPLATES:
        path = ROOT / rel
        if path.exists():
            errors.extend(korean_summary_shape_errors(rel, read(path)))

    errors.extend(mojibake_errors())
    errors.extend(mode_read_order_errors())

    if errors:
        print("Audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
