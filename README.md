# agentic-coding marketplace

설치 전용 브랜치입니다. `main`의 marketplace 목록과 `plugins/`만 담습니다. 직접 수정하지 않고, `main`에서
`python scripts/publish_plugin_branch.py --push`로 다시 만듭니다. 소스와 문서는 `main` 브랜치에 있습니다.

```powershell
# Codex
codex plugin marketplace add young-sub/Skill_Management@plugin
codex plugin add agentic-coding@agentic-coding

# Claude Code
claude plugin marketplace add young-sub/Skill_Management#plugin
claude plugin install agentic-coding@agentic-coding
```
