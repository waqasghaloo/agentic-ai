# Hooks

Every hook in this project — what event triggers it, what it does, and why it was added.

**Where hooks live:** `.claude/settings.json`

---

## Existing Hooks

### Git Push Permission (Phase 1)
- **Trigger:** Any `git push` command
- **What it does:** Allows `git push` without prompting for permission
- **Why added:** This is a personal project where we commit and push frequently.
  Removing the prompt speeds up the workflow without risk since we only ever
  push to the personal GitHub account.
- **File:** `.claude/settings.local.json`

---

*(More hooks documented here as they are added)*

## Planned Hooks

| Phase | Hook | Trigger | Purpose |
|---|---|---|---|
| Phase 6 | Daily pipeline | Cron schedule | Kick off full video pipeline every day |
| Phase 6 | Error notification | Agent failure | Log and notify when any agent fails |
| Phase 6 | Post-upload | Upload complete | Log success, update video tracker |
