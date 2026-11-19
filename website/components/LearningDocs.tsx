import Link from "next/link";
import { Children, Fragment, isValidElement } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { aiEngineerRoadmap } from "../lib/learning";
import { moduleManifests, modulePages } from "../lib/learning-docs.generated";
import LearningDocsFrame from "./LearningDocsFrame";
import styles from "../app/learn/docs.module.css";

const mlSteps = [
  { title: "Decision", detail: "target + baseline" },
  { title: "Examples", detail: "features + labels" },
  { title: "Holdout", detail: "future-like cases" },
  { title: "Train", detail: "fit parameters" },
  { title: "Evaluate", detail: "errors + threshold" },
  { title: "Serve", detail: "review + monitor" },
];
const queueSteps = [
  { title: "Accept", detail: "operation ID" },
  { title: "Commit", detail: "state + outbox" },
  { title: "Publish", detail: "durable queue" },
  { title: "Claim", detail: "visibility lease" },
  { title: "Apply", detail: "safe effect" },
  { title: "Ack", detail: "after success" },
];
const scaleSteps = [
  { title: "Promise", detail: "requirements + SLO" },
  { title: "Estimate", detail: "peak + p99" },
  { title: "Route", detail: "edge + API" },
  { title: "Store", detail: "queries + cache" },
  { title: "Coordinate", detail: "versions + locks" },
  { title: "Evolve", detail: "measure + roll out" },
];
const diagrams = {
  "ml-foundations": { marker: "<!-- ML_LIFECYCLE_DIAGRAM -->", steps: mlSteps, label: "ML feature lifecycle from decision to monitored serving", href: "/ml-foundations-lifecycle.archify.html", caption: "Follow the decision from problem framing to monitored use." },
  "async-systems": { marker: "<!-- QUEUE_LIFECYCLE_DIAGRAM -->", steps: queueSteps, label: "Queue delivery from acceptance to acknowledgement", href: "/queue-delivery-lifecycle.archify.html", caption: "Follow durable acceptance, processing, and acknowledgement; inspect the failure branch in the full diagram." },
  "scale-design": { marker: "<!-- SCALE_DESIGN_DIAGRAM -->", steps: scaleSteps, label: "Scale design from requirements to a safely evolving system", href: "/scale-system-design.archify.html", caption: "Trace the document service from a user request through routing, data, and a compatible rollout." },
} as const;

function slug(text: string) {
  return text.toLowerCase().replace(/[^a-z0-9\s-]/g, "").trim().replace(/\s+/g, "-");
}

