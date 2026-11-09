# Checklist

**English** | [한국어](checklist.ko.md)

## 0. Setup
- [x] Initialize git repo (noreply email configured)
- [x] Create **public** GitHub repo, first push
- [ ] Repo settings: require approval for Actions on outside-contributor PRs, set Pages source to GitHub Actions
- [x] Python project setup (pyproject.toml, test tooling)
- [x] Add `.env` to `.gitignore`
- [x] Create Notion integration, get token
- [x] Create Canada Notion DB (per the property table in plan.md), share it with the integration
- [x] Create a webhook in the Discord Canada alert channel
- [x] Finalize search criteria (intern / new grad SWE, Canada first, remote doesn't matter)

## 1. MVP — Collection + Alerts
- [x] `config.yaml` schema and loader (tracks, regions, enabled/notify flags)
- [x] Define the `Job` model
- [x] Simplify collector (listings.json → `Job`; active, visible, category, country detection) + tests
- [x] canada-internship collector (parse Markdown tables in the Tech sections) + tests
- [x] Filter (excluded keywords, etc.) + tests
- [x] Cross-source dedup (URL normalization, company + title) + tests
- [x] Discord warning on source anomalies (e.g. 0 rows collected)
- [x] Fetch existing `Job ID`s from Notion
- [x] Add new postings to Notion
- [x] Send Discord summary (skip when there are 0 new postings)
- [x] Wire the whole flow in `main.py`, verify a local run
- [x] GitHub Actions workflow (cron + manual trigger), register Secrets
- [x] Verify a real run on Actions
- [ ] Tune queries and exclusions after 1–2 weeks of use

## 1.5 Portfolio — Public Board
- [x] `board.py`: active postings of publish regions → `site/jobs.json` (no personal fields) + tests
- [x] `site/` static page: list, track / city / source filters, search, "new" badge, source attribution
- [x] Add a Pages deploy step to `collect.yml`
- [x] `ci.yml`: tests + lint
- [x] README: problem, architecture diagram, board link, screenshots, how to run, source attribution, CI badge

## JSearch Extra Source (optional)
- [x] Subscribe to JSearch on RapidAPI, get API key, check free quota (200/month)
- [x] JSearch collector + tests, enable in config
- [x] Register the `JSEARCH_API_KEY` Secret on GitHub
- [ ] Review after 2 weeks (around 2026-11-23): how many JSearch postings were worth applying to? Keep or drop

## USA Expansion (optional)
- [ ] Create US Notion DB and Discord webhook
- [ ] Register `NOTION_DB_USA`, `DISCORD_WEBHOOK_USA` Secrets
- [ ] Set usa `enabled` and `notify` to true in `config.yaml`
- [ ] Verify US location detection in Simplify lists (handle shorthands like `SF`, `NYC`, `San Jose, CA`)

## 2. Application Tracking
- [ ] Decide how to use the Notion `Status` and `Deadline` properties
- [ ] Discord reminders for upcoming deadlines and follow-ups

## 3. Tailored Resumes
- [ ] Decide where the base resume lives
- [ ] Decide the generation trigger (e.g. a Notion checkbox)
- [ ] Generate tailored resume / cover letter with the Claude API and save to the Notion page
