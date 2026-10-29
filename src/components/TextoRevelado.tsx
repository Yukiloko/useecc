import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

const normalizar = (s: string) =>
  s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\w]/g, "").toLowerCase();

// Revela palavra por palavra saindo do desfoque, distribuído pela primeira
// parte da cena para acompanhar a fala.
export const TextoRevelado: React.FC<{
  texto: string;
  destaque: string[];
  cor: string;
  corDestaque: string;
}> = ({ texto, destaque, cor, corDestaque }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const palavras = texto.split(/\s+/).filter(Boolean);
  const alvo = new Set(destaque.map(normalizar));

  const janela = durationInFrames * 0.7;
  const passo = palavras.length > 1 ? janela / palavras.length : 0;
  const duracaoPalavra = 8;

  return (
    <div style={{ fontSize: 92, fontWeight: 800, lineHeight: 1.12, letterSpacing: -2, color: cor }}>
      {palavras.map((palavra, i) => {
        const p = interpolate(frame - i * passo, [0, duracaoPalavra], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              marginRight: "0.28em",
              opacity: p,
              filter: `blur(${(1 - p) * 14}px)`,
              transform: `translateY(${(1 - p) * 24}px)`,
              color: alvo.has(normalizar(palavra)) ? corDestaque : cor,
            }}
          >
            {palavra}
          </span>
        );
      })}
    </div>
  );
};
