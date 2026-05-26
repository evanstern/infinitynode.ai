# infinitynode.ai blog

A minimal Astro blog for developer notes, idea dumps, and project logs. The site is static, file-based, and intentionally plain.

## Commands

Install dependencies:

```sh
npm install
```

Run the local development server:

```sh
npm run dev
```

Host the dev server for VS Code port forwarding:

```sh
npm run dev:host -- --port 4326
```

Check Astro, TypeScript, Markdown, and MDX content:

```sh
npm run check
```

Build the static site:

```sh
npm run build
```

Preview the built site:

```sh
npm run preview
```

## Writing posts

Posts live in `src/content/posts` and can be written as Markdown (`.md`) or MDX (`.mdx`). The home page lists non-draft posts newest first. Each non-draft post gets a static page at `/posts/<slug>/`.

Use this frontmatter:

```yaml
---
title: Post title
description: Short summary for listings and meta tags.
pubDate: 2026-05-26
draft: false
---
```

Set `draft: true` to keep a post out of the home page, static post routes, and RSS feed.

## Project shape

- `astro.config.mjs` sets the production site URL and enables MDX support.
- `src/content.config.ts` defines the `posts` content collection schema.
- `src/pages/index.astro` lists non-draft posts.
- `src/pages/posts/[...slug].astro` renders post pages, including nested post paths.
- `src/pages/rss.xml.ts` generates the RSS feed from non-draft posts.
- `src/styles/global.css` contains the small global stylesheet.

## Verification

Before handing off changes, run:

```sh
npm install
npm run check
npm run build
```

This verifies dependencies, content collection types, Astro pages, RSS, and the static build output.
