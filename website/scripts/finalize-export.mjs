import { copyFile } from "node:fs/promises";
await copyFile(new URL("../public/marketing.html", import.meta.url), new URL("../out/index.html", import.meta.url));
console.log("Exported the public marketing page at /");
