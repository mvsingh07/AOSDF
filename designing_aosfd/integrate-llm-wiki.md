You are setting up an LLM Wiki — a persistent, compounding knowledge base — for the                                                  
  project: Comms-Engine
                                                                                                                                       
  ## Project Directory Structure                            
                                                                                                                                       
  {{Comms-Engine}}-Orchestrum/          ← main directory    
  ├── {{project_name}}/                 ← source code (do not read or modify)
  ├── AOSDF/                            ← general AI dev framework (read-only reference)
  ├── {{project_name}}-Documents/       ← primary source of truth for this wiki                                                        
  └── llm-wiki/                         ← CREATE THIS — the wiki lives here                                                            
                                                                                                                                       
  ## Your Task                                                                                                                         
                                                                                                                                       
  Create the `llm-wiki/` folder and its full structure, then ingest all documents from                                                 
  `{{project_name}}-Documents/` into the wiki.              
                                                                                                                                       
  ---                                                       

  ## Step 1 — Create the directory structure                                                                                           
   
  llm-wiki/                                                                                                                            
  ├── WIKI.md              ← schema and rules (create this first)
  ├── index.md             ← content catalog
  ├── log.md               ← append-only event log                                                                                     
  ├── overview.md          ← evolving synthesis
  ├── sessions/                                                                                                                        
  │   └── session-contexts.md   ← session index table       
  ├── sources/             ← one page per ingested document or document group                                                          
  ├── entities/            ← people, orgs, products, services                                                                          
  ├── concepts/            ← ideas, frameworks, patterns, architectural decisions                                                      
  └── analyses/            ← filed query answers and decision records                                                                  
                                                                                                                                       
  ---                                                                                                                                  
                                                            
  ## Step 2 — Create WIKI.md with these exact rules                                                                                    
   
  Write `llm-wiki/WIKI.md` with the following content:                                                                                 
                                                            
  ```markdown                                                                                                                          
  # LLM Wiki — Schema & Rules                               
  # Project: {{project_name}}
                                                                                                                                       
  This wiki is a persistent, compounding knowledge base maintained entirely by the LLM.                                                
  The human curates sources and asks questions. The LLM does all writing, cross-referencing,                                           
  filing, and maintenance.                                                                                                             
                                                            
  ---                                                                                                                                  
                                                            
  ## Directory Layout                                                                                                                  
   
  llm-wiki/                                                                                                                            
  ├── WIKI.md              ← this file                      
  ├── index.md             ← content catalog (updated on every ingest)
  ├── log.md               ← append-only event log                                                                                     
  ├── overview.md          ← evolving synthesis
  ├── sessions/                                                                                                                        
  │   └── session-contexts.md                               
  ├── sources/                                                                                                                         
  ├── entities/
  ├── concepts/                                                                                                                        
  └── analyses/                                             

  Raw sources live in `../{{project_name}}-Documents/` — immutable, never modified by wiki.
  AOSDF framework lives in `../AOSDF/` — referenced but not re-ingested per project.                                                   
                                                                                                                                       
  ---                                                                                                                                  
                                                                                                                                       
  ## Page Frontmatter (required on all wiki pages)                                                                                     
   
  ```yaml                                                                                                                              
  ---                                                       
  title: Page Title
  type: source | entity | concept | analysis | session | overview
  tags: [tag1, tag2]                                                                                                                   
  created: YYYY-MM-DD
  updated: YYYY-MM-DD                                                                                                                  
  sources: [source-slug-1]                                                                                                             
  ---
                                                                                                                                       
  ---                                                       
  Linking Rules
                                                                                                                                       
  - Use [[path/to/page|Display Name]] for all internal links (Obsidian wikilink format)
  - Link from path relative to llm-wiki/ root: [[entities/comms-engine|Comms Engine]]                                                  
  - Link liberally — every named entity, concept, and source mentioned on a page must be linked                                        
  - Dead links are not allowed — create a stub page if the target doesn't exist yet                                                    
  - Bidirectional linking is mandatory: when a new source is ingested, check ALL existing                                              
  wiki pages for topics covered by that source and add backlinks to the new source page
                                                                                                                                       
  ---                                                       
  Workflows                                                                                                                            
                                                            
  INGEST — adding a new source
                                                                                                                                       
  Trigger: Wiki: ingest <path> or Wiki: ingest all                                                                                     
                                                                                                                                       
  Steps:                                                                                                                               
  1. Read the source file(s) fully                          
  2. Discuss key takeaways if the user is present
  3. Write sources/<slug>.md — structured summary
  4. Update index.md — add entry under Sources                                                                                         
  5. Update or create entity pages in entities/                                                                                        
  6. Update or create concept pages in concepts/                                                                                       
  7. Update overview.md — revise synthesis, note any contradictions                                                                    
  8. Backlink pass: check existing wiki pages for topics in this source; add links                                                     
  9. Append to log.md: ## [YYYY-MM-DD] ingest | <slug>                            
                                                                                                                                       
  QUERY — answering a question                                                                                                         
                                                                                                                                       
  Trigger: any question asked in this session                                                                                          
                                                            
  Steps:
  1. Read index.md to find relevant pages
  2. Read relevant pages                                                                                                               
  3. Synthesize answer with citations (link to wiki pages)
  4. If the answer is substantive: offer to file as analyses/<slug>.md                                                                 
  5. If filed: append to log.md: ## [YYYY-MM-DD] query | <slug>                                                                        
                                                                                                                                       
  UPDATE — re-ingesting a changed source                                                                                               
                                                                                                                                       
  Trigger: Wiki: re-ingest <path> or Wiki: re-ingest all                                                                               
                                                            
  Steps:                                                                                                                               
  1. Re-read the updated raw file                           
  2. Update the relevant source page in sources/
  3. Update updated: frontmatter date           
  4. Propagate changes to entity/concept pages                                                                                         
  5. Move superseded claims to ## Superseded Claims section (never delete)                                                             
  6. Append to log.md: ## [YYYY-MM-DD] update | <slug>                                                                                 
                                                                                                                                       
  FULL-SYNC — after bulk document changes                   
                                                                                                                                       
  Trigger: Wiki: full-sync                                  
                                                                                                                                       
  Re-reads every file in {{project_name}}-Documents/, compares against current wiki pages,                                             
  updates any page where the source has changed. Append to log: ## [YYYY-MM-DD] full-sync | all.
                                                                                                                                       
  SESSION — recording a working session                                                                                                
                                                                                                                                       
  Trigger: Wiki: start session or when user explicitly asks to record the session                                                      
                                                            
  Steps:                                                                                                                               
  1. Ask the user: session name (short slug), topic summary 
  2. Create sessions/YYYY-MM-DD-<slug>.md                                                                                              
  3. Add a row to sessions/session-contexts.md
  4. At end of session (or when user says Wiki: close session): write the session summary,                                             
  decisions made, links to any analyses or entities created                                                                            
  5. Append to log.md: ## [YYYY-MM-DD] session | <slug>                                                                                
                                                                                                                                       
  Session file format:                                                                                                                 
  ---                                                                                                                                  
  title: Session — <name>                                                                                                              
  type: session                                             
  tags: [session]                                                                                                                      
  created: YYYY-MM-DD
  session_id: <auto-increment>                                                                                                         
  documented: false | <path-to-analysis-if-filed>           
  ---                                            
                                                                                                                                       
  ## Topic
  ## Decisions Made                                                                                                                    
  ## What Changed in the Wiki                               
  ## Open Questions Raised   
  ## Links                                                                                                                             
          
  LINT — health check                                                                                                                  
                                                                                                                                       
  Trigger: Wiki: lint
                                                                                                                                       
  Check for and report:                                                                                                                
  - Pages with no inbound links (orphans)
  - Pages where updated: is older than the raw source file's last-modified date                                                        
  - Contradictions between pages not yet flagged                               
  - Concepts mentioned on 3+ pages but lacking their own concept page                                                                  
  - Open gaps in sources that have since been resolved               
  - Sessions with documented: false older than 7 days                                                                                  
                                                            
  ---                                                                                                                                  
  session-contexts.md Format                                
                                                                                                                                       
  # Session Contexts                                        
  # {{project_name}}
                                                                                                                                       
  | session_id | session_name | created_at | topic | documented |
  | ---------- | ------------ | ---------- | ----- | ---------- |                                                                      
  | 001 | wiki-init | YYYY-MM-DD | Initial wiki setup and full ingest | false |                                                        
                                                                                                                                       
  ---                                                                                                                                  
  index.md Format                                                                                                                      
                                                            
  # Wiki Index — {{project_name}}
                                                                                                                                       
  ## Overview
  [[overview|Overview]]                                                                                                                
                                                            
  ## Sources (N)
  | Slug | Title | Date | Tags |                                                                                                       
  | ---- | ----- | ---- | ---- |
  | [[sources/slug\|slug]] | Title | date | tags |                                                                                     
                                                                                                                                       
  ## Entities (N)
  - [[entities/name|Name]] — one-line description                                                                                      
                                                                                                                                       
  ## Concepts (N)
  - [[concepts/name|Name]] — one-line description                                                                                      
                                                            
  ## Analyses (N)
  - [[analyses/name|Name]] — one-line description, date
                                                                                                                                       
  ## Sessions (N)
  - [[sessions/YYYY-MM-DD-slug|Name]] — date, topic                                                                                    
                                                                                                                                       
  ---
  Source Page Format                                                                                                                   
                                                            
  ---
  title: [Document title]
  type: source
  tags: []
  created: YYYY-MM-DD                                                                                                                  
  updated: YYYY-MM-DD
  sources: [slug]                                                                                                                      
  ---                                                       

  ## Summary
  ## Key Claims
  ## Key Entities
  ## Key Concepts                                                                                                                      
  ## Tensions & Contradictions
  ## Quotes                                                                                                                            
  ## Source                                                 
  Original file: `../{{project_name}}-Documents/<path>`
                                                                                                                                       
  ---
  Log Format                                                                                                                           
                                                                                                                                       
  Append-only. Newest entries at top.
  Each entry: ## [YYYY-MM-DD] <operation> | <slug>                                                                                     
  Operations: ingest, update, full-sync, query, session, lint, init                                                                    
                                                                                                                                       
  ---                                                                                                                                  
  AOSDF Reference                                                                                                                      
                                                            
  This project follows AOSDF (AI-Orchestrated Software Development Framework).
  Framework files live in: ../AOSDF/                                                                                                   
  AOSDF is not re-ingested into this wiki — it is referenced via the entity page:
  [[entities/aosdf|AOSDF]]                                                                                                             
                                                            
  When an AOSDF agent (captain_agent, research_and_refine_agent, etc.) produces output                                                 
  that lands in {{project_name}}-Documents/, re-ingest those files immediately:
  Wiki: re-ingest ../{{project_name}}-Documents/<changed-file>                                                                         
                                                            
  ---                                                                                                                                  
  Trigger Phrases (Quick Reference)                         
                                                                                                                                       
  ┌────────────────────────┬─────────────────────────────────────────────────┐
  │        Command         │                     Action                      │                                                         
  ├────────────────────────┼─────────────────────────────────────────────────┤
  │ Wiki: ingest <path>    │ Ingest a single file or folder                  │
  ├────────────────────────┼─────────────────────────────────────────────────┤
  │ Wiki: ingest all       │ Ingest all files in {{project_name}}-Documents/ │                                                         
  ├────────────────────────┼─────────────────────────────────────────────────┤
  │ Wiki: re-ingest <path> │ Update wiki from a changed source file          │                                                         
  ├────────────────────────┼─────────────────────────────────────────────────┤                                                         
  │ Wiki: full-sync        │ Re-read all sources, update all stale pages     │
  ├────────────────────────┼─────────────────────────────────────────────────┤                                                         
  │ Wiki: start session    │ Begin a session record                          │
  ├────────────────────────┼─────────────────────────────────────────────────┤                                                         
  │ Wiki: close session    │ Finalize and file the current session           │
  ├────────────────────────┼─────────────────────────────────────────────────┤                                                         
  │ Wiki: lint             │ Health-check the wiki                           │
  ├────────────────────────┼─────────────────────────────────────────────────┤                                                         
  │ Wiki: query <question> │ Explicit query (or just ask naturally)          │
  └────────────────────────┴─────────────────────────────────────────────────┘                                                         
   
  ---                                                                                                                                  
                                                            
  ## Step 3 — Create sessions/session-contexts.md

  ```markdown                                                                                                                          
  # Session Contexts
  # {{project_name}} — LLM Wiki                                                                                                        
                                                            
  | session_id | session_name | created_at | topic | documented |
  | ---------- | ------------ | ---------- | ----- | ---------- |
  | 001 | wiki-init | YYYY-MM-DD | Initial wiki setup and full ingest of {{project_name}}-Documents/ | false |                         
   
  ---                                                                                                                                  
  Step 4 — Ingest all documents                             
                                                                                                                                       
  Run Wiki: ingest all against ../{{project_name}}-Documents/.
                                                                                                                                       
  For each document or logical document group:
  1. Create a source page in sources/                                                                                                  
  2. Create or update entity pages for every named service, system, person, or org mentioned                                           
  3. Create or update concept pages for every key architectural idea, pattern, or rule      
  4. After all sources are ingested, write overview.md as a full synthesis                                                             
  5. Write index.md with all pages listed                                                                                              
  6. Write log.md with the init entry                                                                                                  
                                                                                                                                       
  Linking density requirement: every entity and concept page must link to every source                                                 
  that mentions it. Every source page must link to every entity and concept it introduces.                                             
  The goal is that starting from any page, you can reach any related page in 2 clicks.                                                 
                                                                                                                                       
  ---                                                                                                                                  
  Step 5 — Create the AOSDF entity page                                                                                                
                                                                                                                                       
  Create entities/aosdf.md that describes the framework, links to key agent concepts,
  and notes that the full framework lives at ../AOSDF/. Do not copy framework content                                                  
  into the wiki — reference it.                                                                                                        
                                                                                                                                       
  ---                                                                                                                                  
  Step 6 — Verify                                                                                                                      
                                                            
  After setup, confirm:
  - index.md lists all sources, entities, concepts
  - Every wiki page has complete frontmatter                                                                                           
  - Every entity and concept page has at least 2 inbound links
  - log.md has the init entry                                                                                                          
  - sessions/session-contexts.md has the session-001 row    
  - overview.md is written and reflects the full ingested corpus                                                                       
                                                            
  ---                                                                                                                                 