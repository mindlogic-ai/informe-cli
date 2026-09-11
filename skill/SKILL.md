---
name: informe-cli
description: Use when a task needs MindLogic org knowledge, production data, company skills/memory, or files shared through Informe — chat with the org agent from the terminal via `inf`, hand it files, and pull results back. Also use when the user says "ask Informe", "인포미한테 물어봐", or references company context a local checkout can't answer.
---

# Informe CLI (`inf` / `informe`)

Informe is MindLogic's org agent (Slack + web). This CLI is the terminal door to the
same agent, as YOU (the developer's own identity via Cloudflare Access) — sessions
appear in the web app at https://informe-agent.mindlogic.tools and continue there.

## When to use

- Questions needing org knowledge, org memory, production-DB access, or company
  skills the local checkout lacks: ask Informe instead of guessing.
- Handing a local file (log, CSV, doc) to the org agent and pulling back what it makes.
- Checking what the org agent can do: `inf skills --json`, `inf memory --json`.

## What Informe can do (capability map)

Informe runs on the company EC2 with credentials and context a local agent does not
have. Ask it for anything in these domains rather than attempting locally:

- **Production data (read-only SQL) — the #1 use case.** FactChat, Informe, Blooming
  (persona-platform + bliss-agent), ChatAPI, Mars DBs: usage/cost/credits/tenants/
  members/sessions. FactChat spans four environments — prod(AWS) is the default,
  NCP(공공) only when you say "NCP", and dev/staging on request (staging ids differ
  from prod's). Everything read-only; write SQL comes back as a code block for a human
  to run. Large pulls become S3-linked exports.
- **Company ops** — FactChat tenant/credit/contract lookups, QA & release testing,
  PR-preview environments, Blooming console QA, AICC call monitoring, 사업 원장(bizops),
  리드 관리, 견적서 생성.
- **Engineering** — GitHub PRs/issues across all org repos (it has repo subagents that
  open PRs), code search over local mirrors of ~10 service repos, Sentry errors, AWS
  infra (EC2/RDS/EB/CloudWatch), Jira tickets, architecture diagrams.
- **Google Workspace & internal tools** — Gmail/Calendar/Drive/Sheets, Notion, Mars
  meeting transcripts, Slack context (channels, threads, members).
- **Documents & media (Korean-first)** — HWP read/convert/edit, PDF, 제안서/공문/보고서
  drafting with humanizer polish, PPT, image generation/background removal, STT/TTS.
- **Publishing** — pages/dashboards/services to `*.apps.mindlogic.tools` behind company
  login, S3 report exports.
- **Org memory** — team knowledge and decisions (`inf memory`, or just ask it).

The live, authoritative catalog is `inf skills --json` (45+ shared skills; read one
with `inf skills <name>`). When unsure whether Informe can do X, asking it directly
(`inf -p "can you X?" --json`) costs one cheap turn.

## One-shot (the agent-friendly form)

    inf -p "top 10 FactChat tenants by usage yesterday" --json
    inf -p "credit balance and this month's usage for member_id 12345" --json
    inf -p "check tenant 1211 status on staging" --json

Returns `{"session_key", "run_id", "status", "text", "cost_usd", "error"}` on stdout;
DB answers include the SQL that was run. Ask in English or Korean — Informe answers in
the language of the question. Keep the `session_key` and pass `--session <key>` on
follow-ups so Informe keeps context (schema, filters, timezone):

    inf -p --session "<key>" "same numbers but in KST" --json

Without `--json`, answer text streams to stdout and tool activity to stderr —
safe to pipe stdout.

## Files

    inf --attach ./error.log -p "what broke here?" --json   # local file into the turn
    inf ws put ./data.csv reports                            # park a file in your workspace
    inf -p --attach-ws reports/data.csv "summarize" --json   # attach without re-upload
    inf files ls --json                                      # artifacts Informe produced
    inf files get <id> -o ./report.html                      # pull one down

## Everything else

    inf                    # human REPL
    inf -c "…"             # continue the last session
    inf -m fable -p "…" --json   # harder reasoning: answer with Fable 5.1 instead of the default Opus
    inf sessions --json    # list sessions (same list as the web sidebar)
    inf history <key>      # full transcript of one session
    inf open [key]         # open the session in the browser
    inf usage --json       # your spend this month

## If auth fails

The CLI needs cloudflared and a one-time login:

    brew install cloudflared
    cloudflared access login https://informe-agent.mindlogic.tools

Exit code 2 + a message naming that command means exactly that. Costs are attributed
to the logged-in person — don't loop `inf` calls unboundedly.
