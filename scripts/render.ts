import { execFileSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { FPS, framesDaCena } from "../src/duracao";
import type { PropsVideo } from "../src/tipos";
import { CABECALHO_CSV, CSV_HISTORICO, lerJson, type ArquivoVideo, type ConfigCustos } from "./comum";
import { narrar } from "./narrar";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { minutos: { type: "string", default: "" } },
});
const slug = positionals[0] ?? "exemplo";
const video = lerJson<ArquivoVideo>(`videos/${slug}.json`);
const config = lerJson<ConfigCustos>("custos.config.json");

const t0 = performance.now();
const { cenas, caracteresTts } = await narrar(slug);
const tempoNarracao = (performance.now() - t0) / 1000;

mkdirSync("out", { recursive: true });
const props: PropsVideo = { handle: video.handle, cenas };
const arquivoProps = `out/${slug}.props.json`;
writeFileSync(arquivoProps, JSON.stringify(props, null, 2));

const t1 = performance.now();
execFileSync("npx", ["remotion", "render", "src/index.ts", "TextoAnimado", `out/${slug}.mp4`, `--props=${arquivoProps}`], {
  stdio: "inherit",
});
const tempoRender = (performance.now() - t1) / 1000;

const duracaoVideo = cenas.reduce((t, c) => t + framesDaCena(c), 0) / FPS;
const custoTts = video.narracao.provedor === "elevenlabs" ? (caracteresTts / 1000) * config.elevenlabsUsdPorMilCaracteres : 0;

mkdirSync("relatorio", { recursive: true });
if (!existsSync(CSV_HISTORICO)) appendFileSync(CSV_HISTORICO, CABECALHO_CSV + "\n");
appendFileSync(
  CSV_HISTORICO,
  [
    new Date().toISOString(),
    slug,
    cenas.length,
    duracaoVideo.toFixed(1),
    video.narracao.provedor,
    caracteresTts,
    custoTts.toFixed(4),
    tempoNarracao.toFixed(1),
    tempoRender.toFixed(1),
    values.minutos,
  ].join(",") + "\n",
);

console.log(`\nout/${slug}.mp4 — ${duracaoVideo.toFixed(1)}s de vídeo`);
console.log(`narração ${tempoNarracao.toFixed(1)}s, render ${tempoRender.toFixed(1)}s, TTS US$ ${custoTts.toFixed(4)}`);
if (!values.minutos) console.log("Dica: passe --minutos N com o tempo que você gastou (roteiro + Claude + ajustes).");
