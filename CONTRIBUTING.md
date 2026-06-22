# Contributing to claude-skills

Thanks for your interest in contributing. This repo follows the [Agent Skills](https://agentskills.io) open standard, so any skill you add here will work across Claude Code, Cursor, Windsurf, Aider, and more.

---

## Reporting issues

Found a pattern Chameleon misses? A language or framework it misclassifies?

Open an issue and include:
- The project type / language / framework
- What Chameleon produced
- What it should have produced instead (ideally with a small code snippet as evidence)

---

## Adding a new skill

1. Fork the repo and create a branch: `git checkout -b skill/your-skill-name`
2. Create a folder at the repo root named after your skill (kebab-case):
   ```
   your-skill-name/
   └── SKILL.md
   ```
3. Write your `SKILL.md` following the [Agent Skills spec](https://agentskills.io). At minimum:
   ```markdown
   ---
   name: your-skill-name
   description: >
     One or two sentences. Be specific about when this should trigger.
   ---
   # Your Skill Title
   ...instructions...
   ```
4. Test it locally:
   ```bash
   npx openskills install ./your-skill-name
   npx openskills sync
   # then open Claude Code and try trigger phrases
   ```
5. Add an entry to the root `README.md` under the **Skills** section.
6. Open a PR with a short description of what the skill does and why it's useful.

---

## Improving Chameleon

PRs that improve Chameleon's detection accuracy are very welcome. Good targets:

- New stratum classification patterns (for unusual project layouts)
- Additional design pattern detection rules
- Better handling of a specific language or framework
- Edge cases in the sampling or confidence logic

Please include before/after examples in your PR description.

---

## Code of conduct

Be kind. This is a small open-source project — constructive feedback and patience go a long way.
