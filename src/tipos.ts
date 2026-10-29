export type Icone = "arquivo" | "dinheiro" | "nenhum";

export type Cena = {
  texto: string;
  // Texto falado na narração, se diferente do que aparece na tela.
  fala?: string;
  // Palavras pintadas com a cor de destaque (comparação sem acento/caixa).
  destaque?: string[];
  icone?: Icone;
  // Caminho dentro de public/, preenchido pelo script de narração.
  audio?: string;
  // Duração real do áudio; sem ela a duração é estimada pelo texto.
  duracaoSeg?: number;
};

export type Tema = {
  fundo: string;
  texto: string;
  // Texto falado na narração, se diferente do que aparece na tela.
  fala?: string;
  destaque: string;
};

export type PropsVideo = {
  handle: string;
  cenas: Cena[];
  tema?: Tema;
};

export const TEMA_PADRAO: Tema = {
  fundo: "#EFE8DC",
  texto: "#1F1A14",
  destaque: "#C2410C",
};
