import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHead, Field, Pill } from "../ui";
import { TEMPLATES, buildWorkspace, replicateWorkspace } from "../templates";
import type { Workspace } from "../types";

export function Businesses({ list, current, onCreate, onOpen, onRemove }: { list: Workspace[]; current?: Workspace; onCreate: (w: Workspace) => void; onOpen: (id: string) => void; onRemove: (id: string) => void }) {
  const [tpl, setTpl] = useState(TEMPLATES[0].id);
  const [name, setName] = useState("");
  const [repName, setRepName] = useState("");
  const [repVertical, setRepVertical] = useState("");
  const [confirm, setConfirm] = useState<string | null>(null);

  return (
    <div className="grid gap-10">
      <PageHead title={list.length ? "Negócios e modelos" : "Comece pelo seu primeiro negócio"} sub={list.length ? "Abra um negócio, replique a estrutura dele para outra frente ou comece de um modelo." : "Escolha o modelo mais parecido com a sua operação. Tudo pode ser ajustado depois."} />

      {list.length > 0 && (
        <section className="grid gap-3">
          <h2 className="section-title">Negócios nesta central</h2>
          <ul className="grid gap-px bg-border border rounded-md overflow-hidden">
            {list.map((w) => (
              <li key={w.id} className="bg-card px-4 py-3 flex flex-wrap items-center gap-3">
                <span className="size-3 rounded-full shrink-0" style={{ background: w.color }} />
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{w.name} {w.example && <Pill tone="warn" className="ml-1">exemplo</Pill>}{current?.id === w.id && <Pill tone="brand" className="ml-1">aberto</Pill>}</p>
                  <p className="text-xs text-muted-foreground truncate">{w.vertical}. {w.channels.length} canais, {w.posts.length} posts, {w.campaigns.length} campanhas</p>
                </div>
                {confirm === w.id ? (
                  <div className="flex gap-2 items-center text-sm">
                    <span className="text-bad">Apagar tudo deste negócio?</span>
                    <Button size="sm" variant="destructive" onClick={() => { onRemove(w.id); setConfirm(null); }}>Apagar</Button>
                    <Button size="sm" variant="ghost" onClick={() => setConfirm(null)}>Cancelar</Button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => onOpen(w.id)}>Abrir</Button>
                    <Button size="sm" variant="ghost" className="text-muted-foreground" onClick={() => setConfirm(w.id)}>Excluir</Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {current && (
        <section className="grid gap-4 border rounded-md p-5 bg-card">
          <div>
            <h2 className="section-title">Replicar {current.name} para outra frente</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-[62ch]">Copia canais, comissões, pilares, formatos, segmentos com mensagens, régua de relacionamento, metas e datas. Não copia posts, campanhas, resultados nem produtos.</p>
          </div>
          <form className="grid sm:grid-cols-[1fr_1fr_auto] gap-3 items-end" onSubmit={(e) => { e.preventDefault(); const w = replicateWorkspace(current, repName, repVertical); onCreate(w); setRepName(""); setRepVertical(""); }}>
            <Field label="Nome da nova frente" htmlFor="rep-name"><Input id="rep-name" value={repName} onChange={(e) => setRepName(e.target.value)} placeholder="Ex.: Linha de bolos no pote" /></Field>
            <Field label="Segmento" htmlFor="rep-vertical"><Input id="rep-vertical" value={repVertical} onChange={(e) => setRepVertical(e.target.value)} placeholder={current.vertical} /></Field>
            <Button type="submit">Replicar estrutura</Button>
          </form>
        </section>
      )}

      <section className="grid gap-4">
        <div>
          <h2 className="section-title">Criar a partir de um modelo</h2>
          <p className="text-sm text-muted-foreground mt-1">Cada modelo já vem com canais, comissões típicas, segmentos de clientes, régua de contato e datas do setor. Tudo pode ser editado depois no Playbook.</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3" role="radiogroup" aria-label="Modelo de negócio">
          {TEMPLATES.map((t) => (
            <button key={t.id} role="radio" aria-checked={tpl === t.id} onClick={() => setTpl(t.id)} className={`tpl text-left grid gap-1.5 p-4 rounded-md border bg-card ${tpl === t.id ? "tpl-on" : ""}`} style={{ ["--tpl" as string]: t.color }}>
              <span className="flex items-center gap-2"><span className="size-2.5 rounded-full" style={{ background: t.color }} /><span className="font-medium">{t.label}</span></span>
              <span className="text-xs text-muted-foreground">{t.vertical}</span>
              <span className="text-sm">{t.blurb}</span>
              <span className="text-xs text-muted-foreground">Canais: {t.channels.map((c) => c.name).join(", ")}</span>
            </button>
          ))}
        </div>
        <form className="flex flex-wrap gap-3 items-end" onSubmit={(e) => { e.preventDefault(); onCreate(buildWorkspace(tpl, name)); setName(""); }}>
          <Field label="Nome do negócio" htmlFor="new-name" className="w-full sm:w-80"><Input id="new-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex.: Brownie da Vila" required /></Field>
          <Button type="submit">Criar negócio</Button>
        </form>
      </section>
    </div>
  );
}
