# GitHub Workflow

## Repository target

Recommended repository name: `deeptrace-agentic-research`.

No GitHub remote is currently configured. GitHub CLI was not detected during Phase 0, so no repository creation or push is claimed.

## Minimal manual step

After reviewing Phase 0, create an **empty** GitHub repository named `deeptrace-agentic-research` under the desired account. Do not initialize it with a README, `.gitignore`, or license because those exist locally. Then provide the repository HTTPS or SSH URL. The local connection will be:

```text
git remote add origin <repository-url>
git push -u origin main
```

Authentication should use GitHub's supported credential flow; never paste a personal access token into a tracked file or chat transcript.

## Milestone workflow

1. Review `git status` and the diff.
2. Run phase-appropriate tests/checks.
3. Search staged content for credential patterns and inspect suspicious hits manually.
4. Update the compliance tracker and documentation to match reality.
5. Create one meaningful commit for the verified milestone.
6. Push to the configured remote when authenticated.
7. Record the commit and evidence in the process log/evaluation artifacts as appropriate.

Suggested future commit themes are valid only when the described work and tests exist. Do not create activity-only commits.
