# Context Notes

**English** | [한국어](context-notes.ko.md)

Decisions made during the work, and why, in chronological order.

## 2026-11-09 — Initial Plan

- **Use an aggregator API instead of scraping directly.** (Later replaced by GitHub job lists as the primary source; see "Switching sources to GitHub job lists" below.) LinkedIn's terms forbid scraping and it blocks aggressively. Indeed shut down its public search API and blocks crawlers often. JSearch is built on Google for Jobs and includes postings from both.
- **Single user (me).** No auth or multi-tenancy, which shrinks scope considerably.
- **Notion DB as the UI instead of a separate web app.** The user's suggestion. Notion already provides lists, filters, board views, and notes, so only a backend script is needed.
- **Alerts via Discord webhook.** The user's choice. Notion's own notifications are hard to trigger externally.
- **Run on GitHub Actions cron.** Free, no server, Secrets for credentials.
- **Python.** Script-oriented work; API and LLM integration is simple.
- **MVP scope is collection + alerts.** Application tracking and resume writing are deferred to phases 2 and 3.
- **Deduplicate on `Job ID` in the Notion DB.** No separate state file, so nothing needs to be shared between Actions runs.
- **No code integration with Meta Muse (personal AI agent).** The "muse" the user mentioned is Meta's consumer agent Muse. It has no API for pushing messages in, so it can't be an alert channel. But Muse has a Notion connector, so keeping data in Notion lets Muse read and work with it at no extra cost. This reinforces Notion as the single store. As of 2026-11, sources disagree on connector support, so it needs checking in the actual app.

## 2026-11-09 — Search Criteria

- **Two tracks: Intern and New Grad (New Grad / Associate / Junior) SWE.** Queries are per track and the Notion `Track` property distinguishes them. Canada often calls internships "Co-op", so that term is included.
- **Countries are split into regions.** The user wanted the USA kept separate. Each region has its own Notion DB and Discord webhook so they never mix, and adding the USA is a config change only.
- **USA collection is also off (`enabled: false`).** The user said "alerts for Canada only" but didn't say whether to pre-collect US postings without alerts. The default turns collection off too, to save JSearch quota. Setting `enabled: true, notify: false` collects without alerting.
- **No remote filter.** The user said it doesn't matter.
- **Exclude senior-and-above postings by title keyword.** Aggregator experience filters alone may be inaccurate, so filter twice.

## 2026-11-09 — Switching Sources to GitHub Job Lists

The user shared four job-list files across these repos. Verified directly:

- **SimplifyJobs** (New-Grad-Positions, Summer2027-Internships) has structured data in `.github/scripts/listings.json`. Default branch is `dev`, updated several times a day. At the time of checking, active postings were about 3,200 new grad (about 150 in Canada) and about 5,300 intern (about 450 in Canada). Non-dev roles (Hardware, Quant, Product, etc.) are mixed in, so `category` must be filtered. There's no country field; country is inferred from `locations` strings ("Toronto, ON, Canada", "Remote in Canada", "SF").
- **Francklin9999/canada-internship** is Canada-only and has only Markdown tables. Default branch is `master`. Row format: `| company | title (may be prefixed with NEW) | location | notes | posted<br><sub>..</sub> | <a href=URL>Apply</a> | <!--id:0--> |`. The id comments are all 0 and unusable, so the URL is the key. There's also a per-company summary table at the top, so only the posting tables inside the "Tech" sections should be parsed. It's a small repo (~16 stars) and could stop at any time.

Decisions:

- **The MVP uses these GitHub lists as sources.** Free, no keys or quotas, no terms-of-service issues. They're already curated for students and new grads, so quality is likely better than JSearch search results. This also removes RapidAPI signup from MVP setup.
- **JSearch stays as an optional source (off by default).** It can fill gaps in the GitHub lists or replace them if they stop.
- **`Job ID` is the normalized URL.** ID schemes differ between sources. The same posting may appear in both Simplify and canada-internship, so company + title is also used for merging.

## 2026-11-09 — Portfolio Visibility

- **Public scope is the code and a public job board.** The user's choice. Outsiders can only read.
- **Application status is not public.** Having the companies and stages applied to visible to other recruiters could hurt. Board data comes from collection results, not Notion, which structurally prevents personal fields from leaking.
- **The board is a static GitHub Pages page.** No server or cost, and it deploys in the same Actions run. Plain HTML and JS with no build tooling keeps maintenance light. A framework can be considered later if the web UI grows.
- **Pages uses artifact deployment.** Committing data would pile up bot commits twice a day and clutter the portfolio repo's history.
- **None of the three source repos declares a license** (verified via the GitHub API). Credit sources, show only a filtered subset with links, and allow dropping any source from the board.
- **Secrets stay safe in a public repo.** All secrets live only in GitHub Secrets and the local `.env`; config holds only environment variable names.

## 2026-11-09 — git Setup

- **Planning docs (plan, checklist, context-notes, CLAUDE.md) are public.** The user's decision. The design process itself becomes part of the portfolio.
- **Commit email is set to the GitHub noreply address for this repo only** (`87403433+AndyChoi4495@users.noreply.github.com`), so the personal Gmail from the global config doesn't end up in public history. The global git config was left untouched.

