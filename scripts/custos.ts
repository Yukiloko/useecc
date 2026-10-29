import { existsSync, readFileSync } from "node:fs";
import { CSV_HISTORICO, lerJson, type ConfigCustos } from "./comum";

const config = lerJson<ConfigCustos>("custos.config.json");
if (!existsSync(CSV_HISTORICO)) {
  console.log(`Nada em ${CSV_HISTORICO} ainda. Rode "npm run render -- <video>" primeiro.`);
  process.exit(0);
}

const [cabecalho, ...linhas] = readFileSync(CSV_HISTORICO, "utf8").trim().split("\n");
const colunas = cabecalho.split(",");
const registros = linhas.map((l) => Object.fromEntries(l.split(",").map((v, i) => [colunas[i], v])));

const media = (campo: string) => {
  const valores = registros.map((r) => r[campo]).filter((v) => v !== "").map(Number);
  return valores.length ? valores.reduce((a, b) => a + b, 0) / valores.length : undefined;
};

const brl = (usd: number) => `R$ ${(usd * config.cotacaoDolar).toFixed(2)}`;
const assinaturas = Object.values(config.assinaturasMensaisUsd).reduce((a, b) => a + b, 0);
const fixoPorVideo = assinaturas / config.videosPorMes;
const ttsPorVideo = media("custo_tts_usd") ?? 0;
const custoPorVideo = fixoPorVideo + ttsPorVideo;
const margem = config.precoCobradoBrl - custoPorVideo * config.cotacaoDolar;
const minutos = media("minutos_trabalho");

console.log(`Renders registrados: ${registros.length}`);
console.log(`Duração média do vídeo: ${media("duracao_video_s")?.toFixed(1)}s`);
console.log(`Tempo médio de máquina: narração ${media("tempo_narracao_s")?.toFixed(1)}s + render ${media("tempo_render_s")?.toFixed(1)}s`);
console.log("");
console.log(`Assinaturas: US$ ${assinaturas}/mês ÷ ${config.videosPorMes} vídeos = ${brl(fixoPorVideo)} por vídeo`);
console.log(`TTS por uso (média): ${brl(ttsPorVideo)} por vídeo`);
console.log(`Custo por vídeo: ${brl(custoPorVideo)}`);
console.log(`Cobrando R$ ${config.precoCobradoBrl}: margem de R$ ${margem.toFixed(2)} por vídeo (antes de imposto)`);
if (minutos) {
  console.log(`Seu tempo médio: ${minutos.toFixed(0)} min → R$ ${((margem / minutos) * 60).toFixed(2)} por hora trabalhada`);
} else {
  console.log("Sem tempo de trabalho registrado; use --minutos no render para ver R$/hora.");
}
