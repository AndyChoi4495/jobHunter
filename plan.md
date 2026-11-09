# jobHunter Plan

**English** | [한국어](plan.ko.md)

## Goals

Build a personal (single-user) job-search automation tool.

1. Collect job postings (LinkedIn, Indeed, and others)
2. Alert on new postings
3. Track application status
4. Tailor resumes and cover letters per posting

## Key Decisions

| Area | Decision |
|---|---|
| Users | Just me (no login) |
| Language | Python |
| Job collection | Community job-list GitHub repos (SimplifyJobs, canada-internship) first. JSearch aggregator API as an optional extra source |
| Storage & UI | Notion database |
| Alerts | Discord webhook |
| Runtime | GitHub Actions cron |
| MVP | Collection + alerts |
| Roles | Software developer, two tracks: Intern (incl. Co-op) and New Grad (New Grad / Associate / Junior) |
| Countries | Run per region. Canada active; USA configured but disabled |
| Remote | Doesn't matter (not filtered) |
| Portfolio | Public GitHub repo + read-only public job board (GitHub Pages). Application status stays private in Notion |

The reasoning behind each decision is in `context-notes.md`.

## Architecture

```
GitHub Actions (cron)
   └─ main.py
        1. Load config.yaml
        2. For each enabled region
           a. Collect postings per track (intern / new grad) from enabled sources (sources/*)
           b. filter.py → region (country), category, required role keyword, excluded-keyword filters
           c. Merge cross-source duplicates (by URL, company + title)
           d. notion_store.py → fetch existing Job IDs from the region's Notion DB, add only new postings
           e. If notify is true, notify_discord.py → send a summary to the region's Discord webhook
        3. Active postings of regions with publish: true → board.py → site/jobs.json
   └─ actions/deploy-pages → deploy site/ to GitHub Pages
```

- Deduplication uses the `Job ID` property in the Notion DB. No separate state file.
- `Job ID` is the normalized application URL, because each source has its own ID scheme and canada-internship has no usable ID. When the same posting appears in several sources, it is merged if the URL matches or company + title match.

### Public Job Board (Portfolio)

- **What's public:** all the code, plus the filtered list of collected postings. Each posting shows company, title, location, track, posted date, source, and application link.
- **What's private:** personal data such as application status, notes, and tailored resumes. That lives only in Notion, and the board never reads Notion. Because board data is built only from collection results, there is no path for personal data to leak into it by accident.
- **Form:** a single static HTML + JS page with no build tooling. Track, city, and source filters, search, and a "new in the last 7 days" badge.
- **Deployment:** every Actions run deploys `site/` as a Pages artifact. No data is committed to the repo, so git history stays clean.
- **Attribution:** original sources are credited and linked on the board and in the README. None of the three source repos declares a license.
- **Outsiders can only read.** Only the owner can push to a public repo, and PRs from forks can't access Secrets. Repo settings will require approval before Actions run on outside PRs.

### Portfolio Quality

- README covers the problem, an architecture diagram, the board link and screenshots, and how to run it.
- CI (tests + lint) on every PR and push, with a badge.
- Type hints and per-source parser tests (using saved sample data).

### Regions

- Each region gets **its own Notion DB and Discord webhook**, so Canadian and US postings never mix.
- `enabled` (collect) and `notify` (alert) are toggled per region.
- To add the USA: create a US Notion DB and webhook, register the Secrets, then set `enabled: true` and `notify: true`. No code changes.

### config.yaml (draft)

```yaml
sources:
  simplify:
    enabled: true
    new_grad_repo: SimplifyJobs/New-Grad-Positions
    intern_repo: SimplifyJobs/Summer2027-Internships   # update when the season rolls over
    categories: [Software, Software Engineering, AI/ML/Data]
  canada_internship:
    enabled: true            # applies to the Canada region only
  jsearch:
    enabled: false

tracks:
  intern:
    queries:                 # JSearch only
      - software developer intern
      - software engineer intern
      - software developer co-op
  new_grad:
    queries:
      - new grad software engineer
      - junior software developer
      - associate software engineer
      - entry level software developer

exclude_title_keywords: [senior, sr., staff, principal, lead, manager, director]

regions:
  canada:
    country: ca
    enabled: true
    notify: true
    publish: true            # include in the public board
    notion_db_env: NOTION_DB_CANADA
    discord_webhook_env: DISCORD_WEBHOOK_CANADA
  usa:
    country: us
    enabled: false
    notify: false
    publish: false
    notion_db_env: NOTION_DB_USA
    discord_webhook_env: DISCORD_WEBHOOK_USA
```

- Secrets never go in config; only environment variable names do.
- The query lists are drafts, to be tuned against real results.
- JSearch parameter names for country, date posted, employment type (INTERN), and experience requirements will be confirmed against the API docs at implementation time.

### Sources

