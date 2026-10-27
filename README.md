# Silinosic-X Website

This branch contains the static documentation website for Silinosic-X v11.2.2.

## Purpose

The site is intentionally plain HTML, CSS, and JavaScript so it can be:

- served by GitHub Pages
- edited without a build step
- kept close to the repository docs and current runtime state

## Structure

### Pages

- `website/index.html` is the landing and project overview page
- `website/getting-started.html` covers installation, prerequisites, and first runs
- `website/download.html` links to Docker runner scripts and installation paths
- `website/workflow.html` explains the four main workflows and layered runtime design
- `website/cli-reference.html` documents commands, aliases, and common flags
- `website/modes.html` describes prompt, wizard, live, and source-study runtime modes
- `website/reporting.html` explains Reporter, output formats, storage, history, and testing
- `website/development.html` shows repository health and GitHub activity signals
- `website/project.html` covers project context, author, legal use, and roadmap signals

### CSS

- `website/css/core/` holds shared tokens and baseline styles
- `website/css/layout/` holds top bar, sidebar, content, and responsive layout rules
- `website/css/components/` holds component-specific styling

### JavaScript

- `website/js/core/` holds shared docs data and helper utilities
- `website/js/features/` holds isolated interactive features
- `website/js/bootstrap/` wires the site together

### Assets

- `website/web_assets/media/` holds the Silinosic-X website image and favicon
- `website/web_assets/installers/` is reserved for downloadable installer assets if the site later ships mirrored copies

## Load Order

Load CSS in this order:

1. `website/css/core/base.css`
2. `website/css/layout/topbar.css`
3. `website/css/layout/sidebar.css`
4. `website/css/layout/content.css`
5. `website/css/components/workflow.css`
6. `website/css/components/modules.css`
7. `website/css/components/development.css`
8. `website/css/components/console.css` (home and workflow pages)
9. `website/css/layout/responsive.css`
10. `website/css/core/polish.css` (always last: accessibility, motion, mobile topbar)

Load JavaScript in this order:

1. `website/js/core/site-data.js`
2. `website/js/core/helpers.js`
3. `website/js/features/sidebar.js`
4. `website/js/features/search.js`
5. `website/js/features/workflow-visual.js`
6. `website/js/features/easter-eggs.js`
7. `website/js/features/development-feed.js`
8. `website/js/features/ui-enhancements.js`
9. `website/js/bootstrap/app.js`

## Maintenance Rules

- Keep the site fully static.
- Keep asset paths relative so GitHub Pages works cleanly.
- Put shared tokens and reusable components in the shared CSS modules.
- Keep page-specific behavior out of HTML where possible.
- Favor repository-accurate wording over marketing claims that the codebase does not support yet.
- Keep version strings, docs links, and Reporter wording aligned with the root `README.md` and `docs/*.md`.

## Verification

Local JavaScript parse checks:

```powershell
node --check website/js/core/site-data.js
node --check website/js/core/helpers.js
node --check website/js/features/sidebar.js
node --check website/js/features/search.js
node --check website/js/features/workflow-visual.js
node --check website/js/features/easter-eggs.js
node --check website/js/features/development-feed.js
node --check website/js/features/ui-enhancements.js
node --check website/js/bootstrap/app.js
```
