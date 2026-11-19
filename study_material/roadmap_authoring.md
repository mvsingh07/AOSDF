# Learning Roadmap Authoring Order

Use this order when creating a project-specific learning roadmap. The framework's public
AI Engineer / FDE roadmap is a baseline example; a project's roadmap should still point to its
actual design decisions and source documents.

1. **Start from the work.** Identify the next feature, its user, success condition, and trust
   boundaries. Pick only concepts needed to understand or review that work.
2. **Teach the working model first.** The module overview and first lesson define the core
   subject before introducing its failure modes or architecture terms. Give a plain-language
   definition, explain when it is used, name the parts in one concrete example, show a small
   browser-rendered figure when it clarifies flow, and offer one practical engineering exercise that a newcomer can attempt. Use local
   vector assets with descriptive alt text and captions; preserve a text diagram as a fallback
   where the framework's diagram index needs one. Keep the engineering
   contracts, trade-offs, and failure review in the same learning path so experienced readers
   can move directly to them.
3. **Order by dependency.** Start with ML and cloud fundamentals; make queues, reliability,
   and system-design trade-offs concrete in a working service. Introduce transformers and
   embeddings before RAG, evaluation before advanced retrieval changes, tool policy before
   agents, and production operations before customer rollout. Apply identity and authorization
   at every private-data or tool boundary rather than waiting for a late security phase.
4. **Make safety cross-cutting.** At each module, ask what is untrusted, what authority is used,
   what data could leak, and how failure is detected. Add dedicated security modules for attacks
   that the project actually exposes. Never claim a system cannot be hacked.
5. **Link to evidence.** Every module points to the relevant project ADR/code and to a maintained
   primary source for general facts. A module link must open the exact reading page, not a home page.
   For each major function, show example tools or frameworks, where they sit in the design,
   a small implementation example, and a limitation to test. Self-host relevant product logos
   with provenance when visuals improve recognition; do not treat a vendor name as an explanation.
6. **Defer depth deliberately.** List advanced topics under “learn later when needed”; do not
   assign calendar dates or block feature work on reading a textbook.
7. **Check the navigation.** Each available diagram node has a stable ID and opens a module index;
   each lesson has a stable ID and direct URL. Give each topic its own documentation page with
   explanation, example, diagram context, exercise, answer guide, and source links. Verify links
   and a keyboard path.

The public sequence is derived from [`roadmap.md`](roadmap.md), with its week/day schedule
removed. The coverage map in [`roadmap_curriculum.md`](roadmap_curriculum.md) records which
reference sections became which modules. Public lessons use general examples and do not refer
to private projects. Project-specific roadmaps can cite their own systems and decisions.

The public roadmap catalog lives as typed objects in `AOSDF-Hosting/lib/learning.ts`.
The complete ML foundations, Queues and reliable delivery, and Scale and system design modules have manifests and separate
Markdown pages in [`modules/ml-foundations/`](modules/ml-foundations/README.md),
[`modules/async-systems/`](modules/async-systems/README.md), and
[`modules/scale-design/`](modules/scale-design/README.md). Syncing generates the deployable
content snapshots. Stable IDs allow a later database-backed loader without changing public URLs.
This document is authoring guidance, not an instruction to add a roadmap editor or a database now.
