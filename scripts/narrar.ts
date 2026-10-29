import { createHash } from "node:crypto";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { estimarSegundos } from "../src/duracao";
import type { Cena } from "../src/tipos";
import { duracaoAudioSeg, lerJson, type ArquivoVideo } from "./comum";

export type ResultadoNarracao = {
  cenas: Cena[];
  // Caracteres efetivamente enviados ao TTS (áudios em cache não contam).
  caracteresTts: number;
};

const gerarElevenLabs = async (texto: string, vozId: string, modelo: string, destino: string) => {
  const chave = process.env.ELEVENLABS_API_KEY;
  if (!chave) throw new Error("Defina ELEVENLABS_API_KEY (veja .env.example).");
  const resposta = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${vozId}?output_format=mp3_44100_128`,
    {
      method: "POST",
      headers: { "xi-api-key": chave, "Content-Type": "application/json" },
      body: JSON.stringify({ text: texto, model_id: modelo }),
    },
  );
  if (!resposta.ok) throw new Error(`ElevenLabs ${resposta.status}: ${await resposta.text()}`);
  writeFileSync(destino, Buffer.from(await resposta.arrayBuffer()));
};

export const narrar = async (slug: string): Promise<ResultadoNarracao> => {
  const video = lerJson<ArquivoVideo>(`videos/${slug}.json`);
  const { provedor, vozId = "", modelo = "eleven_multilingual_v2" } = video.narracao;
  const pasta = path.join("public", "audio", slug);
  mkdirSync(pasta, { recursive: true });

  let caracteresTts = 0;
  const cenas: Cena[] = [];
  for (const [i, cena] of video.cenas.entries()) {
    const fala = cena.fala ?? cena.texto;

    if (provedor === "nenhum") {
      cenas.push({ ...cena, duracaoSeg: estimarSegundos(fala) });
      continue;
    }

    let arquivo: string;
    if (provedor === "elevenlabs") {
      if (!vozId) throw new Error(`videos/${slug}.json: preencha narracao.vozId`);
      // O hash no nome evita pagar de novo por uma fala que não mudou.
      const hash = createHash("sha1").update(`${vozId}|${modelo}|${fala}`).digest("hex").slice(0, 8);
      arquivo = `cena-${i + 1}-${hash}.mp3`;
      if (!existsSync(path.join(pasta, arquivo))) {
        await gerarElevenLabs(fala, vozId, modelo, path.join(pasta, arquivo));
        caracteresTts += fala.length;
      }
    } else {
      // "arquivos": você grava ou exporta de qualquer ferramenta e coloca aqui.
      arquivo = `cena-${i + 1}.mp3`;
      if (!existsSync(path.join(pasta, arquivo))) throw new Error(`Faltando ${path.join(pasta, arquivo)}`);
    }

    cenas.push({
      ...cena,
      audio: `audio/${slug}/${arquivo}`,
      duracaoSeg: duracaoAudioSeg(path.join(pasta, arquivo)),
    });
  }
  return { cenas, caracteresTts };
};

if (import.meta.url === `file://${process.argv[1]}`) {
  const slug = process.argv[2] ?? "exemplo";
  const { cenas, caracteresTts } = await narrar(slug);
  for (const [i, c] of cenas.entries()) console.log(`cena ${i + 1}: ${c.duracaoSeg?.toFixed(2)}s ${c.audio ?? "(sem áudio)"}`);
  console.log(`caracteres enviados ao TTS: ${caracteresTts}`);
}
