import { useCallback, useEffect, useRef, useState } from "react";
import type { Workspace } from "./types";
import { normalizeWorkspace } from "./templates";

type SyncState = "carregando" | "salvo" | "salvando" | "local" | "erro";
const LS_KEY = "central-mkt-workspaces";

declare global {
  interface Window {
    claude?: { use: (name: string) => Promise<any> };
  }
}

function lsRead(): Workspace[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? (JSON.parse(raw) as Workspace[]).map(normalizeWorkspace) : [];
  } catch {
    return [];
  }
}
function lsWrite(list: Workspace[]) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(list));
  } catch {
    /* sem armazenamento local */
  }
}

/**
 * Cada negócio é um documento em `workspaces/<id>` no banco compartilhado do artifact.
 * Sem banco disponível (fora do claude.ai), cai para o navegador deste aparelho.
 */
export function useWorkspaces() {
  const [list, setList] = useState<Workspace[]>([]);
  const [sync, setSync] = useState<SyncState>("carregando");
  const dbRef = useRef<any>(null);
  const timers = useRef<Record<string, number>>({});
  const pending = useRef<Record<string, Workspace>>({});

  useEffect(() => {
    let unsub: (() => void) | undefined;
    let done = false;
    const fallback = () => {
      if (done) return;
      done = true;
      setList(lsRead());
      setSync("local");
    };
    const timer = window.setTimeout(fallback, 10000);
    const start = async () => {
      const db = window.claude ? await window.claude.use("db").catch(() => null) : null;
      if (!db) {
        window.clearTimeout(timer);
        fallback();
        return;
      }
      dbRef.current = db;
      unsub = db.collection("workspaces").onSnapshot(
        (snap: any) => {
          window.clearTimeout(timer);
          done = true;
          const rows = snap.docs.filter((d: any) => d.exists).map((d: any) => normalizeWorkspace(structuredClone(d.data()) as Workspace));
          rows.sort((a: Workspace, b: Workspace) => a.createdAt.localeCompare(b.createdAt));
          // mantém edições locais que ainda não foram gravadas
          setList(rows.map((r: Workspace) => pending.current[r.id] ?? r));
          setSync(Object.keys(pending.current).length ? "salvando" : "salvo");
        },
        () => {
          window.clearTimeout(timer);
          dbRef.current = null;
          fallback();
        },
      );
    };
    start();
    return () => {
      window.clearTimeout(timer);
      unsub?.();
    };
  }, []);

  const flush = useCallback(async (id: string) => {
    const ws = pending.current[id];
    if (!ws) return;
    const db = dbRef.current;
    try {
      await db.doc("workspaces/" + id).set(JSON.parse(JSON.stringify(ws)));
      if (pending.current[id] === ws) delete pending.current[id];
      setSync(Object.keys(pending.current).length ? "salvando" : "salvo");
    } catch (e: any) {
      if (e?.code === "unavailable") {
        window.setTimeout(() => flush(id), 1500 + Math.random() * 1000);
      } else setSync("erro");
    }
  }, []);

  const save = useCallback(
    (ws: Workspace) => {
      setList((prev) => {
        const exists = prev.some((w) => w.id === ws.id);
        const next = exists ? prev.map((w) => (w.id === ws.id ? ws : w)) : [...prev, ws];
        if (!dbRef.current) lsWrite(next);
        return next;
      });
      if (dbRef.current) {
        pending.current[ws.id] = ws;
        setSync("salvando");
        window.clearTimeout(timers.current[ws.id]);
        timers.current[ws.id] = window.setTimeout(() => flush(ws.id), 700);
      }
    },
    [flush],
  );

  const remove = useCallback(async (id: string) => {
    setList((prev) => {
      const next = prev.filter((w) => w.id !== id);
      if (!dbRef.current) lsWrite(next);
      return next;
    });
    delete pending.current[id];
    if (dbRef.current) {
      try {
        await dbRef.current.doc("workspaces/" + id).delete();
      } catch {
        setSync("erro");
      }
    }
  }, []);

  return { list, sync, save, remove };
}
