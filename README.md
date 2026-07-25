# Axiom Skills Used

Personal collection of skills used in daily work with Codex, Claude, and other local agent environments.

## Contents

The `skills/` directory contains one copy of each distinct local skill, with supporting references and scripts where available. It is collected from the local Codex, `.agents`, and the formal `.claude/skills` directories.

Identical skills are deduplicated by `SKILL.md` content. When versions share a name but have different content, the alternate version is retained with a source suffix such as `--claude`.

## Security

Local environment files and credentials are intentionally excluded. Configure any required API keys in your own local environment before using a skill.

## Updating this repository

Copy updated skill folders into `skills/`, review the changes, and commit them. Do not commit `.env` files, tokens, or other credentials.