export default function LearningDocs({ moduleId, lessonId }: { moduleId: keyof typeof moduleManifests; lessonId?: string }) {
  const moduleManifest = moduleManifests[moduleId];
  const base = `/learn/${aiEngineerRoadmap.id}/${moduleManifest.id}`;
  const diagram = diagrams[moduleId];
  const moduleNumber = aiEngineerRoadmap.modules.findIndex((entry) => entry.id === moduleId) + 1;
  const index = lessonId ? moduleManifest.lessons.findIndex((lesson) => lesson.id === lessonId) : -1;
  const current = index >= 0 ? moduleManifest.lessons[index] : null;
  const markdown = modulePages[moduleId][current?.file ?? moduleManifest.index];
  const diagramParts = markdown.split(diagram.marker);
  const headings = [...markdown.matchAll(/^## (.+)$/gm)].map((match) => ({ label: match[1], id: slug(match[1]) }));
  const previous = index > 0 ? moduleManifest.lessons[index - 1] : null;
  const next = index === -1 ? moduleManifest.lessons[0] : moduleManifest.lessons[index + 1];
  return <LearningDocsFrame moduleTitle={moduleManifest.title}
    sidebar={<aside id="module-sidebar" className={styles.sidebar} aria-label="Module contents">
        <Link href={`/learn/${aiEngineerRoadmap.id}`} className={styles.back}>← All modules</Link>
        <p className={styles.sidebarLabel}>MODULE {String(moduleNumber).padStart(2, "0")}</p>
        {moduleId === "async-systems" && <img className={styles.moduleMark} src="/learning/async-systems/queue-mark.svg" width="48" height="48" alt="" aria-hidden="true" />}
        {moduleId === "scale-design" && <img className={styles.moduleMark} src="/learning/scale-design/scale-mark.svg" width="48" height="48" alt="" aria-hidden="true" />}
        <h2>{moduleManifest.title}</h2>
        <nav><Link href={base} aria-current={!current ? "page" : undefined} className={!current ? styles.current : ""}>Overview</Link>
          {moduleManifest.lessons.map((lesson, lessonIndex) => <Link key={lesson.id} href={`${base}/${lesson.id}`} aria-current={lesson.id === lessonId ? "page" : undefined} className={lesson.id === lessonId ? styles.current : ""}><span>{String(lessonIndex + 1).padStart(2, "0")}</span>{lesson.title}</Link>)}
        </nav>
      </aside>}
    toc={<aside className={styles.toc} aria-label="On this page"><strong>ON THIS PAGE</strong>{headings.map((heading) => <a href={`#${heading.id}`} key={heading.id}>{heading.label}</a>)}</aside>}>
      <main className={styles.main}>
        <div className={styles.articleMeta}><span>{current ? `LESSON ${String(index + 1).padStart(2, "0")} OF ${moduleManifest.lessons.length}` : "MODULE OVERVIEW"}</span><span>{moduleManifest.level}</span></div>
        <article className={styles.article}>
          {diagramParts.map((part, partIndex) => <Fragment key={partIndex}>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
              h2: ({ children }) => <h2 id={slug(String(children))}>{children}</h2>,
              a: ({ href, children }) => href?.startsWith("/") ? <Link href={href}>{children}</Link> : <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
              p: ({ node, children }) => {
                const image = node?.children.length === 1 && node.children[0].type === "element" && node.children[0].tagName === "img" ? node.children[0] : null;
                if (image) return <figure className={styles.studyFigure}><div className={styles.studyFigureViewport}>{children}</div><figcaption>{String(image.properties?.alt ?? "")}</figcaption></figure>;
                return <p>{children}</p>;
              },
              img: ({ src, alt }) => typeof src === "string" && src.startsWith("/learning/scale-design/logo-")
                ? <img className={styles.techLogo} src={src} alt={alt ?? ""} width="32" height="32" loading="lazy" />
                : <img className={styles.studyFigureImage} src={src} alt={alt ?? ""} width="920" height="402" loading="lazy" />,
              pre: ({ children }) => {
                const code = Children.toArray(children).find((child) => isValidElement(child));
                if ((moduleId === "async-systems" || moduleId === "scale-design") && isValidElement<{ className?: string }>(code) && code.props.className?.includes("language-aosdf-diagram")) {
                  return <details className={styles.textDiagram}><summary>Read the text version of this flow</summary><pre>{children}</pre></details>;
                }
                return <pre>{children}</pre>;
              },
            }}>{part}</ReactMarkdown>
            {partIndex < diagramParts.length - 1 && <figure className={styles.embeddedDiagram}>
              <div className={styles.diagramViewport}>
                <ol className={styles.diagramFlow} aria-label={diagram.label}>{diagram.steps.map((step, stepIndex) => <li key={step.title}><span>{String(stepIndex + 1).padStart(2, "0")}</span><strong>{step.title}</strong><small>{step.detail}</small></li>)}</ol>
              </div>
              <figcaption>{diagram.caption} <a href={diagram.href} target="_blank" rel="noopener noreferrer">Open the full interactive diagram ↗</a></figcaption>
            </figure>}
          </Fragment>)}
        </article>
        <nav className={styles.pager} aria-label="Lesson navigation">
          {previous ? <Link href={`${base}/${previous.id}`}>← {previous.title}</Link> : current ? <Link href={base}>← Module overview</Link> : <span />}
          {next ? <Link href={`${base}/${next.id}`}>{next.title} →</Link> : <Link href={`/learn/${aiEngineerRoadmap.id}`}>Back to roadmap →</Link>}
        </nav>
      </main>
  </LearningDocsFrame>;
}
