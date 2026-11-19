import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { aiEngineerRoadmap } from "../../../lib/learning";
import LearningArchify from "../../../components/LearningArchify";
import RoadmapModuleExplorer from "../../../components/RoadmapModuleExplorer";
import { moduleManifests } from "../../../lib/learning-docs.generated";
import styles from "../learn.module.css";

type Props = { params: Promise<{ roadmap: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { roadmap } = await params;
  return { title: roadmap === aiEngineerRoadmap.id ? `${aiEngineerRoadmap.title} · Learning` : "Learning" };
}

export default async function RoadmapPage({ params }: Props) {
  const { roadmap } = await params;
  if (roadmap !== aiEngineerRoadmap.id) notFound();
  return <div className={styles.shell}>
    <header className={styles.header}><Link href="/" className={styles.brand}>◼ Orchestrum</Link><nav aria-label="Learning navigation"><Link href="/learn">Learning</Link><span>/</span><strong>{aiEngineerRoadmap.title}</strong></nav></header>
    <main className={styles.workspace}>
      <div className={styles.intro}><div><p className={styles.eyebrow}>Roadmap · {aiEngineerRoadmap.modules.length} modules</p><h1>{aiEngineerRoadmap.title}</h1><p>{aiEngineerRoadmap.description}</p></div></div>
      <LearningArchify />
      <RoadmapModuleExplorer modules={aiEngineerRoadmap.modules} roadmapId={aiEngineerRoadmap.id} publishedLessons={Object.fromEntries(Object.values(moduleManifests).map((manifest) => [manifest.id, manifest.lessons.map(({ id, title }) => ({ id, title }))]))} />
    </main>
  </div>;
}

export function generateStaticParams() { return [{ roadmap: aiEngineerRoadmap.id }]; }
