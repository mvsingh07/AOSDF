# Repository and publication boundaries

The parent workspace is not a Git repository. These are independent repositories with independent visibility and releases.

| Repository | Visibility | Owns |
| --- | --- | --- |
| AOSDF | Public | Framework, roles, policies, templates, inactive coordination tooling, MCP, VS Code, metadata tools, learning content, website and synthetic examples |
| AOSDF-Hosting | Private | Managed service, login/dashboard, registry, private repository fetching, build orchestration, sharing and hosted-document access |
| AOSDF-Documents | Private | Internal requirements, execution tracking, design history, product-specific prompts and planning |
| AOSDF-Operations | Private, optional future repository | Infrastructure and operational runbooks when a separate repository is warranted |

Public code must be usable without a private sibling checkout. The website builds from committed public content. Hosting imports explicit, versioned public source snapshots; its ordinary build needs only its own checkout. Hosted features may be described publicly without distributing their implementation. Customers can use the framework and local documentation builds independently of the managed service.

Keep live thread records, sprint assignments, claims, result receipts, model profiles, customer repositories, credentials and production data in their owning private project or secret store. Publish schemas, inactive examples, tests and synthetic walkthroughs. Never copy an active Supagram/Comms Engine thread into templates. Product names alone do not establish permission to publish their underlying code or documents.

Separate repository access controls enforce this boundary; ignored folders inside a public repository do not. Check the actual files and Git history before publishing. Ignore rules do not remove previously tracked data.

The legacy public pages retained in Hosting are compatibility snapshots, not a second authoring source. See website/README.md and the private service's snapshot import instructions. Live route/deployment retirement is a separate operational change.
