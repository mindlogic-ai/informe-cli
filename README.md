# informe-cli — Informe in your terminal

    uv tool install "git+https://github.com/mindlogic-ai/mindlogic-claude-agent#subdirectory=cli"
    inf setup                                  # checks cloudflared, installs the Claude Code skill
    inf "어제 팩트챗 테넌트별 사용량 top 10"    # ask; the session also appears at informe-agent.mindlogic.tools

The #1 use case is production data: Informe runs read-only SQL against the FactChat /
Informe / Blooming / ChatAPI / Mars DBs and replies with the SQL it ran. FactChat
covers prod(AWS, default), NCP(공공 — say "NCP"), and dev/staging on request. Writes
are never executed — they come back as SQL for a human to run.

`informe` and `inf` are the same binary. Auth is your own Cloudflare Access login
(`cloudflared access login https://informe-agent.mindlogic.tools`, one time) — every
session, file, and cost is attributed to you, exactly like the web app.

## Commands

    inf "question"              one-shot, streamed (tool activity → stderr)
    inf                         REPL
    inf -c "follow-up"          continue your last session
    inf -p "q" --json           script/agent mode: JSON summary on stdout
    inf --attach f.log "q"      hand a local file to the turn
    inf -m fable "q"            answer with Fable 5.1 (also: sonnet, opus = default); sticks to the chat; REPL: /opus, /fable, /sonnet, /model, /compact
    inf open [key]              open the session in the web app
    inf stop [key]              stop the turn running on a session (default: last)
    inf compact [key]           summarize a heavy session's context, keeping the session
    inf sessions [--search q]   list / search your sessions (with context size)
    inf history <key>           one session's transcript, and its context size
    inf skills [name] [--mine]  what the org agent can do
    inf memory [show <path>]    org memory
    inf usage                   your spend this month
    inf files ls|get            artifacts from chats
    inf ws ls|put|get|mv|rm     your persistent workspace (--project <id> for a project's)
    inf setup                   onboarding: cloudflared check + Claude Code skill

Anything that isn't a subcommand is a chat message (`inf what changed yesterday` works);
quote questions that contain shell metacharacters.

## The Claude Code skill

`inf setup` copies the bundled skill to `~/.claude/skills/informe-cli/SKILL.md` —
user-level, so every Claude Code project on the machine can call Informe as a
sub-agent (with a capability map of what Informe can do plus the live-catalog check
`inf skills --json`).

## Upgrading

    uv tool upgrade informe-cli && inf setup

The first command re-pulls the CLI from git; the second refreshes the installed skill
(the copy does not update itself).

Dev loop: `cd cli && uv run --extra dev pytest`. The CLI is a pure client of
`src/mindlogic_claude_agent/web/api.py` — change them together.
