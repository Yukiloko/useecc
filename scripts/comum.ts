import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import type { Cena } from "../src/tipos";

export type Provedor = "nenhum" | "elevenlabs" | "arquivos";

export type ArquivoVideo = {
  handle: string;
  narracao: { provedor: Provedor; vozId?: string; modelo?: string };
  cenas: Cena[];
};

export type ConfigCustos = {
  cotacaoDolar: number;
  videosPorMes: number;
  assinaturasMensaisUsd: Record<string, number>;
  elevenlabsUsdPorMilCaracteres: number;
  precoCobradoBrl: number;
};

export const lerJson = <T>(caminho: string): T => JSON.parse(readFileSync(caminho, "utf8"));

export const duracaoAudioSeg = (caminho: string) =>
  Number(
    execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", caminho], {
      encoding: "utf8",
    }).trim(),
  );

export const CSV_HISTORICO = "relatorio/historico.csv";
export const CABECALHO_CSV =
  "data,video,cenas,duracao_video_s,provedor,caracteres_tts,custo_tts_usd,tempo_narracao_s,tempo_render_s,minutos_trabalho";
