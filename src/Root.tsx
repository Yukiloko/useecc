import { Composition } from "remotion";
import exemplo from "../videos/exemplo.json";
import { FPS, framesDaCena } from "./duracao";
import { TextoAnimado } from "./TextoAnimado";
import type { PropsVideo } from "./tipos";

const propsExemplo: PropsVideo = { handle: exemplo.handle, cenas: exemplo.cenas as PropsVideo["cenas"] };

export const Root: React.FC = () => (
  <Composition
    id="TextoAnimado"
    component={TextoAnimado}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={1}
    defaultProps={propsExemplo}
    calculateMetadata={({ props }) => ({
      durationInFrames: props.cenas.reduce((total, cena) => total + framesDaCena(cena), 0),
    })}
  />
);
