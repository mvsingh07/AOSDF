"use client";

import { useCallback } from "react";
import styles from "../app/learn/learn.module.css";

export default function LearningArchify() {
  const connect = useCallback((frame: HTMLIFrameElement | null) => {
    if (!frame) return;
    frame.onload = () => {
      const document = frame.contentDocument;
      if (!document) return;
      const moduleLinks: Record<string, { id: string; label: string }> = {
        ml_foundations: { id: "ml-foundations", label: "ML foundations" },
        async_systems: { id: "async-systems", label: "Queues and reliable delivery" },
        scale_design: { id: "scale-design", label: "Scale and system design" },
      };
      for (const node of document.querySelectorAll<SVGElement>("[data-node-id]")) {
        const id = node.dataset.nodeId;
        if (!id || !moduleLinks[id]) continue;
        node.style.cursor = "pointer";
        node.setAttribute("role", "link");
        node.setAttribute("tabindex", "0");
        node.setAttribute("aria-label", `Open ${moduleLinks[id].label} documentation`);
      }
      const openNode = (event: Event) => {
        const node = (event.target as Element | null)?.closest?.("[data-node-id]");
        const id = node?.getAttribute("data-node-id");
        if (!id || !moduleLinks[id]) return;
        if (event.type === "keydown" && (event as KeyboardEvent).key !== "Enter") return;
        event.preventDefault();
        event.stopPropagation();
        window.location.href = `/learn/ai-engineer-fde/${moduleLinks[id].id}`;
      };
      document.addEventListener("click", openNode, true);
      document.addEventListener("keydown", openNode, true);
    };
  }, []);

  return <section className={styles.archifyPanel} aria-labelledby="archify-heading">
    <div className={styles.archifyHead}><div><span>ARCHIFY DIAGRAM</span><h2 id="archify-heading">Your learning path</h2></div><p>Select ML foundations, queues, or scale and system design to open the documentation. Other modules are planned.</p></div>
    <iframe ref={connect} title="Clickable AI Engineer and FDE learning roadmap" src="/ai-engineer-roadmap.archify.html" className={styles.archifyFrame} />
  </section>;
}
