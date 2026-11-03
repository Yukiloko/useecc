import { useEffect, useMemo, useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { useWorkspaces } from "./store";
import type { Workspace } from "./types";
import { Overview } from "./views/Overview";
import { Calendar } from "./views/Calendar";
import { Campaigns } from "./views/Campaigns";
import { Customers } from "./views/Customers";
import { Results } from "./views/Results";
import { Playbook } from "./views/Playbook";
import { Businesses } from "./views/Businesses";

const NAV = [
  { id: "visao", label: "Visão geral" },
  { id: "calendario", label: "Calendário" },
  { id: "campanhas", label: "Campanhas" },
  { id: "clientes", label: "Clientes" },
  { id: "resultados", label: "Resultados" },
  { id: "playbook", label: "Playbook" },
  { id: "negocios", label: "Negócios" },
] as const;
const VIEWS = NAV.map((n) => n.id) as string[];
const CUR_KEY = "central-mkt-atual";

function hexRgb(hex: string): [number, number, number] {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  const n = m ? parseInt(m[1], 16) : 0x6b3a22;
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function brandVars(hex: string) {
  const [r, g, b] = hexRgb(hex);
  const lift = (c: number) => Math.round(c + (255 - c) * 0.5);
  return { "--brand-l": `${r} ${g} ${b}`, "--brand-d": `${lift(r)} ${lift(g)} ${lift(b)}` } as React.CSSProperties;
}

const SYNC_LABEL: Record<string, string> = {
  carregando: "Conectando…",
  salvo: "Salvo na central",
  salvando: "Salvando…",
  local: "Salvo só neste navegador",
  erro: "Não foi possível salvar. Recarregue a página.",
};

export default function App() {
  const { list, sync, save, remove } = useWorkspaces();
  const [view, setView] = useState(() => {
    const h = location.hash.slice(1);
    return VIEWS.includes(h) ? h : "visao";
  });
  const [curId, setCurId] = useState<string | null>(() => {
    try { return localStorage.getItem(CUR_KEY); } catch { return null; }
  });

  useEffect(() => {
    const on = () => { const h = location.hash.slice(1); if (VIEWS.includes(h)) setView(h); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const go = (v: string) => {
    setView(v);
    try { history.replaceState(null, "", "#" + v); } catch { location.hash = v; }
    window.scrollTo({ top: 0 });
  };
  const open = (id: string) => {
    setCurId(id);
    try { localStorage.setItem(CUR_KEY, id); } catch { /* ok */ }
  };

  const ws: Workspace | undefined = useMemo(() => list.find((w) => w.id === curId) ?? list[0], [list, curId]);
  const update = (fn: (d: Workspace) => void) => {
    if (!ws) return;
    const d = structuredClone(ws);
    fn(d);
    save(d);
  };
  const loading = sync === "carregando" && !list.length;
  const active = !ws ? "negocios" : view;

  let body: React.ReactNode;
  if (loading) body = <p className="text-sm text-muted-foreground py-20">Carregando seus negócios…</p>;
  else if (!ws || active === "negocios")
    body = (
      <Businesses
        list={list}
        current={ws}
        onCreate={(w) => { save(w); open(w.id); go("playbook"); }}
        onOpen={(id) => { open(id); go("visao"); }}
        onRemove={(id) => { remove(id); if (id === ws?.id) setCurId(null); }}
      />
    );
  else {
    const p = { ws, update, go };
    body = {
      visao: <Overview {...p} />,
      calendario: <Calendar {...p} />,
      campanhas: <Campaigns {...p} />,
      clientes: <Customers {...p} />,
      resultados: <Results key={ws.id} {...p} />,
      playbook: <Playbook {...p} />,
    }[active];
  }

  return (
    <div className="app" style={brandVars(ws?.color ?? "#6B3A22")}>
      <aside className="rail">
        <div className="rail-inner">
          <div className="grid gap-1.5">
            <p className="rail-eyebrow">Central de marketing</p>
            {list.length > 0 ? (
              <select aria-label="Negócio aberto" className="ws-select" value={ws?.id} onChange={(e) => { open(e.target.value); }}>
                {list.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select>
            ) : (
              <p className="font-display text-lg">Nenhum negócio</p>
            )}
            {ws && <p className="text-xs opacity-70 truncate">{ws.vertical}</p>}
          </div>
          <nav aria-label="Seções" className="rail-nav">
            {NAV.map((n) => (
              <button key={n.id} disabled={!ws && n.id !== "negocios"} aria-current={active === n.id ? "page" : undefined} onClick={() => go(n.id)} className="rail-link">
                {n.label}
              </button>
            ))}
          </nav>
          <p className={`rail-sync sync-${sync}`} aria-live="polite">{SYNC_LABEL[sync]}</p>
        </div>
      </aside>
      <main className="main">{body}</main>
      <Toaster position="bottom-right" />
    </div>
  );
}
