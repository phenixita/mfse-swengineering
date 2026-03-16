---
description: Review the current branch before opening a pull request against main.
name: pre-pr-review
argument-hint: Optional focus area, files, or risks to pay extra attention to.
agent: agent
---

Review the current branch before opening a pull request.

Use these workspace files as context:
- PR template: [../pull_request_template.md](../pull_request_template.md)


Optional extra focus from the user:
- ${input:focus:Optional focus area, files, or risks}

This is a review-only workflow. Do not make code changes unless the user explicitly asks for them.

Tasks:
1. Identify the current branch and compare it against the default branch (usually `main`). If the current branch is already the default branch, or if you cannot determine a meaningful diff, say so clearly.
2. Review the branch diff and changed files that would be part of the pull request. If there are local uncommitted changes, call them out separately.
3. Read the PR template and use it as the opening-time checklist.
4. Review with a code review mindset focused on bugs, regressions, missing tests, behavioral risks, schema or configuration changes, and violations of repository conventions.
5. Explicitly check whether:
  - relevant tests are missing or should be added or updated
  - project-specific build or linting commands should be run before opening the PR
  - relevant unit, integration, or end-to-end tests should be run
  - issue tracker (e.g., Jira, GitHub Issues, ADO) or documentation updates appear required
  - breaking changes, migrations, or configuration changes should be called out in PR notes

Output format:
1. Findings first, ordered by severity, with file references when possible.
2. `PR template readiness` with each checklist item marked as `ready`, `missing`, or `unclear`.
3. `Draft PR summary` using the template headings provided in the repository's PR template.
4. If there are no findings, say that explicitly and list residual risks or unverified areas.
