# Halo docs (Mintlify)

This folder is a [Mintlify](https://mintlify.com) docs site. `docs.json` is the config;
each `.mdx` file is a page.

## Preview locally

```bash
npm i -g mint        # one-time
cd docs-site
mint dev             # http://localhost:3000
```

## Publish (get the live link)

1. Go to [mintlify.com](https://mintlify.com) and sign in with GitHub.
2. Create a project and point it at this repo, with the docs directory set to `docs-site`.
3. Mintlify gives you a hosted link (e.g. `https://halo.mintlify.app`) and redeploys on
   every push to the repo.

Optional: add a `logo/` and `favicon` in `docs.json` for branding, and a custom domain in
the Mintlify dashboard.

## Pages

- `introduction.mdx` — what Halo is (problem / solution / a real run)
- `how-it-works.mdx` — the workflow, the three operating modes, a walkthrough
- `architecture.mdx` — monorepo, components, the safety design
- `truefoundry.mdx` — exactly which gateway features we used and how
- `api-reference.mdx` — the incident API
