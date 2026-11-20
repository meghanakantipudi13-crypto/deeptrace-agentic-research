# GitHub Workflow

## Repository target

Repository: `https://github.com/meghanakantipudi13-crypto/deeptrace-agentic-research.git`.

The repository is configured as `origin`, and `main` is the release branch. Authentication uses Git Credential Manager/browser sign-in; credentials and tokens are never stored in tracked files.

## Synchronization commands

```text
git remote -v
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
