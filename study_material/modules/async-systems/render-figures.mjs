import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const target = join(root, "assets");
await mkdir(target, { recursive: true });

const palette = {
  blue: { ink: "#1466b2", pale: "#e8f3ff", border: "#aed5f4" },
  teal: { ink: "#087f79", pale: "#e4f7f3", border: "#a9ddd4" },
  violet: { ink: "#7152ba", pale: "#f1ecfc", border: "#cec1ee" },
  amber: { ink: "#a35d0c", pale: "#fff4df", border: "#f0d39b" },
  rose: { ink: "#b3445f", pale: "#fff0f3", border: "#f1bac9" },
};

const icons = {
  user: '<circle cx="18" cy="13" r="5"/><path d="M7 29c1-6 5-9 11-9s10 3 11 9"/>',
  api: '<rect x="5" y="7" width="26" height="22" rx="4"/><path d="M5 13h26M11 20h5m-5 5h9"/>',
  queue: '<rect x="6" y="7" width="24" height="6" rx="2"/><rect x="6" y="16" width="24" height="6" rx="2"/><rect x="6" y="25" width="24" height="6" rx="2"/>',
  worker: '<rect x="6" y="8" width="24" height="20" rx="4"/><path d="M13 17l-3 3 3 3m10-6 3 3-3 3M17 25l3-10"/>',
  file: '<path d="M10 5h11l6 6v19H10zM21 5v6h6M14 18h9m-9 5h9"/>',
  database: '<ellipse cx="18" cy="9" rx="11" ry="4"/><path d="M7 9v18c0 2 5 4 11 4s11-2 11-4V9M7 18c0 2 5 4 11 4s11-2 11-4"/>',
  clock: '<circle cx="18" cy="18" r="12"/><path d="M18 10v9l6 4"/>',
  shield: '<path d="M18 4 29 9v9c0 8-5 12-11 15C12 30 7 26 7 18V9zM13 18l4 4 7-8"/>',
  alert: '<path d="M18 5 32 30H4zM18 14v7m0 5h.01"/>',
  bell: '<path d="M10 25h16l-2-4v-7a6 6 0 0 0-12 0v7zM15 29a3 3 0 0 0 6 0"/>',
  chart: '<path d="M6 29V7m0 22h25M11 24l6-7 5 3 8-11"/>',
  refresh: '<path d="M29 13a11 11 0 0 0-19-4L6 13m0-7v7h7M7 23a11 11 0 0 0 19 4l4-4m0 7v-7h-7"/>',
  network: '<circle cx="7" cy="18" r="3"/><circle cx="28" cy="8" r="3"/><circle cx="28" cy="28" r="3"/><path d="m10 17 15-8M10 19l15 8"/>',
};

