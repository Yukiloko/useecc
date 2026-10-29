import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { IconeCard } from "./components/IconeCard";
import { TextoRevelado } from "./components/TextoRevelado";
import { framesDaCena } from "./duracao";
import { TEMA_PADRAO, type Cena, type PropsVideo, type Tema } from "./tipos";

const FADE = 8;

const CenaView: React.FC<{ cena: Cena; tema: Tema }> = ({ cena, tema }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const saida = interpolate(frame, [durationInFrames - FADE, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ padding: "0 110px", justifyContent: "center", opacity: saida }}>
      <IconeCard icone={cena.icone ?? "nenhum"} cor={tema.texto} />
      <TextoRevelado texto={cena.texto} destaque={cena.destaque ?? []} cor={tema.texto} corDestaque={tema.destaque} />
      {cena.audio && <Audio src={staticFile(cena.audio)} />}
    </AbsoluteFill>
  );
};

export const TextoAnimado: React.FC<PropsVideo> = ({ handle, cenas, tema = TEMA_PADRAO }) => {
  let inicio = 0;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 40%, rgba(255,255,255,0.75), transparent 60%), ${tema.fundo}`,
        fontFamily: "Inter, 'Helvetica Neue', Arial, sans-serif",
      }}
    >
      <div style={{ position: "absolute", top: 380, right: 90, fontSize: 30, color: tema.texto, opacity: 0.35 }}>
        @{handle}
      </div>
      {cenas.map((cena, i) => {
        const duracao = framesDaCena(cena);
        const seq = (
          <Sequence key={i} from={inicio} durationInFrames={duracao}>
            <CenaView cena={cena} tema={tema} />
          </Sequence>
        );
        inicio += duracao;
        return seq;
      })}
    </AbsoluteFill>
  );
};
