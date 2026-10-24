---
name: humanize-korean
description: AI(ChatGPT·Claude·Gemini)가 쓴 한글 텍스트를 사람이 쓴 글처럼 진단·윤문·검증한다. 원본 im-not-ai의 Codex 스킬을 처음 사용할 때 받아 최신으로 유지하며 light·standard·heavy 경로를 그대로 실행한다. "AI 티 없애줘", "AI 윤문", "사람이 쓴 것처럼", "번역투 고쳐", "정밀 모드", "2차 윤문", "이 문단만 다시", "humanize Korean" 요청에 사용한다. 단순 맞춤법 교정, 번역, 사실이나 내용을 추가하는 재작성에는 사용하지 않는다.
---

# Humanize Korean — upstream launcher

This skill contains no rewriting rules of its own. It runs the upstream
[im-not-ai](https://github.com/epoko77-ai/im-not-ai) Codex skill from a copy kept
under `CODEX_HOME/vendor/im-not-ai/`.

1. Run the sync script beside this file, with `python` (or `python3` where `python`
   is absent):

   ```
   python "<directory of this SKILL.md>/scripts/sync_upstream.py"
   ```

   Add `--refresh` when the user asks for the latest upstream version. The first run
   and about one run a day need network access to github.com. When the sandbox
   blocks it, request approval to rerun the same command with network access.
2. The script prints one JSON object. If the exit code is not 0, report its
   `message` to the user with the fix (install Git, allow network access, or remove
   the named directory) and stop. Do not rewrite the text from memory instead.
   A `stale` status means the copy is usable but could not be refreshed; mention
   `message` once and continue.
3. Read `<skill_root>/SKILL.md` in full and follow it for the user's request.
   `skill_root` is that skill's real directory, so use it as its `SKILL_ROOT`.
