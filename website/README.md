# AOSDF public website

Public marketing, framework explanation and AI Engineer / FDE learning interface extracted from AOSDF-Hosting. This application has no database, authentication middleware, private repository client or managed deployment pipeline. It builds from this repository alone.

```sh
npm ci
npm run build
# Serve out/ with any static web server.
python3 -m http.server 3000 --directory out
```

`npm run dev` provides Next.js development mode; open `/marketing.html` for the landing page and `/learn` for learning. The production build copies the landing page to `out/index.html`. `npm run check` checks TypeScript. Dynamic learning routes enumerate their published parameters at build time.

Edit `public/marketing.html` here as the canonical landing page. `/hosting/` explains the separately operated service; this checkout does not assume an operator URL or implement sign-in. The private service can import these public files as a compatibility snapshot while retaining its existing routes.

Lesson sources are `../study_material/modules/`. Run `npm run sync:learning` after lesson edits; commit `content/learning/`, `public/learning/` and `lib/learning-docs.generated.ts`. Snapshots let the website build without generating content or contacting a service. Interactive Archify exports and their editable JSON sources live in `public/`.

The website source is covered by the repository LICENSE. Retain THIRD_PARTY_NOTICES.md and the diagram credits when redistributing.
