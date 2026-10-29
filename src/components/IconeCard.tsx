import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Icone } from "../tipos";

const desenhos: Record<Exclude<Icone, "nenhum">, React.ReactNode> = {
  arquivo: (
    <>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
    </>
  ),
  dinheiro: (
    <>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <circle cx="12" cy="12" r="2.5" />
    </>
  ),
};

export const IconeCard: React.FC<{ icone: Icone; cor: string }> = ({ icone, cor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (icone === "nenhum") return null;

  const entrada = spring({ frame, fps, config: { damping: 12 } });
  return (
    <div
      style={{
        width: 150,
        height: 150,
        borderRadius: 36,
        background: "white",
        boxShadow: "0 18px 40px rgba(0,0,0,0.10)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${entrada}) rotate(${(1 - entrada) * -12}deg)`,
        marginBottom: 70,
      }}
    >
      <svg width="76" height="76" viewBox="0 0 24 24" fill="none" stroke={cor} strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round">
        {desenhos[icone]}
      </svg>
    </div>
  );
};
