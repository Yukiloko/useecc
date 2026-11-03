import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Plus, Gift } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { PageHead, Field, Pill, selectCls, type ViewProps } from "../ui";
import { iso, parseIso } from "../lib/metrics";
import { uid } from "../templates";
import type { Post, PostStatus } from "../types";

export const POST_STATUS: Record<PostStatus, { label: string; tone: string }> = {
  ideia: { label: "Ideia", tone: "neutral" },
  producao: { label: "Em produção", tone: "warn" },
  agendado: { label: "Agendado", tone: "brand" },
  publicado: { label: "Publicado", tone: "good" },
};
const WEEKDAYS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"];

export function Calendar({ ws, update }: ViewProps) {
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1);
  });
  const [edit, setEdit] = useState<Post | null>(null);
  const today = iso(new Date());

  const first = new Date(month);
  const offset = (first.getDay() + 6) % 7;
  const daysIn = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const cells = Array.from({ length: Math.ceil((offset + daysIn) / 7) * 7 }, (_, i) => {
    const day = i - offset + 1;
    return day >= 1 && day <= daysIn ? iso(new Date(month.getFullYear(), month.getMonth(), day)) : null;
  });
  const monthKey = iso(month).slice(0, 7);
  const monthPosts = ws.posts.filter((p) => p.date.startsWith(monthKey)).sort((a, b) => a.date.localeCompare(b.date));
  const dateFor = (d: string) => ws.dates.filter((k) => k.md === d.slice(5));

  const newPost = (date: string): Post => ({
    id: uid(),
    date,
    title: "",
    channelId: ws.channels.find((c) => c.kind === "midia")?.id ?? ws.channels[0]?.id ?? "",
    pillar: ws.pillars[0] ?? "",
    format: ws.formats[0] ?? "",
    status: "ideia",
    notes: "",
  });
  const save = (p: Post) => {
    update((d) => {
      const i = d.posts.findIndex((x) => x.id === p.id);
      if (i >= 0) d.posts[i] = p;
      else d.posts.push(p);
    });
    setEdit(null);
  };
  const del = (id: string) => {
    update((d) => {
      d.posts = d.posts.filter((x) => x.id !== id);
    });
    setEdit(null);
  };

  const pillarCount = ws.pillars.map((p) => ({ p, n: monthPosts.filter((x) => x.pillar === p).length }));
  const maxP = Math.max(1, ...pillarCount.map((x) => x.n));
  const monthLabel = month.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });

  return (
    <div className="grid gap-6">
      <PageHead title={monthLabel.charAt(0).toUpperCase() + monthLabel.slice(1)}>
        <Button variant="outline" size="sm" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() - 1, 1))} aria-label="Mês anterior"><ChevronLeft className="size-4" /></Button>
        <Button variant="outline" size="sm" onClick={() => { const d = new Date(); setMonth(new Date(d.getFullYear(), d.getMonth(), 1)); }}>Hoje</Button>
        <Button variant="outline" size="sm" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() + 1, 1))} aria-label="Próximo mês"><ChevronRight className="size-4" /></Button>
        <Button size="sm" onClick={() => setEdit(newPost(today.startsWith(monthKey) ? today : iso(month)))}>Novo post</Button>
      </PageHead>

      <section className="grid gap-2">
        <h2 className="eyebrow">Posts do mês por pilar ({monthPosts.length} no total)</h2>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          {pillarCount.map(({ p, n }) => (
            <div key={p} className="grid gap-1 min-w-[120px] flex-1 max-w-[220px]">
              <div className="flex justify-between text-xs"><span className="truncate">{p}</span><span className="tabular-nums text-muted-foreground">{n}</span></div>
              <div className="h-1 bg-muted rounded-full"><div className="h-1 bg-brand rounded-full" style={{ width: `${(n / maxP) * 100}%` }} /></div>
            </div>
          ))}
        </div>
      </section>

      <div className="hidden md:grid grid-cols-7 border-l border-t rounded-md overflow-hidden">
        {WEEKDAYS.map((w) => (
          <div key={w} className="border-r border-b px-2 py-1.5 text-xs text-muted-foreground bg-muted/50">{w}</div>
        ))}
        {cells.map((d, i) => (
          <div key={i} className={`border-r border-b min-h-[112px] p-1.5 grid content-start gap-1 ${d ? "bg-card" : "bg-muted/30"}`}>
            {d && (
              <>
                <div className="flex items-center justify-between gap-1">
                  <span className={`text-xs tabular-nums ${d === today ? "bg-primary text-primary-foreground rounded px-1.5" : "text-muted-foreground"}`}>{parseIso(d).getDate()}</span>
                  <button className="text-muted-foreground hover:text-foreground p-0.5 rounded focus-visible:ring-1 ring-ring" onClick={() => setEdit(newPost(d))} aria-label={`Adicionar post em ${d}`}><Plus className="size-3.5" /></button>
                </div>
                {dateFor(d).map((k) => (
                  <span key={k.name} className="text-xs leading-tight text-brand-ink font-medium flex gap-1 items-start"><Gift className="size-3 shrink-0 mt-px" aria-hidden />{k.name}</span>
                ))}
                {ws.posts.filter((p) => p.date === d).map((p) => (
                  <button key={p.id} onClick={() => setEdit(p)} className={`post-chip status-${p.status} text-left`}>
                    <span className="block truncate">{p.title || "Sem título"}</span>
                    <span className="block opacity-75 truncate">{p.format}</span>
                  </button>
                ))}
              </>
            )}
          </div>
        ))}
      </div>

      <ul className="md:hidden grid divide-y border-y">
        {monthPosts.length === 0 && <li className="py-4 text-sm text-muted-foreground">Nenhum post neste mês.</li>}
        {monthPosts.map((p) => (
          <li key={p.id}>
            <button onClick={() => setEdit(p)} className="w-full text-left py-3 flex gap-3 items-start">
              <span className="text-xs tabular-nums w-10 shrink-0 pt-0.5">{parseIso(p.date).getDate()}</span>
              <span className="min-w-0 flex-1 grid gap-1">
                <span className="text-sm truncate">{p.title || "Sem título"}</span>
                <span className="text-xs text-muted-foreground">{p.format}, {p.pillar}</span>
              </span>
              <Pill tone={POST_STATUS[p.status].tone}>{POST_STATUS[p.status].label}</Pill>
            </button>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground items-center">
        Status:
        {Object.entries(POST_STATUS).map(([k, v]) => (
          <Pill key={k} tone={v.tone}>{v.label}</Pill>
        ))}
      </div>

      <PostDialog post={edit} ws={ws} onClose={() => setEdit(null)} onSave={save} onDelete={del} />
    </div>
  );
}

function PostDialog({ post, ws, onClose, onSave, onDelete }: { post: Post | null; ws: ViewProps["ws"]; onClose: () => void; onSave: (p: Post) => void; onDelete: (id: string) => void }) {
  const [p, setP] = useState<Post | null>(post);
  const [lastId, setLastId] = useState<string | null>(null);
  if (post && post.id !== lastId) {
    setLastId(post.id);
    setP(post);
  }
  if (!post && lastId) setLastId(null);
  const exists = post && ws.posts.some((x) => x.id === post.id);
  const set = <K extends keyof Post>(k: K, v: Post[K]) => setP((x) => (x ? { ...x, [k]: v } : x));
  return (
    <Dialog open={!!post} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-display">{exists ? "Editar post" : "Novo post"}</DialogTitle>
        </DialogHeader>
        {p && (
          <form
            className="grid gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              onSave(p);
            }}
          >
            <Field label="Ideia / título" htmlFor="post-title">
              <Input id="post-title" value={p.title} onChange={(e) => set("title", e.target.value)} placeholder="Ex.: Reels do recheio escorrendo" required />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Data" htmlFor="post-date"><Input id="post-date" type="date" value={p.date} onChange={(e) => set("date", e.target.value)} required /></Field>
              <Field label="Status" htmlFor="post-status">
                <select id="post-status" className={selectCls} value={p.status} onChange={(e) => set("status", e.target.value as PostStatus)}>
                  {Object.entries(POST_STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </Field>
              <Field label="Canal" htmlFor="post-channel">
                <select id="post-channel" className={selectCls} value={p.channelId} onChange={(e) => set("channelId", e.target.value)}>
                  {ws.channels.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </Field>
              <Field label="Formato" htmlFor="post-format">
                <select id="post-format" className={selectCls} value={p.format} onChange={(e) => set("format", e.target.value)}>
                  {ws.formats.map((f) => <option key={f}>{f}</option>)}
                </select>
              </Field>
              <Field label="Pilar" htmlFor="post-pillar" className="col-span-2">
                <select id="post-pillar" className={selectCls} value={p.pillar} onChange={(e) => set("pillar", e.target.value)}>
                  {ws.pillars.map((f) => <option key={f}>{f}</option>)}
                </select>
              </Field>
            </div>
            <Field label="Roteiro, legenda ou observações" htmlFor="post-notes">
              <Textarea id="post-notes" rows={4} value={p.notes} onChange={(e) => set("notes", e.target.value)} />
            </Field>
            <DialogFooter className="gap-2 sm:justify-between">
              {exists ? <Button type="button" variant="ghost" className="text-bad" onClick={() => onDelete(p.id)}>Excluir</Button> : <span />}
              <Button type="submit">Salvar post</Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
