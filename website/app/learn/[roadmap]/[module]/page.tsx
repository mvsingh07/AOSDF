import { notFound } from "next/navigation";
import type { Metadata } from "next";
import LearningDocs from "../../../../components/LearningDocs";
import { aiEngineerRoadmap } from "../../../../lib/learning";
import { moduleManifests } from "../../../../lib/learning-docs.generated";

type Props = { params: Promise<{ roadmap: string; module: string }> };
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { module } = await params;
  const manifest = moduleManifests[module as keyof typeof moduleManifests];
  return { title: manifest ? `${manifest.title} · AI Engineer / FDE` : "Learning", description: manifest?.summary };
}

export default async function ModulePage({ params }: Props) {
  const { roadmap, module } = await params;
  if (roadmap !== aiEngineerRoadmap.id || !(module in moduleManifests)) notFound();
  return <LearningDocs moduleId={module as keyof typeof moduleManifests} />;
}

export function generateStaticParams() { return Object.keys(moduleManifests).map((module) => ({ roadmap: aiEngineerRoadmap.id, module })); }
