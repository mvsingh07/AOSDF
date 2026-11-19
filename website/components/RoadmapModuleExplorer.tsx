"use client";

import { useState } from "react";
import Link from "next/link";
import type { LearningModule } from "../lib/learning";
import styles from "../app/learn/learn.module.css";

type PublishedLesson = { id: string; title: string };

export default function RoadmapModuleExplorer({ modules, roadmapId, publishedLessons }: { modules: LearningModule[]; roadmapId: string; publishedLessons: Record<string, PublishedLesson[]> }) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selected = modules[selectedIndex];
  const lessons = publishedLessons[selected.id] ?? [];
  const topics = selected.status === "available" ? lessons.map((lesson) => lesson.title) : selected.topics;
  const moduleUrl = `/learn/${roadmapId}/${selected.id}`;
  const availableCount = modules.filter((module) => module.status === "available").length;
  return <section className={styles.moduleSection} aria-labelledby="modules-heading">
    <div className={styles.panelTop}><div><span>MODULE INDEX</span><h2 id="modules-heading">Explore the learning path</h2></div><small>{String(availableCount).padStart(2, "0")} available · {String(modules.length - availableCount).padStart(2, "0")} planned</small></div>
    <div className={styles.explorer}>
      <div className={styles.moduleList} aria-label="Roadmap modules">
        {modules.map((module, index) => <button key={module.id} type="button" onClick={() => setSelectedIndex(index)} aria-pressed={selectedIndex === index} aria-controls="module-preview" className={`${styles.moduleCard} ${selectedIndex === index ? styles.moduleSelected : ""}`}>
          <span className={styles.moduleNumber}>{String(index + 1).padStart(2, "0")} / {module.stage.split(" · ")[1]}</span>
          <strong>{module.title}</strong>
          <span className={styles.moduleStatus}>{module.status === "available" ? "Documentation available" : "Planned outline"}<span aria-hidden="true">→</span></span>
        </button>)}
      </div>
      <div id="module-preview" className={styles.preview} aria-live="polite">
        <div className={styles.previewHead}><span className={styles.previewEyebrow}>MODULE {String(selectedIndex + 1).padStart(2, "0")} · {selected.stage.split(" · ")[1]}</span><span className={selected.status === "available" ? styles.availableBadge : styles.plannedBadge}>{selected.status === "available" ? "AVAILABLE" : "PLANNED"}</span></div>
        <h3>{selected.title}</h3><p className={styles.previewSummary}>{selected.summary}</p>
        <div className={styles.previewDivider} />
        <h4>{selected.status === "available" ? "Lesson index" : "Topic outline"}</h4>
        <ol className={styles.previewTopics}>{topics.map((topic, index) => <li key={topic}>
          <span>{String(index + 1).padStart(2, "0")}</span>
          {selected.status === "available" ? <Link href={`${moduleUrl}/${lessons[index].id}`}>{topic}<span aria-hidden="true">↗</span></Link> : <span>{topic}</span>}
        </li>)}</ol>
        {selected.status === "available" ? <div className={styles.previewActions}>
          <Link className={styles.primaryAction} href={moduleUrl}>Open module documentation →</Link>
          <a className={styles.diagramAction} href={selected.id === "async-systems" ? "/queue-delivery-lifecycle.archify.html" : selected.id === "scale-design" ? "/scale-system-design.archify.html" : "/ml-foundations-lifecycle.archify.html"} target="_blank" rel="noopener noreferrer">Explore the module diagram ↗</a>
        </div> : <p className={styles.previewNote}>This is the planned scope. Lessons and source links will appear here when this module is published.</p>}
      </div>
    </div>
  </section>;
}
