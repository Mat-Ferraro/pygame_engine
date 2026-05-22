**Version:** 2.0-design
**Authority:** Supplements CODING_STANDARDS.md and RESTRICTIONS.md

This document defines what a reviewer is responsible for checking and
what the author is responsible for before requesting review.

---

## Author Checklist — Before Requesting Review

Complete every item before marking a PR ready for review.
Incomplete PRs should not be reviewed — they waste both parties' time.

### Code
- [ ] All tests pass locally (`pytest`)
- [ ] Linter passes locally (`ruff check .`)
- [ ] No new `print()` statements in `pygame_engine/`
- [ ] No inline magic numbers without comments explaining them
- [ ] All TODO comments follow the required format (tag, what, why, reference)

### Tests
- [ ] New engine core features have Tier 1 tests
- [ ] New engine module features have Tier 2 tests
- [ ] New game scenes have at least a smoke test (once SceneTestHarness exists)
- [ ] Any new public API with a postcondition has a test verifying it

### Documentation
- [ ] All new public methods have docstrings (Google style)
- [ ] CHANGELOG.md updated under `[Unreleased]`
- [ ] Relevant doc file updated if public API changed
- [ ] CODEBASE_CHANGES.md updated if a planned change was resolved or a new one identified

### Git
- [ ] Commit messages follow Conventional Commits format
- [ ] No "wip", "fix typo", "asdf" commits in the branch history (squash them)
- [ ] Branch is up to date with `main`

---

## Reviewer Checklist — Blocking Issues

These must be resolved before the PR can merge. If any item fails,
leave a blocking comment explaining what needs to change and why.

### Restrictions (RESTRICTIONS.md)
- [ ] No game-specific concepts added to `pygame_engine/` (R3)
- [ ] No circular imports introduced — check with `python -c "import pygame_engine"` (R2)
- [ ] Dependency direction not violated — lower layers not importing from higher (R4)
- [ ] No new stateful module-level singletons (R9)
- [ ] No `eval()`, `exec()`, or runtime code generation in production paths (R1)
- [ ] No cross-scene imports at module level (R7)
- [ ] No new background threads for game logic (R13)
- [ ] No imports from `editor/` in engine or game code (R14)

### API and Documentation
- [ ] Every new public method has a docstring in Google style
- [ ] Docstrings describe the contract, not the implementation
- [ ] No type annotations restated in docstring Args sections
- [ ] Magic numbers have comments explaining their derivation
- [ ] Workarounds have comments explaining the limitation and the fix reference

### Tests
- [ ] New engine core features have tests
- [ ] Test file named after the system under test (not after a phase or date)
- [ ] Test function names describe the expected behaviour
- [ ] At least one test per documented failure mode (Raises section)

### File Structure
- [ ] No file over 600 lines without a decomposition plan (R17)
- [ ] No file over 400 lines without a comment explaining why decomposition was deferred
- [ ] Imports are in the correct order (stdlib → third-party → engine → game)

### Naming
- [ ] No abbreviations in public identifiers (sw, sh, btn, cb, fn, idx)
- [ ] Boolean attributes use is_, has_, can_, should_ prefix
- [ ] Event names are dot-separated and noun-first

---

## Reviewer Checklist — Non-Blocking Suggestions

These are suggestions. The author decides whether to act on them.
Leave as comments, not blocking changes. Mark them clearly as optional.

- Alternative implementation approaches
- Additional test cases beyond the minimum
- Naming improvements within the allowed rules
- Opportunities to reduce duplication
- Performance observations (without demanding changes)
- Questions about design intent (not blocking — for understanding)

Format non-blocking comments as:
```
nit: consider naming this `subscription_token` rather than `token` for clarity
suggestion: this could be simplified using the existing wrap_text() utility
question: what happens if the scene registry is empty when navigate() is called?
```

The `nit:` / `suggestion:` / `question:` prefix makes it clear these
are not blocking the merge.

---

## What Reviewers Are Not Responsible For

