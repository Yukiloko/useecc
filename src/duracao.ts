import type { Cena } from "./tipos";

export const FPS = 30;
// Respiro depois da fala antes de trocar de cena.
const FOLGA_SEG = 0.5;

export const estimarSegundos = (texto: string) => {
  const palavras = texto.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1.5, palavras / 2.6);
};

export const framesDaCena = (cena: Cena) =>
  Math.ceil(((cena.duracaoSeg ?? estimarSegundos(cena.texto)) + FOLGA_SEG) * FPS);
