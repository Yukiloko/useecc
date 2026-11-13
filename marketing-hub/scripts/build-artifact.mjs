// Gera um único HTML (fragmento de página) a partir do build do Vite, pronto para publicar como Artifact.
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
const dir = "dist/assets";
const files = readdirSync(dir);
const css = files.filter((f) => f.endsWith(".css")).map((f) => readFileSync(`${dir}/${f}`, "utf8")).join("\n");
const js = files.filter((f) => f.endsWith(".js")).map((f) => readFileSync(`${dir}/${f}`, "utf8")).join("\n");
const safe = (s) => s.replace(/<\/(script|style)/gi, "<\\/$1");
const html = `<meta charset="utf-8">
<title>Central de Marketing</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..700&family=Figtree:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>${safe(css)}</style>
<div id="root"></div>
<script type="module">${safe(js)}</script>
`;
writeFileSync("artifact/central-de-marketing.html", html);
console.log("artifact/central-de-marketing.html", (html.length / 1024).toFixed(0) + " KB");