function escape(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function icon(name, x, y, color) {
  return `<g transform="translate(${x} ${y})" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${icons[name]}</g>`;
}

function card(node) {
  const { x, y, title, detail, tone = "blue", glyph = "queue", w = 188 } = node;
  const color = palette[tone];
  return `<g role="group" aria-label="${escape(title)}: ${escape(detail)}">
    <rect x="${x}" y="${y}" width="${w}" height="78" rx="13" fill="#fff" stroke="${color.border}" stroke-width="1.5" filter="url(#shadow)"/>
    <rect x="${x}" y="${y}" width="5" height="78" rx="2.5" fill="${color.ink}"/>
    <rect x="${x + 13}" y="${y + 17}" width="44" height="44" rx="11" fill="${color.pale}"/>
    <g transform="translate(${x + 17} ${y + 21}) scale(1)">${icon(glyph, 0, 0, color.ink)}</g>
    <text x="${x + 67}" y="${y + 32}" class="node-title">${escape(title)}</text>
    <text x="${x + 67}" y="${y + 53}" class="node-detail">${escape(detail)}</text>
  </g>`;
}

function path(edge) {
  const color = palette[edge.tone ?? "blue"].ink;
  return `<path d="${edge.d}" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"${edge.noArrow ? "" : ` marker-end="url(#arrow-${edge.tone ?? "blue"})"`}/>`;
}

function label(item) {
  return `<g><rect x="${item.x}" y="${item.y}" width="${item.w}" height="25" rx="12.5" fill="${palette[item.tone ?? "blue"].pale}"/><text x="${item.x + item.w / 2}" y="${item.y + 17}" text-anchor="middle" class="edge-label" fill="${palette[item.tone ?? "blue"].ink}">${escape(item.text)}</text></g>`;
}

function figure(spec) {
  const markers = Object.entries(palette).map(([name, color]) => `<marker id="arrow-${name}" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M1 1.5 8 4.5 1 7.5" fill="none" stroke="${color.ink}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></marker>`).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="920" height="402" viewBox="0 0 920 402" role="img" aria-labelledby="title desc">
    <title id="title">${escape(spec.title)}</title><desc id="desc">${escape(spec.description)}</desc>
    <defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#dbe7f4" stroke-width=".65"/></pattern><filter id="shadow" x="-20%" y="-30%" width="140%" height="160%"><feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#1e3b58" flood-opacity=".09"/></filter>${markers}</defs>
    <style>.kicker{font:700 12px ui-monospace,Menlo,monospace;letter-spacing:1.4px;fill:#3975a8}.heading{font:750 25px Inter,Arial,sans-serif;letter-spacing:-.6px;fill:#142a42}.subtitle{font:400 13px Inter,Arial,sans-serif;fill:#60758c}.node-title{font:700 14px Inter,Arial,sans-serif;fill:#18334d}.node-detail{font:400 11px Inter,Arial,sans-serif;fill:#61778e}.edge-label{font:700 10px Inter,Arial,sans-serif}.note{font:600 13px Inter,Arial,sans-serif;fill:#28516e}.note-key{font:800 10px ui-monospace,Menlo,monospace;letter-spacing:1px;fill:#2676af}</style>
    <rect width="920" height="402" rx="18" fill="#f7faff"/><rect x="1" y="1" width="918" height="400" rx="17" fill="none" stroke="#cbdff1" stroke-width="2"/>
    <rect x="18" y="18" width="884" height="310" rx="12" fill="url(#grid)" opacity=".8"/>
    <text x="38" y="43" class="kicker">SYSTEMS / QUEUES</text>
    <text x="38" y="77" class="heading">${escape(spec.title)}</text>
    <text x="38" y="100" class="subtitle">${escape(spec.subtitle)}</text>
    ${spec.edges.map(path).join("")}
    ${(spec.labels ?? []).map(label).join("")}
    ${spec.nodes.map(card).join("")}
    <rect x="28" y="342" width="864" height="43" rx="9" fill="#e9f3fb"/>
    <text x="43" y="368" class="note-key">KEY IDEA</text><text x="125" y="368" class="note">${escape(spec.note)}</text>
  </svg>`;
}

const figures = [
  {
    file: "queue-basics.svg", title: "What a queue does", subtitle: "A job waits safely until a worker is ready.",
    description: "A user request reaches an API producer, which sends an export job to a queue. A worker consumes it and stores a completed file.",
    nodes: [
      { x: 28, y: 170, title: "User request", detail: "Export document", glyph: "user" },
      { x: 254, y: 170, title: "Producer", detail: "API creates a job", glyph: "api", tone: "blue" },
      { x: 480, y: 170, title: "Queue", detail: "Work waits here", glyph: "queue", tone: "violet" },
      { x: 706, y: 170, title: "Worker", detail: "Creates the file", glyph: "worker", tone: "teal" },
    ],
    edges: [{ d: "M216 209H248" }, { d: "M442 209H474", tone: "violet" }, { d: "M668 209H700", tone: "teal" }],
    labels: [{ x: 279, y: 272, w: 133, text: "responds early" }, { x: 513, y: 272, w: 119, text: "holds the job", tone: "violet" }],
    note: "The queue transports work; a separate status record tells the user the result.",
  },
  {
    file: "acceptance.svg", title: "Acceptance is a promise", subtitle: "Respond after durable intent, then complete the effect.",
    description: "The API records an export operation, returns 202 with an ID, then a queue delivers the job to a worker that creates a file.",
    nodes: [
      { x: 28, y: 145, title: "API", detail: "Validate request", glyph: "api" },
      { x: 254, y: 145, title: "Operation", detail: "Durable status row", glyph: "database", tone: "violet" },
      { x: 480, y: 145, title: "Queue", detail: "Deliver job", glyph: "queue", tone: "amber" },
      { x: 706, y: 145, title: "Worker", detail: "Create file", glyph: "worker", tone: "teal" },
      { x: 28, y: 255, title: "202 + ID", detail: "Check progress later", glyph: "file", tone: "blue" },
      { x: 706, y: 255, title: "Result", detail: "Completed status", glyph: "file", tone: "teal" },
    ],
    edges: [{ d: "M216 184H248" }, { d: "M442 184H474", tone: "violet" }, { d: "M668 184H700", tone: "amber" }, { d: "M122 223V249" }, { d: "M800 223V249", tone: "teal" }],
    note: "A 202 response means the operation can be found later; it does not mean the file exists.",
  },
  {
    file: "backpressure.svg", title: "When arrivals outrun workers", subtitle: "A buffer buys time; it does not create processing capacity.",
    description: "Requests arrive at 120 jobs per minute, while workers finish 90 per minute, so the queue grows by 30 per minute.",
    nodes: [
      { x: 28, y: 162, title: "Arrivals", detail: "120 jobs / minute", glyph: "api", tone: "blue" },
      { x: 254, y: 162, title: "Backlog", detail: "+30 jobs / minute", glyph: "queue", tone: "amber" },
      { x: 480, y: 162, title: "Workers", detail: "90 jobs / minute", glyph: "worker", tone: "teal" },
      { x: 706, y: 162, title: "File store", detail: "Capacity limit", glyph: "database", tone: "violet" },
    ],
    edges: [{ d: "M216 201H248" }, { d: "M442 201H474", tone: "amber" }, { d: "M668 201H700", tone: "teal" }],
    labels: [{ x: 302, y: 259, w: 92, text: "20 min → 600", tone: "amber" }],
    note: "Watch the age of the oldest job; adding workers may overload the file store.",
  },
  {
    file: "retries.svg", title: "Retry, then quarantine", subtitle: "Classify the failure and limit the attempt budget.",
    description: "A claimed job calls a dependency. Success persists a result. Transient failure retries with backoff; repeated failure enters a dead-letter queue.",
    nodes: [
      { x: 28, y: 148, title: "Claim job", detail: "Start attempt", glyph: "worker" },
      { x: 254, y: 148, title: "Call store", detail: "Bounded timeout", glyph: "database", tone: "violet" },
      { x: 480, y: 148, title: "Success", detail: "Persist + ack", glyph: "shield", tone: "teal" },
      { x: 254, y: 253, title: "Retry", detail: "Backoff + jitter", glyph: "refresh", tone: "amber" },
      { x: 480, y: 253, title: "DLQ", detail: "Inspect cause", glyph: "alert", tone: "rose" },
      { x: 706, y: 253, title: "Replay", detail: "Fix, then review", glyph: "shield", tone: "violet" },
    ],
    edges: [{ d: "M216 187H248" }, { d: "M442 187H474", tone: "teal" }, { d: "M348 226V247", tone: "amber" }, { d: "M254 292H231V247H122V232", tone: "amber" }, { d: "M442 292H474", tone: "rose" }, { d: "M668 292H700", tone: "violet" }],
    note: "A timeout leaves the outcome uncertain; check for an existing effect before replay.",
  },
  {
    file: "idempotency.svg", title: "A duplicate delivery", subtitle: "One logical operation may be delivered more than once.",
    description: "Worker A completes a result but loses acknowledgement. The queue redelivers the same operation to Worker B, which sees the result and only acknowledges.",
    nodes: [
      { x: 28, y: 158, title: "Worker A", detail: "Processes exp_82", glyph: "worker" },
      { x: 254, y: 158, title: "Result exists", detail: "One export file", glyph: "file", tone: "teal" },
      { x: 480, y: 158, title: "Ack lost", detail: "Message returns", glyph: "alert", tone: "amber" },
      { x: 706, y: 158, title: "Worker B", detail: "Checks exp_82", glyph: "worker", tone: "violet" },
      { x: 706, y: 259, title: "Ack only", detail: "No second file", glyph: "shield", tone: "teal" },
    ],
    edges: [{ d: "M216 197H248", tone: "teal" }, { d: "M442 197H474", tone: "amber" }, { d: "M668 197H700", tone: "violet" }, { d: "M800 236V253", tone: "teal" }],
    note: "Use a stable operation ID and check the durable effect before repeating work.",
  },
  {
    file: "outbox-events.svg", title: "Commit, then publish", subtitle: "The outbox preserves intent across a database and broker.",
    description: "An API commits business state and an outbox row together. A relay publishes to a broker, which reaches an export worker and other event subscribers.",
    nodes: [
      { x: 28, y: 160, title: "API", detail: "Accept export", glyph: "api" },
      { x: 254, y: 160, title: "DB + outbox", detail: "One transaction", glyph: "database", tone: "violet" },
      { x: 480, y: 160, title: "Relay", detail: "Publish pending", glyph: "refresh", tone: "amber" },
      { x: 706, y: 160, title: "Broker", detail: "Deliver event", glyph: "queue", tone: "teal" },
      { x: 706, y: 259, title: "Subscribers", detail: "Worker + audit", glyph: "network", tone: "blue" },
    ],
    edges: [{ d: "M216 199H248" }, { d: "M442 199H474", tone: "violet" }, { d: "M668 199H700", tone: "amber" }, { d: "M800 238V253", tone: "teal" }],
    note: "A relay may publish twice after a crash; each subscriber must handle duplicates.",
  },
  {
    file: "delivery-channels.svg", title: "One result, several channels", subtitle: "Choose updates by recipient and direction.",
    description: "Browser polling asks a durable status store for the result; the same store pushes server-sent events and signed partner webhooks.",
    nodes: [
      { x: 28, y: 170, title: "Status", detail: "Durable result", glyph: "database", tone: "violet" },
      { x: 254, y: 170, title: "Polling", detail: "Browser asks", glyph: "api" },
      { x: 480, y: 170, title: "SSE", detail: "Server pushes", glyph: "network", tone: "teal" },
      { x: 706, y: 170, title: "Webhook", detail: "Signed POST", glyph: "bell", tone: "amber" },
    ],
    edges: [{ d: "M122 170V137H800", tone: "violet", noArrow: true }, { d: "M254 209H222" }, { d: "M574 137V164", tone: "teal" }, { d: "M800 137V164", tone: "amber" }],
    note: "Polling reads durable state; pushed updates can be missed and must be recoverable.",
  },
  {
    file: "operations.svg", title: "Signals to action", subtitle: "Measure user-visible progress and choose a safe response.",
    description: "Queue age, operation age, and dead-letter count lead to triage. Operators can limit intake or isolate and replay a poison job.",
    nodes: [
      { x: 28, y: 170, title: "Signals", detail: "Age, errors, DLQ", glyph: "chart" },
      { x: 254, y: 170, title: "Triage", detail: "Find the boundary", glyph: "alert", tone: "amber" },
      { x: 480, y: 125, title: "Overload", detail: "Limit intake", glyph: "shield", tone: "violet" },
      { x: 480, y: 260, title: "Poison job", detail: "Isolate + fix", glyph: "alert", tone: "rose" },
      { x: 706, y: 170, title: "Recovery", detail: "Verify results", glyph: "refresh", tone: "teal" },
    ],
    edges: [{ d: "M216 209H248" }, { d: "M442 190L474 168", tone: "violet" }, { d: "M442 228L474 282", tone: "rose" }, { d: "M668 164L700 191", tone: "teal" }, { d: "M668 295L700 225", tone: "teal" }],
    note: "Use operation state for exact outcomes; broker counts are approximate signals.",
  },
];

for (const spec of figures) {
  await writeFile(join(target, spec.file), figure(spec));
  console.log(`Rendered ${spec.file}`);
}

await writeFile(join(target, "queue-mark.svg"), `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96" role="img" aria-label="Queue module mark"><rect width="96" height="96" rx="24" fill="#e9f3ff"/><rect x="19" y="23" width="58" height="12" rx="5" fill="#1466b2"/><rect x="19" y="43" width="48" height="12" rx="5" fill="#7152ba"/><rect x="19" y="63" width="38" height="12" rx="5" fill="#087f79"/><path d="M70 49v23m0 0-8-8m8 8 8-8" fill="none" stroke="#087f79" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
console.log("Rendered queue-mark.svg");