| Source | Format | Scope | Track | Notes |
|---|---|---|---|---|
| [SimplifyJobs/New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) | `.github/scripts/listings.json` (JSON) | Worldwide | New Grad | Structured data. Fields `active`, `is_visible`, `category`, `locations`, `date_posted` (unix) |
| [SimplifyJobs/Summer2027-Internships](https://github.com/SimplifyJobs/Summer2027-Internships) | Same JSON | Worldwide | Intern | Adds a `terms` field. Repo name includes the year, so it changes every season |
| [Francklin9999/canada-internship](https://github.com/Francklin9999/canada-internship) `INTERNSHIPS.md` | Markdown table | Canada only | Intern | Only the "Tech internships" section. Links are mostly LinkedIn |
| Same repo, `NEW_GRAD.md` | Markdown table | Canada only | New Grad | Only the "Tech new-grad roles" section |
| JSearch API (optional) | REST JSON | Per country | By query | Off by default. Fills gaps the lists above miss |

- Everything is fetched from `raw.githubusercontent.com`. No API keys or quotas.
- From the Simplify lists, keep only `category` Software / AI/ML/Data, and determine the country from `locations`.
- canada-internship is human-oriented Markdown, so the parser can break if the format changes. If parsing yields 0 rows, send a warning instead of an alert.
- Meta Muse reads the same DB through its own Notion connector, as a helper for searching, summarizing, and writing. No code integration.
- Sources live as separate modules under `sources/` so new ones are easy to add.

### Directory Layout (draft)

```
jobHunter/
├─ config.yaml              # search keywords, regions, exclusions
├─ src/jobhunter/
│  ├─ main.py
│  ├─ config.py
│  ├─ models.py             # Job dataclass
│  ├─ filter.py
│  ├─ sources/
│  │  ├─ simplify.py        # SimplifyJobs listings.json
│  │  ├─ canada_internship.py  # Francklin9999 Markdown tables
│  │  └─ jsearch.py         # optional
│  ├─ dedupe.py
│  ├─ notion_store.py
│  ├─ notify_discord.py
│  └─ board.py              # builds jobs.json for the public board
├─ site/                    # public board (index.html, app.js, style.css)
├─ tests/
│  └─ fixtures/             # sample data per source
└─ .github/workflows/
   ├─ collect.yml           # cron: collect → Notion → Discord → Pages deploy
   └─ ci.yml                # PR / push: tests + lint
```

### Notion DB Properties (draft)

| Property | Type | Notes |
|---|---|---|
| Title | Title | Job title |
| Company | Text | |
| Location | Text | |
| Remote | Checkbox | |
| Track | Select | Intern / New Grad |
| Source | Select | Simplify / CanadaInternship / JSearch |
| Category | Select | Software / AI/ML/Data, etc. (Simplify's) |
| Link | URL | Application link |
| Job ID | Text | Dedup key |
| Posted | Date | |
| Collected | Date | |
| Status | Select | From phase 2. New → Interested → Applied → Screening → Interview → Result |

### Secrets (GitHub Secrets)

- `JSEARCH_API_KEY` (RapidAPI, only if JSearch is enabled)
- `NOTION_TOKEN`
- `NOTION_DB_CANADA`, `DISCORD_WEBHOOK_CANADA`
- `NOTION_DB_USA`, `DISCORD_WEBHOOK_USA` (when the USA is enabled)
- `ANTHROPIC_API_KEY` (from phase 3)

Locally these live in `.env`, which is never committed.

## Agent Team (Phase 1 build)

The lead (main session) coordinates; every teammate runs on **Sonnet** and must get plan approval before changing anything (CLAUDE.md §11).

| Teammate | Owns (only these files) | Starts after |
|---|---|---|
| `scaffold` | `pyproject.toml`, `config.yaml`, `src/jobhunter/{__init__,config,models}.py`, `tests/test_config.py`, `.github/workflows/ci.yml` | — (first) |
| `sources` | `src/jobhunter/sources/{simplify,canada_internship}.py`, `filter.py`, `dedupe.py`, matching tests and `tests/fixtures/` | scaffold |
| `integrations` | `src/jobhunter/{notion_store,notify_discord,main}.py`, matching tests, `.github/workflows/collect.yml` | scaffold |
| `board` | `src/jobhunter/board.py`, `site/`, matching tests | scaffold |

- The lead alone edits `plan*.md`, `checklist*.md`, `context-notes*.md`, `CLAUDE*.md`, and makes commits.
- `scaffold` fixes the `Job` model and config shape first, so the other three can work in parallel without touching shared files.
- Split-pane display via tmux: start `tmux`, then run `claude` inside it (`teammateMode: "tmux"` in user settings).

## Phases

### Phase 1 — MVP: Collection + Alerts
New matching postings land in Notion once or twice a day, and a summary arrives on Discord.

### Phase 2 — Application Tracking
Track application stages with the Notion `Status` property. Send deadline and follow-up reminders to Discord.

### Phase 3 — Tailored Resumes & Cover Letters
Keep a base resume; when a posting is selected, generate a tailored version with the Claude API and save it to that Notion page.

## Risks

- **Redistributing data on the public board:** the source repos have no license. Credit sources, link to the originals, and show only a filtered subset rather than republishing the raw files. Keep a per-source flag to drop a source from the board if its maintainers object.
- **Dependence on GitHub lists:** community-maintained repos may stop updating or change format; canada-internship in particular is a small personal repo. Log per-source counts to spot problems quickly.
- **Intern repo season rollover:** Simplify creates a new intern repo per year (e.g. `Summer2027`). The repo name in config must be updated each season.
- **JSearch free quota** (if enabled): monthly requests are capped. Requests ≈ `queries × active regions × runs per day × 30`. Canada alone with 7 queries × 2 runs/day is about 420/month. Size queries and schedule to the quota, and remember enabling the USA doubles it.
- **Posting quality:** aggregator APIs can miss postings or lag behind the originals.
- **Notion API rate limit:** about 3 requests/second, so space out bulk inserts.
- **GitHub Actions cron:** runs in UTC and can be delayed by several minutes.
