import Link from "next/link";
import styles from "../learn/learn.module.css";
export const metadata = { title: "AOSDF framework and software factory foundations" };
export default function FrameworkPage() {
  return <div className={styles.shell}>
    <header className={styles.header}><Link href="/">◼ AOSDF</Link><Link href="/learn">Learning</Link></header>
    <main className={styles.home}>
      <p className={styles.eyebrow}>AI-orchestrated software development</p>
      <h1>The foundations of a software factory</h1>
      <p className={styles.lead}>AOSDF turns requirements and architecture into traceable execution plans. Specialized agents coordinate through explicit ownership, durable handoffs, risk-based review and evidence-based validation.</p>
      <h2>Use the public framework</h2>
      <p>The open-source project includes specifications, agent roles, project templates, coordination protocols and inactive automation, MCP and VS Code integrations, documentation tooling, and learning content.</p>
      <p><a href="https://github.com/mvsingh07/AOSDF">Browse the source and setup guide</a></p>
      <h2>Coordinate development threads</h2>
      <p>A Solution Architect maintains the execution plan. Coordinators manage thread ownership and handoffs. Workers implement bounded tasks, while review and validation scale with risk. Accepted results are reconciled without redispatching completed work. Each adopting project owns its configuration and runtime records.</p>
      <h2>Understand the current boundary</h2>
      <p>Reusable automation is inactive by default. AOSDF does not yet claim proven fully autonomous specification-to-production delivery. Repeatable releases across independent applications, measured human intervention, build reproducibility and recovery evidence remain the next factory milestones.</p>
      <h2>Managed hosting is a separate service</h2>
      <p>The privately operated companion application provides GitHub-connected documentation builds, deployment, authenticated access and role-based sharing. Its service code and customer records remain separate from this public repository.</p>
      <p><Link href="/hosting/">About the hosting service</Link> · <Link href="/learn/">Explore the learning material</Link></p>
    </main>
  </div>;
}
