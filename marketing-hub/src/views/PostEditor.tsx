import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Copy, Plus, RotateCcw, X } from "lucide-react";
import { toast } from "sonner";
import { Field, Pill, selectCls } from "../ui";
import { checklistFor, uid } from "../templates";
import type { Post, PostStatus, Workspace } from "../types";

export const POST_STATUS: Record<PostStatus, { label: string; tone: string }> = {
  ideia: { label: "Ideia", tone: "neutral" },
  producao: { label: "Em produção", tone: "warn" },
  agendado: { label: "Agendado", tone: "brand" },
  publicado: { label: "Publicado", tone: "good" },
};
export const STATUS_ORDER: PostStatus[] = ["ideia", "producao", "agendado", "publicado"];

// Limites do Instagram para legenda e hashtags.
const CAPTION_MAX = 2200;
const HASHTAG_MAX = 30;
const FOLD = 125; // caracteres visíveis antes do "mais" no feed

const CTA_SUGGESTIONS = [
  "Peça pelo link da bio",
  "Chame no WhatsApp para encomendar",
  "Salve para lembrar no fim de semana",
  "Marque quem dividiria essa caixa com você",
  "Comente qual sabor você quer na próxima fornada",
];

const SCRIPT_HINT: Record<string, string> = {
  Reels: "Uma cena por linha: o que aparece e o que é dito.",
  Carrossel: "Um slide por linha, na ordem.",
  Stories: "Um story por linha, na ordem.",
};

