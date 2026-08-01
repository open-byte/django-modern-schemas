# Publishing Documentation

The Material site is published to GitHub Pages at
[open-byte.github.io/django-modern-schemas](https://open-byte.github.io/django-modern-schemas/).

## One-Time Repository Setup

An organization owner or repository administrator must enable GitHub Pages once:

1. Open the repository **Settings**.
2. Open **Pages** in the sidebar.
3. Under **Build and deployment**, choose **GitHub Actions** as the source.

The deployment workflow then has the permissions it needs to publish the built
site.

## Automatic Deployment

[`deploy-docs.yml`](https://github.com/open-byte/django-modern-schemas/blob/main/.github/workflows/deploy-docs.yml)
deploys after a push to `main` that changes documentation, executable examples,
the Material configuration, or documentation dependencies.

The workflow:

1. Installs the locked `docs` dependency group with `uv`.
2. Runs `mkdocs build --strict`.
3. Uploads the generated `site/` directory to GitHub Pages.

The deployment URL appears in the **Deploy Documentation** workflow summary.

## Manual Deployment

Open the repository **Actions** tab, choose **Deploy Documentation**, and select
**Run workflow**. This is useful when Pages has just been enabled or when a
deployment must be repeated without another documentation commit.

## Local Verification

Build the same artifact before pushing:

```bash
uv sync --group docs
uv run --group docs mkdocs build --strict
```

Preview it locally with:

```bash
uv run --group docs mkdocs serve
```