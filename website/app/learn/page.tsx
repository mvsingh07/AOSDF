import Link from "next/link";
import type { Metadata } from "next";
import { aiEngineerRoadmap } from "../../lib/learning";
import styles from "./learn.module.css";

export const metadata: Metadata = { title: "Learning · Orchestrum", description: "A practical AI Engineer / FDE learning roadmap." };

export default function LearningHome() {
  return <div className={styles.shell}>
    <header className={styles.header}><Link href="/" className={styles.brand}>◼ Orchestrum</Link><span>Learning</span></header>
    <main className={styles.home}>
      <p className={styles.eyebrow}>Learn while you build</p>
      <h1>Choose a roadmap</h1>
      <p className={styles.lead}>Start with the working model. Open deeper reading when a real task needs it. No schedule, account, or setup required.</p>
      <Link className={styles.roadmapChoice} href={`/learn/${aiEngineerRoadmap.id}`}>
        <span className={styles.choiceIcon}>↗</span>
        <span><strong>{aiEngineerRoadmap.title}</strong><small>{aiEngineerRoadmap.description}</small><em>{aiEngineerRoadmap.modules.length} connected modules · {aiEngineerRoadmap.modules.filter((module) => module.status === "available").length} modules available · interactive diagram</em></span>
        <span aria-hidden="true" className={styles.choiceArrow}>→</span>
      </Link>
    </main>
  </div>;
}
