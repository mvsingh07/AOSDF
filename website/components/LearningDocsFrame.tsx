"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import styles from "../app/learn/docs.module.css";

const storageKey = "learning-docs-sidebar-collapsed";

export default function LearningDocsFrame({
  moduleTitle,
  sidebar,
  toc,
  children,
}: {
  moduleTitle: string;
  sidebar: ReactNode;
  toc: ReactNode;
  children: ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    setCollapsed(window.sessionStorage.getItem(storageKey) === "true");
  }, []);

  function toggleSidebar() {
    const next = !collapsed;
    setCollapsed(next);
    window.sessionStorage.setItem(storageKey, String(next));
  }

  return <div className={`${styles.shell} ${collapsed ? styles.sidebarCollapsed : ""}`}>
    <header className={styles.header}>
      <div className={styles.headerStart}>
        <button className={styles.sidebarToggle} type="button" onClick={toggleSidebar}
          aria-controls="module-sidebar" aria-expanded={!collapsed}
          aria-label={collapsed ? "Show module contents" : "Hide module contents"}>
          <svg aria-hidden="true" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="2" y="2.5" width="14" height="13" rx="2" stroke="currentColor" strokeWidth="1.5" />
            <path d="M6.5 3v12" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          <span>{collapsed ? "Show contents" : "Hide contents"}</span>
        </button>
        <Link href="/" className={styles.brand}>◼ Orchestrum</Link>
      </div>
      <nav aria-label="Learning navigation"><Link href="/learn">Learning</Link><span>/</span><Link href="/learn/ai-engineer-fde">AI Engineer / FDE</Link><span>/</span><strong>{moduleTitle}</strong></nav>
    </header>
    <div className={styles.docsLayout}>
      {sidebar}
      {children}
      {toc}
    </div>
  </div>;
}
