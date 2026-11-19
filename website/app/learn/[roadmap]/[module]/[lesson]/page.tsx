import { notFound } from "next/navigation";
import type { Metadata } from "next";
import LearningDocs from "../../../../../components/LearningDocs";
import { aiEngineerRoadmap } from "../../../../../lib/learning";
import { moduleManifests } from "../../../../../lib/learning-docs.generated";

type Props = { params: Promise<{ roadmap: string; module: string; lesson: string }> };
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { module, lesson } = await params;
  const manifest = moduleManifests[module as keyof typeof moduleManifests];
  const item = manifest?.lessons.find((entry) => entry.id === lesson);
  return { title: item ? `${item.title} · ${manifest.title}` : "Learning" };
}
export default async function LessonPage({ params }: Props) {
  const { roadmap, module, lesson } = await params;
  const manifest = moduleManifests[module as keyof typeof moduleManifests];
  if (roadmap !== aiEngineerRoadmap.id || !manifest || !manifest.lessons.some((entry) => entry.id === lesson)) notFound();
  return <LearningDocs moduleId={module as keyof typeof moduleManifests} lessonId={lesson} />;
}

export function generateStaticParams() { return Object.values(moduleManifests).flatMap((manifest) => manifest.lessons.map((lesson) => ({ roadmap: aiEngineerRoadmap.id, module: manifest.id, lesson: lesson.id }))); }
