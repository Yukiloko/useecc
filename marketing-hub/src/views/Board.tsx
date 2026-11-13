import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { PageHead, Empty, type ViewProps } from "../ui";
import { fmtDay, iso } from "../lib/metrics";
import type { Post, PostStatus } from "../types";
import { POST_STATUS, PostEditor, STATUS_ORDER, newPost, progress } from "./PostEditor";

const COLUMN_HINT: Record<PostStatus, string> = {
  ideia: "Ainda sem roteiro",
  producao: "Gravando, editando ou escrevendo",
  agendado: "Pronto, com data e hora",
  publicado: "Últimos 14 dias",
};

export function Board({ ws, update }: ViewProps) {
  const [edit, setEdit] = useState<Post | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);
  const [over, setOver] = useState<PostStatus | null>(null);
  const today = iso(new Date());
  const twoWeeksAgo = iso(new Date(Date.now() - 14 * 864e5));

  const save = (p: Post) => {
    update((d) => {
      const i = d.posts.findIndex((x) => x.id === p.id);
      if (i >= 0) d.posts[i] = p;
      else d.posts.push(p);
    });
    setEdit(null);
  };
  const move = (id: string, status: PostStatus) =>
    update((d) => {
      const p = d.posts.find((x) => x.id === id);
      if (p) p.status = status;
    });

  const cols = STATUS_ORDER.map((s) => ({
    s,
    posts: ws.posts
      .filter((p) => p.status === s && (s !== "publicado" || p.date >= twoWeeksAgo))
      .sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time)),
  }));
  const late = ws.posts.filter((p) => p.date < today && p.status !== "publicado");
  const weekEnd = iso(new Date(Date.now() + 7 * 864e5));
  const weekNotReady = ws.posts.filter((p) => p.date >= today && p.date <= weekEnd && (p.status === "ideia" || p.status === "producao"));

  return (
    <div className="grid gap-6">
      <PageHead title="Produção de conteúdo" sub="Cada post do roteiro até a publicação. Arraste os cards entre as colunas ou use as setas.">
        <Button size="sm" onClick={() => setEdit(newPost(ws, today))}><Plus className="size-4" />Novo post</Button>
      </PageHead>

      {(late.length > 0 || weekNotReady.length > 0) && (
        <ul className="grid gap-2 text-sm">
          {late.length > 0 && <li className="alert alert-bad">{late.length} {late.length === 1 ? "post passou" : "posts passaram"} da data sem ser {late.length === 1 ? "publicado" : "publicados"}. Remarque ou marque como publicado.</li>}
          {weekNotReady.length > 0 && <li className="alert alert-warn">{weekNotReady.length} {weekNotReady.length === 1 ? "post dos próximos 7 dias ainda não está pronto" : "posts dos próximos 7 dias ainda não estão prontos"}.</li>}
        </ul>
      )}

      {ws.posts.length === 0 ? (
        <Empty title="Nenhum post ainda" body="Crie o primeiro post. Ele já vem com as etapas de produção do formato escolhido." action={<Button size="sm" onClick={() => setEdit(newPost(ws, today))}>Criar post</Button>} />
      ) : (
        <div className="overflow-x-auto -mx-1 px-1 pb-2">
          <div className="grid grid-cols-4 gap-3 min-w-[880px]">
            {cols.map(({ s, posts }, ci) => (
              <section
                key={s}
                aria-label={POST_STATUS[s].label}
                className={`board-col grid content-start gap-2 min-h-[320px] pb-2 ${over === s ? "board-col-over" : ""}`}
                onDragOver={(e) => {
                  if (!dragId) return;
                  e.preventDefault();
                  setOver(s);
                }}
                onDragLeave={() => setOver((o) => (o === s ? null : o))}
                onDrop={(e) => {
                  e.preventDefault();
                  if (dragId) move(dragId, s);
                  setDragId(null);
                  setOver(null);
                }}
              >
                <header className="px-0.5 pt-2 pb-2 border-t-2 border-foreground/80">
                  <h2 className="text-sm font-semibold flex items-center justify-between gap-2">
                    {POST_STATUS[s].label}
                    <span className="text-xs font-normal text-muted-foreground tabular-nums">{posts.length}</span>
                  </h2>
                  <p className="text-xs text-muted-foreground">{COLUMN_HINT[s]}</p>
                </header>
                {posts.map((p) => {
                  const pr = progress(p);
                  const isLate = p.date < today && s !== "publicado";
                  return (
                    <article
                      key={p.id}
                      draggable
                      onDragStart={(e) => {
                        setDragId(p.id);
                        e.dataTransfer.effectAllowed = "move";
                      }}
                      onDragEnd={() => {
                        setDragId(null);
                        setOver(null);
                      }}
                      className={`board-card rounded border bg-card p-2.5 grid gap-1.5 ${dragId === p.id ? "opacity-50" : ""}`}
                    >
                      <button className="text-left grid gap-1" onClick={() => setEdit(p)}>
                        <span className={`text-xs tabular-nums ${isLate ? "text-bad font-medium" : "text-muted-foreground"}`}>
                          {fmtDay(p.date)}{p.time && `, ${p.time}`}{isLate && " (atrasado)"}
                        </span>
                        <span className="text-sm font-medium leading-snug">{p.title || "Sem título"}</span>
                        {p.hook && <span className="text-xs text-muted-foreground line-clamp-2">“{p.hook}”</span>}
                      </button>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="truncate">{p.format}</span>
                        {pr.total > 0 && (
                          <span className="ml-auto flex items-center gap-1.5 shrink-0" aria-label={`${pr.done} de ${pr.total} etapas feitas`}>
                            <span className="w-10 h-1 rounded-full bg-muted overflow-hidden"><span className="block h-full bg-brand" style={{ width: `${(pr.done / pr.total) * 100}%` }} /></span>
                            <span className="tabular-nums">{pr.done}/{pr.total}</span>
                          </span>
                        )}
                      </div>
                      <div className="flex justify-between -mx-1 -mb-1">
                        <Button size="sm" variant="ghost" className="h-7 px-1.5 text-muted-foreground" disabled={ci === 0} aria-label={`Mover para ${ci > 0 ? POST_STATUS[STATUS_ORDER[ci - 1]].label : ""}`} onClick={() => move(p.id, STATUS_ORDER[ci - 1])}>
                          <ChevronLeft className="size-4" />
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 px-1.5 text-muted-foreground" disabled={ci === STATUS_ORDER.length - 1} aria-label={`Mover para ${ci < STATUS_ORDER.length - 1 ? POST_STATUS[STATUS_ORDER[ci + 1]].label : ""}`} onClick={() => move(p.id, STATUS_ORDER[ci + 1])}>
                          <ChevronRight className="size-4" />
                        </Button>
                      </div>
                    </article>
                  );
                })}
                {posts.length === 0 && <p className="text-xs text-muted-foreground px-0.5 py-3">Nada aqui.</p>}
              </section>
            ))}
          </div>
        </div>
      )}

      <PostEditor
        post={edit}
        ws={ws}
        onClose={() => setEdit(null)}
        onSave={save}
        onDelete={(id) => {
          update((d) => {
            d.posts = d.posts.filter((x) => x.id !== id);
          });
          setEdit(null);
        }}
      />
    </div>
  );
}

