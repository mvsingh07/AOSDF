import Link from "next/link";
import styles from "../learn/learn.module.css";
export const metadata = { title: "AOSDF managed hosting" };
export default function HostingPage() {
  return <div className={styles.shell}>
    <header className={styles.header}><Link href="/">◼ AOSDF</Link><Link href="/framework/">Framework</Link></header>
    <main className={styles.home}>
      <p className={styles.eyebrow}>Companion service</p><h1>Managed documentation hosting</h1>
      <p className={styles.lead}>The companion AOSDF Hosting application connects GitHub repositories to documentation builds and deployment, with project ownership and editor/viewer sharing.</p>
      <p>The hosted application has its own login, dashboard and deployment configuration. This public website is independently buildable and does not include that service or assume a particular operator URL.</p>
      <p>You can use AOSDF and build project documentation locally without a hosting account. Follow the repository setup guide to get started.</p>
      <p><a href="https://github.com/mvsingh07/AOSDF">Open AOSDF on GitHub</a> · <Link href="/framework/">Understand the development model</Link></p>
    </main>
  </div>;
}
