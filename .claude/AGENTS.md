# Agent instructions (zapret2)

When working in this repo, **always follow the project rules** in `.claude/rules/`. They define how we work. Agents must apply these rules in every session and must not skip them.

## Rules that always apply

- **agent-communication.mdc** — Always ask for clarification on complex choices and do not guess.
- **git-workflow.mdc** — Branching (master / feature|fix|refactor), merge flow, one task per branch. Never work directly in `master` for features.
- **commit-standards.mdc** — One logical change per commit; message format `type: short description`; group by task when staging.
- **ci-cd-versioning.mdc** — Desktop app layout, versioning (SemVer with VERSION file), CI/CD stages (GitHub Actions + Jenkins).
- **safe-development.mdc** — No secrets in code; validate input; handle errors; Windows security considerations.

## Rules that apply in context

- **jenkins-pipeline.mdc** — When editing `Jenkinsfile` or `*.groovy` files.
- **release-management.mdc** — When creating releases, bumping versions, or updating CHANGELOG.

## In practice

- Before suggesting git commands (branch, merge, commit), follow **git-workflow.mdc** and **commit-standards.mdc**.
- When touching CI, versioning, or build process, follow **ci-cd-versioning.mdc** (and **jenkins-pipeline.mdc** if applicable).
- When editing code or handling user input, follow **safe-development.mdc**.
- When creating releases, follow **release-management.mdc**.

Consider these rules part of the definition of "done" for any change in this project.

## Project Context

zapret2 is a Windows desktop application for bypassing network blocks (Discord, YouTube). It uses:
- Python 3.12+ with PyInstaller for EXE builds
- WinDivert for packet manipulation (requires admin rights)
- System tray GUI with preset management
- Hybrid CI/CD: GitHub Actions (PR validation, releases) + Jenkins (delivery pipeline)
- Artifacts published to GitHub Releases and Playerok Artifact Server

## Key Files

- `VERSION` — SemVer version (e.g., 1.0.0)
- `src/` — Python source code
- `build/build.bat` — PyInstaller build script
- `Jenkinsfile` — Jenkins delivery pipeline
- `.github/workflows/` — GitHub Actions workflows
- `CONTRIBUTING.md` — Development guidelines
- `CHANGELOG.md` — Release history

## Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes, write tests
3. Commit: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Create PR to `master`
6. After merge, Jenkins builds and publishes artifacts

## Release Workflow

1. Bump version: `python scripts/bump_version.py [major|minor|patch]`
2. Update CHANGELOG.md
3. Commit: `git commit -am "chore: bump version to X.Y.Z"`
4. Tag: `git tag vX.Y.Z`
5. Push: `git push origin master --tags`
6. GitHub Actions creates release automatically