export const countHashtags = (s: string) => (s.match(/#[\p{L}\p{N}_]+/gu) ?? []).length;
export const progress = (p: Post) => {
  const done = p.checklist.filter((c) => c.done).length;
  return { done, total: p.checklist.length };
};

export function newPost(ws: Workspace, date: string): Post {
  const format = ws.formats[0] ?? "";
  return {
    id: uid(),
    date,
    time: "",
    title: "",
    channelId: ws.channels.find((c) => /instagram/i.test(c.name))?.id ?? ws.channels.find((c) => c.kind === "midia")?.id ?? ws.channels[0]?.id ?? "",
    pillar: ws.pillars[0] ?? "",
    format,
    status: "ideia",
    hook: "",
    script: "",
    caption: "",
    hashtags: ws.hashtags,
    cta: "",
    notes: "",
    checklist: checklistFor(ws, format),
  };
}

export function fullCaption(p: Pick<Post, "hook" | "caption" | "cta" | "hashtags">) {
  const body = [p.caption.trim(), p.cta.trim()].filter(Boolean).join("\n\n");
  return [body, p.hashtags.trim()].filter(Boolean).join("\n\n");
}

export function PostEditor({ post, ws, onClose, onSave, onDelete }: { post: Post | null; ws: Workspace; onClose: () => void; onSave: (p: Post) => void; onDelete: (id: string) => void }) {
  const [p, setP] = useState<Post | null>(post);
  const [lastId, setLastId] = useState<string | null>(null);
  const [newItem, setNewItem] = useState("");
  if (post && post.id !== lastId) {
    setLastId(post.id);
    setP(post);
  }
  if (!post && lastId) setLastId(null);
  const exists = !!post && ws.posts.some((x) => x.id === post.id);
  const set = <K extends keyof Post>(k: K, v: Post[K]) => setP((x) => (x ? { ...x, [k]: v } : x));

  const changeFormat = (format: string) =>
    setP((x) => {
      if (!x) return x;
      const untouched = x.checklist.every((c) => !c.done);
      return { ...x, format, checklist: untouched ? checklistFor(ws, format) : x.checklist };
    });

  const copyCaption = async () => {
    if (!p) return;
    const text = fullCaption(p);
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Legenda copiada");
    } catch {
      const el = document.getElementById("post-caption") as HTMLTextAreaElement | null;
      el?.focus();
      el?.select();
      toast("Selecionei a legenda. Use Ctrl+C ou Copiar.");
    }
  };

  const capLen = p ? fullCaption(p).length : 0;
  const tags = p ? countHashtags(p.hashtags) : 0;
  const prog = p ? progress(p) : { done: 0, total: 0 };
  const preview = p ? fullCaption(p) : "";

  return (
    <Sheet open={!!post} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto p-0">
        {p && (
          <form
            className="grid gap-7 px-5 sm:px-7 py-6"
            onSubmit={(e) => {
              e.preventDefault();
              onSave(p);
            }}
          >
            <SheetHeader className="text-left space-y-1">
              <SheetTitle className="font-display text-xl">{exists ? "Produção do post" : "Novo post"}</SheetTitle>
              <SheetDescription>
                {prog.total ? `${prog.done} de ${prog.total} etapas feitas.` : "Sem etapas de produção."} {POST_STATUS[p.status].label}.
              </SheetDescription>
            </SheetHeader>

            <section className="grid gap-4">
              <Field label="Ideia / título interno" htmlFor="post-title">
                <Input id="post-title" value={p.title} onChange={(e) => set("title", e.target.value)} placeholder="Ex.: Reels do recheio escorrendo" required />
              </Field>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <Field label="Data" htmlFor="post-date"><Input id="post-date" type="date" value={p.date} onChange={(e) => set("date", e.target.value)} required /></Field>
                <Field label="Horário" htmlFor="post-time"><Input id="post-time" type="time" value={p.time} onChange={(e) => set("time", e.target.value)} /></Field>
                <Field label="Status" htmlFor="post-status">
                  <select id="post-status" className={selectCls} value={p.status} onChange={(e) => set("status", e.target.value as PostStatus)}>
                    {STATUS_ORDER.map((k) => <option key={k} value={k}>{POST_STATUS[k].label}</option>)}
                  </select>
                </Field>
                <Field label="Formato" htmlFor="post-format">
                  <select id="post-format" className={selectCls} value={p.format} onChange={(e) => changeFormat(e.target.value)}>
                    {ws.formats.map((f) => <option key={f}>{f}</option>)}
                  </select>
                </Field>
                <Field label="Pilar" htmlFor="post-pillar">
                  <select id="post-pillar" className={selectCls} value={p.pillar} onChange={(e) => set("pillar", e.target.value)}>
                    {ws.pillars.map((f) => <option key={f}>{f}</option>)}
                  </select>
                </Field>
                <Field label="Canal" htmlFor="post-channel">
                  <select id="post-channel" className={selectCls} value={p.channelId} onChange={(e) => set("channelId", e.target.value)}>
                    {ws.channels.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </Field>
              </div>
            </section>

            <section className="grid gap-4 border-t pt-6">
              <h3 className="section-title">Roteiro</h3>
              <Field label="Gancho" htmlFor="post-hook" hint={p.format === "Reels" ? "O que aparece e é dito nos primeiros 3 segundos." : "A primeira frase, que precisa parar a rolagem."}>
                <Input id="post-hook" value={p.hook} onChange={(e) => set("hook", e.target.value)} placeholder="Ex.: Esse é o brownie que mais esgota aqui" />
              </Field>
              <Field label="Roteiro" htmlFor="post-script" hint={SCRIPT_HINT[p.format] ?? "Como o post vai ser montado."}>
                <Textarea id="post-script" rows={5} value={p.script} onChange={(e) => set("script", e.target.value)} />
              </Field>
            </section>

            <section className="grid gap-4 border-t pt-6">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="section-title">Legenda</h3>
                <Button type="button" size="sm" variant="outline" onClick={copyCaption}><Copy className="size-3.5" />Copiar legenda completa</Button>
              </div>
              <Field label="Texto" htmlFor="post-caption">
                <Textarea id="post-caption" rows={6} value={p.caption} onChange={(e) => set("caption", e.target.value)} placeholder={p.hook ? `Comece pelo gancho: ${p.hook}` : ""} />
              </Field>
              <div className="grid sm:grid-cols-2 gap-3">
                <Field label="Chamada para ação" htmlFor="post-cta">
                  <Input id="post-cta" list="cta-options" value={p.cta} onChange={(e) => set("cta", e.target.value)} placeholder="Peça pelo link da bio" />
                  <datalist id="cta-options">{CTA_SUGGESTIONS.map((c) => <option key={c} value={c} />)}</datalist>
                </Field>
                <Field label={`Hashtags (${tags} de ${HASHTAG_MAX})`} htmlFor="post-tags" hint={tags > HASHTAG_MAX ? "O Instagram não publica com mais de 30 hashtags." : undefined}>
                  <Input id="post-tags" value={p.hashtags} onChange={(e) => set("hashtags", e.target.value)} className={tags > HASHTAG_MAX ? "border-bad" : ""} />
                </Field>
              </div>
              <div className="grid gap-1.5">
                <div className="flex justify-between gap-2 text-xs text-muted-foreground">
                  <span>Como aparece no feed</span>
                  <span className={`tabular-nums ${capLen > CAPTION_MAX ? "text-bad font-medium" : ""}`}>{capLen.toLocaleString("pt-BR")} de {CAPTION_MAX.toLocaleString("pt-BR")} caracteres</span>
                </div>
                <div className="rounded-md border bg-card px-3 py-2.5 text-sm whitespace-pre-wrap break-words">
                  {preview ? (
                    <>
                      <strong className="font-semibold">{ws.name.normalize("NFD").toLowerCase().replace(/[^a-z0-9]+/g, "")}</strong>{" "}
                      {preview.length > FOLD ? (
                        <>
                          {preview.slice(0, FOLD).trimEnd()}… <span className="text-muted-foreground">mais</span>
                        </>
                      ) : (
                        preview
                      )}
                    </>
                  ) : (
                    <span className="text-muted-foreground">A legenda aparece aqui. No feed, só os primeiros {FOLD} caracteres ficam visíveis antes do "mais".</span>
                  )}
                </div>
              </div>
            </section>

            <section className="grid gap-3 border-t pt-6">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="section-title">Etapas de produção</h3>
                <Button type="button" size="sm" variant="ghost" className="text-muted-foreground" onClick={() => set("checklist", checklistFor(ws, p.format))}>
                  <RotateCcw className="size-3.5" />Usar etapas padrão de {p.format}
                </Button>
              </div>
              <ul className="grid gap-1">
                {p.checklist.map((c, i) => (
                  <li key={c.id} className="flex items-center gap-3 rounded px-1 py-1 hover:bg-muted/60">
                    <Checkbox
                      id={`chk-${c.id}`}
                      checked={c.done}
                      onCheckedChange={(v) => set("checklist", p.checklist.map((x, j) => (j === i ? { ...x, done: v === true } : x)))}
                    />
                    <label htmlFor={`chk-${c.id}`} className={`flex-1 text-sm cursor-pointer ${c.done ? "line-through text-muted-foreground" : ""}`}>{c.label}</label>
                    <button type="button" aria-label={`Remover etapa ${c.label}`} className="text-muted-foreground hover:text-foreground p-1 rounded" onClick={() => set("checklist", p.checklist.filter((_, j) => j !== i))}>
                      <X className="size-3.5" />
                    </button>
                  </li>
                ))}
              </ul>
              <div className="flex gap-2">
                <Input
                  id="chk-new"
                  aria-label="Nova etapa"
                  className="h-8"
                  value={newItem}
                  onChange={(e) => setNewItem(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      if (newItem.trim()) {
                        set("checklist", [...p.checklist, { id: uid(), label: newItem.trim(), done: false }]);
                        setNewItem("");
                      }
                    }
                  }}
                  placeholder="Nova etapa, ex.: Pedir foto para a cliente"
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    if (newItem.trim()) {
                      set("checklist", [...p.checklist, { id: uid(), label: newItem.trim(), done: false }]);
                      setNewItem("");
                    }
                  }}
                >
                  <Plus className="size-3.5" />Adicionar
                </Button>
              </div>
              {prog.total > 0 && prog.done === prog.total && p.status !== "agendado" && p.status !== "publicado" && (
                <p className="text-sm">
                  Todas as etapas feitas.{" "}
                  <button type="button" className="underline underline-offset-2" onClick={() => set("status", "agendado")}>Marcar como agendado</button>
                </p>
              )}
            </section>

            <section className="grid gap-3 border-t pt-6">
              <h3 className="section-title">Referências e observações</h3>
              <Textarea id="post-notes" aria-label="Referências e observações" rows={3} value={p.notes} onChange={(e) => set("notes", e.target.value)} placeholder="Links de inspiração, áudio do Reels, quem aparece, onde gravar" />
            </section>

            <div className="flex flex-wrap gap-2 justify-between border-t pt-5 sticky bottom-0 bg-background pb-2">
              {exists ? <Button type="button" variant="ghost" className="text-bad" onClick={() => onDelete(p.id)}>Excluir post</Button> : <span />}
              <div className="flex gap-2">
                <Pill tone={POST_STATUS[p.status].tone} className="self-center">{POST_STATUS[p.status].label}</Pill>
                <Button type="submit">Salvar post</Button>
              </div>
            </div>
          </form>
        )}
      </SheetContent>
    </Sheet>
  );
}
