# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**English** | [한국어](CLAUDE.ko.md)

## Project Status

Planning stage, no source code yet. jobHunter is a personal job-search automation tool: Python scripts run by GitHub Actions cron collect postings from community job-list GitHub repos (SimplifyJobs JSON, Francklin9999/canada-internship markdown; JSearch API is an optional, off-by-default extra), store them in a Notion database (which doubles as the UI), and send Discord webhook alerts. The repo is public as a portfolio, and a read-only static job board (`site/`, GitHub Pages) is built from collected postings only. Never let Notion data (application status, notes) flow into anything published. See `plan.md` for the architecture, `checklist.md` for progress, and `context-notes.md` for the reasoning behind each decision (each has a Korean `.ko.md` twin; see §12). Once the project is scaffolded, add the commands (build, lint, test, running a single test) here.

## Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. No Closing Colons (Korean Output)

**End Korean sentences with a period, not a colon.**

When the user writes in Korean, your output is also Korean:
- Don't end sentences with `:` even if the next line is a list or example.
- LLMs trained on English docs leak the colon habit into Korean. Catch it.
- The test: every Korean sentence terminator should be `.`, `?`, or `!` — not `:`.
- Colons are fine inside code, key-value pairs, or labels. Not as sentence enders.

## 6. File Header Comments (Korean + English)

**First lines of every new source file: a one-line Korean comment stating its role, followed by the same in English.**

When creating a new file:
- TypeScript/JavaScript:
  ```ts
  // 사용자 인증 상태를 관리하는 Context Provider
  // Context provider that manages user auth state
  ```
- Python:
  ```python
  # KIS API 호출을 비동기로 래핑하는 클라이언트
  # Client that wraps KIS API calls asynchronously
  ```
- SQL: `-- 일별 집계 결과를 저장하는 머티리얼라이즈드 뷰` / `-- Materialized view storing daily aggregates`
- Place it directly under required directives (`'use client'`, `'use server'`, shebang).
- Skip config files (`*.config.ts`, `package.json`, etc.).
- All other comments, identifiers, and docstrings are in English.

Why: agents read files selectively, not whole codebases. A one-line header gives instant context so the next session (human or agent) can navigate without re-reading the entire file. The repo is a public portfolio, so English readers need it too (see §12).

## 7. Plan + Checklist + Context Notes

**Before any non-trivial task, produce three artifacts. Don't start coding without them.**

- **Plan** — what we're building and why.
- **Checklist** (`checklist.md`) — concrete tasks as checkboxes. Tick as you go.
- **Context Notes** (`context-notes.md`) — decisions made during the work and the reasoning behind them. Append continuously.

If the user gives only a plan and asks you to start coding, stop and ask: "Should I create the checklist and context notes first?" The next session — yours or someone else's — needs the notes to pick up where you left off without re-deriving every decision.

## 8. Run Tests Before Marking Complete

**If you touched code, run the tests before saying "done".**

- `npm test`, `pytest`, `cargo test`, whatever the project uses — run it.
- If tests pass, report results. If they fail, fix and re-run.
- No test setup? At minimum, verify the project builds/compiles.
- Run tests proactively, before the user signals "끝", "완료", "다 됐어" — not after.

This is the step LLMs skip most often. Treat it as non-negotiable.

## 9. Semantic Commits

**Commit when one logical change is complete. Don't wait for the user to ask.**

- The test: "Can I describe this commit in one sentence?" If yes, commit. If no, the changes are still mixed — split them.
- Good: "auth 미들웨어 추가". Bad: "auth 추가하고 UI도 고치고 버그도 수정" (split into 3).
- Don't accumulate 20 unrelated edits and lose the ability to roll back individually.
- Don't commit just to commit — meaningful units only.

Note: For solo prototypes or throwaway scripts, group commits loosely if it slows you down. The point is reversibility, not ceremony.

## 10. Read Errors, Don't Guess

**Read the actual error/log line. Don't pattern-match from memory.**

When something fails:
- Read the full error message and stack trace.
- Check the actual log output, not what you assume it should say.
- Don't apply a "common fix" before confirming the cause.
- If unclear, add a print/log to verify state — then fix.

This is the step LLMs skip most often after "run tests". They guess from error keywords and apply the most-recent-pattern fix. That's how a one-line bug becomes a three-file refactor.

## 11. Agent Team Rules

**Applies to every teammate in an agent team, and to the lead when running one.**

- **No broadcast.** Never send a message to all teammates at once. Message only the specific teammate (or the lead) who needs it.
- **Shut down immediately when done.** Once your assigned task is finished and reported to the lead, end your session. Don't idle, don't pick up unassigned work.
- **Plan approval before any change.** Before creating, editing, or deleting any file, or running a command that changes state (install, git, etc.), send your plan to the lead with `SendMessage`: files you'll touch, what changes, how you'll verify. Then wait. Start only after the lead replies with approval; if rejected, revise and resend. Read-only exploration needs no approval. (Claude Code's built-in plan-mode approval can auto-approve without the lead reviewing, so this message-based gate is the one that counts.)
- **Stay in your lane.** Edit only the files assigned to you. If you need a change in someone else's file, ask the lead.
- **3-iteration limit.** Any loop (plan revision after rejection, fix → test → fix, retrying a failing step) runs at most 3 times. After the 3rd failed attempt, stop and report to the lead what was tried and what's blocking, instead of trying again.

## 12. Bilingual Docs (English + Korean)

**Every document pushed to GitHub exists in English and Korean, as a pair of files.**

- `X.md` is English (the default GitHub renders); `X.ko.md` is the Korean version. Example: `README.md` / `README.ko.md`, `plan.md` / `plan.ko.md`.
- Right below the title of each file is a language switch: `**English** | [한국어](X.ko.md)` in the English file, `[English](X.md) | **한국어**` in the Korean one.
- **Update both files in the same change.** Never edit one without the other; a commit that touches only one side of a pair is incomplete. This includes ticking boxes in `checklist.md` / `checklist.ko.md` and appending to `context-notes.md` / `context-notes.ko.md`.
- Exception: this `CLAUDE.md` is the English source of truth that Claude Code loads. `CLAUDE.ko.md` is a translation for humans; keep it in sync, but if they ever disagree, `CLAUDE.md` wins.
- Code is not duplicated: see §6 for comments.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