## 2026-11-09 — Bilingual Docs

- **Every document pushed to GitHub has both an English and a Korean version.** The user's request.
- **Separate files rather than both languages in one file:** `X.md` is English and `X.ko.md` is Korean, with a language switch link at the top of each. This is the common GitHub convention, and each file stays readable.
- **English is the default (`X.md`).** The portfolio audience is mainly Canadian recruiters, and GitHub renders `README.md` by default.
- **Code:** identifiers and comments are in English; only the first-line role comment is two lines, Korean + English (CLAUDE.md §6).
- **`CLAUDE.md` stays English as the source of truth that Claude Code loads; `CLAUDE.ko.md` is a translation for people.**

## 2026-11-09 — Agent Team Setup

- **Agent teams enabled per project** via `.claude/settings.json` (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`). Teams are set up only at session start, so Claude Code must be restarted.
- **Split panes via tmux.** The user is on Apple Terminal, which has no native split-pane support for teams, so tmux 3.8 was installed with Homebrew and `teammateMode: "tmux"` was set in the user settings. `~/.tmux.conf` enables the mouse, highlights the active pane border in green, shows each pane's number and title on its top border, and uses a green status bar showing the active pane.
- **Plan approval is message-based.** Per the docs, when a teammate spawned in plan mode finishes planning, Claude Code approves the plan automatically without the lead reviewing it. To get a real review, teammates must send their plan to the lead and wait for an explicit approval (CLAUDE.md §11).
- **Four Sonnet teammates with disjoint file ownership** (see plan.md "Agent Team"). Docs and commits stay with the lead to avoid conflicts and keep the bilingual pairs in sync.

## 2026-11-09 — Scaffold

- **Python 3.9 floor** (`requires-python >=3.9`), because the local interpreter is 3.9.6. Modules use `from __future__ import annotations` and `Optional`/`List` instead of `X | Y`/`list[str]` where evaluated at runtime. CI runs on 3.11; ruff targets py39.
- **`Job` gets a `country` field** (lowercase ISO code) that isn't in the Notion table. Simplify lists span many countries, so the filter needs a per-job country to match a region's `country`.
- **`Track`/`Source` are `str` enums whose values equal the config keys.** Display labels (Intern / New Grad, Simplify / CanadaInternship / JSearch) are mapped by the Notion and board code, not the model.
- **Dates, not datetimes**, for `posted` and `collected`: Notion Date and the board only need the day.
- **`requests` is a dependency from the start**, since sources, Notion, and Discord all make HTTP calls.
- **Local setup needs a newer pip:** the system pip 21.2.4 can't do editable installs from pyproject, so upgrade pip inside `.venv` first.

## 2026-11-09 — Sources, Filter, Dedupe

- **Default branches are not `main`:** SimplifyJobs repos use `dev`, canada-internship uses `master`. Stored as `BRANCH` constants in each source module.
- **Country is classified per Simplify location string** (Canada checked first: "Canada", "CAN", province codes; US: state codes, SF/NYC/LA, bare state names, "United States"). "CA" alone means California, not Canada. A listing spanning both countries becomes one `Job` per country; listings with no CA/US location are dropped.
- **canada-internship parsing** takes only table rows with an `<a href=` link inside the Tech section, unescapes HTML, and drops the "NEW " prefix. A format change yields 0 rows rather than an exception, and main.py warns on 0 rows.
- **Excluded keywords match on word boundaries** (`re.escape`, case-insensitive), so "senior" doesn't hit "seniority" and "sr." matches literally.
- **Dedupe merges on equal `job_id` or equal company + title + country**, first occurrence wins (Simplify is passed first since it has a category). canada-internship links are mostly LinkedIn, so cross-source merging relies mainly on company + title.
- **First real-data dry run (2026-11-09):** Simplify 5361 rows, canada-internship 645 rows → 842 Canada postings after filter and dedupe.

## 2026-11-09 — Notion, Discord, main, collect.yml

- **Notion API via plain `requests`, pinned to `Notion-Version: 2022-06-28`.** Newer versions (2025-09-03+) move databases to "data sources"; Notion says old versions stay supported, and the old `/databases/{id}/query` endpoint is the one we could confirm. Revisit if it's ever deprecated.
- **Throttle ~0.35 s between Notion requests, retry once on 429** using `Retry-After`.
- **Each source is fetched once per run, not per region.** A fetch error is logged, counts as 0 rows (Discord warning), and makes `main()` return 1.
- **The Pages deploy only runs when `main` exits 0**, so a partial board never replaces the live one.
- **`DRY_RUN=1`** fetches and builds the board but skips all Notion and Discord calls, so it runs with no secrets. Local `.env` isn't auto-loaded (no extra dependency); export vars in the shell.
- **Cron at 11:17 and 23:17 UTC**, off the hour to avoid Actions congestion.
- **JSearch isn't implemented yet**; enabling it in config only logs a line.
- Code-complete with mocked tests; the "local run" and Actions items stay open until a real run against Notion and Discord.

## Open Questions

- Phase 3 (tailored resumes): automate with the Claude API, or leave it manual by having Muse read the Notion page and write it? Not decided.
- Whether to narrow Canada down to specific cities (Toronto, Vancouver, etc.). Currently all of Canada.