Reviewers are not responsible for:
- Catching every possible bug (that is what tests are for)
- Verifying the feature works correctly end-to-end (that is what the author's testing is for)
- Style preferences not covered by the linter or this document
- Architectural decisions already made in ARCHITECTURE.md

If a reviewer disagrees with an architectural decision in ARCHITECTURE.md,
that conversation happens in the architecture docs — not in a PR comment.
PR comments address the specific code change, not the design philosophy.

---

## Review Response Standards

### For the Author Receiving Review

- **Blocking comment:** acknowledge it and either fix it or explain why
  the reviewer's concern does not apply. Never silently dismiss a
  blocking comment.
- **Non-blocking suggestion:** you decide. A simple "acknowledged, keeping
  as-is because X" closes the conversation cleanly.
- **Question:** always answer. Questions are how reviewers understand
  your intent. If the code requires a question to understand, it
  probably needs a comment.

### For the Reviewer

- Be specific. "This is wrong" is not useful. "This violates R9 because
  it creates module-level state that will be shared between Application
  instances in tests" is useful.
- Distinguish blocking from non-blocking clearly. Authors should never
  have to guess which comments must be resolved.
- Approve when the blocking checklist passes — do not hold a PR for
  non-blocking suggestions.

---

## When Review Is Not Required

Direct commits to `main` without review are permitted only for:
- Single-line documentation fixes (typo, broken link)
- Version number bumps after a release
- Trivial CI configuration fixes (timeout value, environment variable)

If in doubt — branch and review.

---

## Review Turnaround

Reviews should be completed within one working day of being requested.
If you cannot review within that window, say so immediately so the
author knows to find another reviewer.

A PR that sits unreviewed for more than two days with no response is
blocking productive work — this is never acceptable.

---

## When a Review Is Complete

A review is complete when all of the following are true:

- All blocking comments are resolved — either fixed or explicitly
  declined with a justification that the reviewer accepts
- The author has acknowledged every non-blocking comment — acted on
  it, or responded "acknowledged, keeping as-is because X"
- CI passes on the latest commit

**Re-review is required only when:**
- A blocking comment was resolved with a non-trivial code change
- The reviewer explicitly requests it in their approval message

**Re-review is not required for:**
- Trivial fixes (typo correction, adding a missing docstring)
- Non-blocking suggestions the author acted on
- Rebasing onto main with no functional changes

When in doubt, the reviewer who left the blocking comment decides
whether re-review is needed. If they are unavailable, a second
reviewer may approve.

---

## When Reviewers Disagree

When two reviewers leave conflicting blocking comments:

1. The author surfaces the conflict explicitly — do not silently
   pick one and hope the other reviewer does not notice
2. The two reviewers discuss and reach a position
3. If they cannot agree, the decision defers to ARCHITECTURE.md
   — if the architecture document covers the case, it decides
4. If ARCHITECTURE.md does not cover it, the decision is made and
   documented there before the PR merges — this is a signal that
   the architecture document needed updating anyway

Architectural disagreements belong in architecture documents, not in
PR comment threads. A PR thread is not the right venue for relitigating
design decisions.

---

## Definition of "Done" for the Author

A PR is done — ready to merge — when:

- [ ] The reviewer has approved
- [ ] All blocking comments are resolved
- [ ] All non-blocking comments are acknowledged
- [ ] CI passes
- [ ] The branch is up to date with main (rebase, not merge)
- [ ] No commits remain that say "wip", "fixup", or "address review"

The author merges, not the reviewer. The reviewer approves the change.
The author is responsible for the merge and for the branch being clean.

---

## Fixup Commits During Review

When a reviewer requests changes, use fixup commits rather than new
standalone commits:

```bash
# Make the fix
git add -p                           # stage only the fix
git commit --fixup <original-sha>    # create a fixup commit

# Before merge — squash fixups into their parents
git rebase -i --autosquash main
```

**Never** leave `fixup!` commits in the branch history at merge time.
The merged history should look as if the review feedback was incorporated
from the start.

**Do not** create "address review comments" commits. They add noise to
the history and make bisecting harder. Fixup commits squashed into their
parent are the correct approach.

**After squashing:** verify CI still passes before merging.
