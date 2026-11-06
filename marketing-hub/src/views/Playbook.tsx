import { useState } from "react";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { PageHead, Field, selectCls, type ViewProps } from "../ui";
import { brl, num } from "../lib/metrics";
import { DEFAULT_CHECKLISTS, uid } from "../templates";
import type { ChannelKind, Workspace } from "../types";

const KIND: Record<ChannelKind, string> = { venda: "Venda", midia: "Mídia / divulgação", relacionamento: "Relacionamento" };

function Chips({ id, items, onChange, placeholder }: { id: string; items: string[]; onChange: (v: string[]) => void; placeholder: string }) {
  const [v, setV] = useState("");
  return (
    <div className="grid gap-2">
      <ul className="flex flex-wrap gap-1.5">
        {items.map((it, i) => (
          <li key={it + i} className="inline-flex items-center gap-1 rounded-full border bg-card pl-3 pr-1 py-0.5 text-sm">
            {it}
            <button aria-label={`Remover ${it}`} className="rounded-full size-5 grid place-items-center text-muted-foreground hover:bg-muted" onClick={() => onChange(items.filter((_, j) => j !== i))}><X className="size-3" /></button>
          </li>
        ))}
      </ul>
      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (v.trim()) { onChange([...items, v.trim()]); setV(""); } }}>
        <Input id={id} className="h-8" value={v} onChange={(e) => setV(e.target.value)} placeholder={placeholder} />
        <Button type="submit" size="sm" variant="outline">Adicionar</Button>
      </form>
    </div>
  );
}

export function Playbook({ ws, update }: ViewProps) {
  const set = <K extends keyof Workspace>(k: K, v: Workspace[K]) => update((d) => { d[k] = v; });
  const V = ws.vocab;
  return (
    <div className="grid gap-10">
      <PageHead title="Playbook do negócio" sub="Marca, canais, cardápio e metas. Quando você replica este negócio para outra frente, canais, pilares, segmentos, régua, metas e datas vão junto. Posts, campanhas e resultados não são copiados." />

      <section className="grid gap-4">
        <h2 className="section-title">Identidade</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Field label="Nome do negócio" htmlFor="pb-name"><Input id="pb-name" value={ws.name} onChange={(e) => set("name", e.target.value)} /></Field>
          <Field label="Segmento" htmlFor="pb-vertical"><Input id="pb-vertical" value={ws.vertical} onChange={(e) => set("vertical", e.target.value)} /></Field>
          <Field label="Cor da marca" htmlFor="pb-color">
            <div className="flex gap-2"><input id="pb-color" type="color" className="h-9 w-12 rounded border bg-card p-1" value={ws.color} onChange={(e) => set("color", e.target.value)} /><Input aria-label="Código da cor" className="font-mono" value={ws.color} onChange={(e) => set("color", e.target.value)} /></div>
          </Field>
          <Field label="Como você chama uma venda" htmlFor="pb-vocab" hint="Muda os textos do painel: pedido, venda, agendamento…">
            <div className="flex gap-2">
              <Input id="pb-vocab" aria-label="Singular" value={V.order} onChange={(e) => update((d) => { d.vocab.order = e.target.value; })} />
              <Input aria-label="Plural" value={V.orders} onChange={(e) => update((d) => { d.vocab.orders = e.target.value; })} />
            </div>
          </Field>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <Field label="Tom de voz" htmlFor="pb-voice"><Textarea id="pb-voice" rows={4} value={ws.voice} onChange={(e) => set("voice", e.target.value)} /></Field>
          <Field label="Público / persona" htmlFor="pb-persona"><Textarea id="pb-persona" rows={4} value={ws.persona} onChange={(e) => set("persona", e.target.value)} /></Field>
        </div>
        <Field label="Hashtags e termos de busca" htmlFor="pb-tags"><Input id="pb-tags" value={ws.hashtags} onChange={(e) => set("hashtags", e.target.value)} /></Field>
      </section>

      <section className="grid gap-4">
        <h2 className="section-title">Metas mensais</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Field label={`${V.orders} por mês`} htmlFor="goal-orders"><Input id="goal-orders" type="number" min={0} value={ws.goals.orders} onChange={(e) => update((d) => { d.goals.orders = Number(e.target.value); })} /></Field>
          <Field label="Faturamento por mês (R$)" htmlFor="goal-rev"><Input id="goal-rev" type="number" min={0} value={ws.goals.revenue} onChange={(e) => update((d) => { d.goals.revenue = Number(e.target.value); })} /></Field>
          <Field label="CAC máximo (R$)" htmlFor="goal-cac" hint="Quanto pode custar trazer 1 cliente novo"><Input id="goal-cac" type="number" min={0} step="any" value={ws.goals.cac} onChange={(e) => update((d) => { d.goals.cac = Number(e.target.value); })} /></Field>
          <Field label="MER mínimo (×)" htmlFor="goal-mer" hint="Faturamento ÷ investimento em mídia"><Input id="goal-mer" type="number" min={0} step="0.1" value={ws.goals.mer} onChange={(e) => update((d) => { d.goals.mer = Number(e.target.value); })} /></Field>
        </div>
      </section>

      <section className="grid md:grid-cols-2 gap-8">
        <div className="grid gap-3 content-start">
          <h2 className="section-title">Pilares de conteúdo</h2>
          <Chips id="pb-pillar-new" items={ws.pillars} onChange={(v) => set("pillars", v)} placeholder="Ex.: Receita do mês" />
        </div>
        <div className="grid gap-3 content-start">
          <h2 className="section-title">Formatos</h2>
          <Chips id="pb-format-new" items={ws.formats} onChange={(v) => set("formats", v)} placeholder="Ex.: Unboxing" />
        </div>
      </section>

      <section className="grid gap-3">
        <div>
          <h2 className="section-title">Etapas de produção por formato</h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-[62ch]">Cada post novo começa com as etapas do formato dele. Mudanças aqui valem para os próximos posts.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-x-8 gap-y-5">
          {ws.formats.map((f) => (
            <div key={f} className="grid gap-2 content-start">
              <h3 className="text-sm font-semibold">{f}</h3>
              <Chips id={`pb-chk-${f}`} items={ws.checklists?.[f] ?? DEFAULT_CHECKLISTS[f] ?? []} onChange={(v) => update((d) => { d.checklists = { ...(d.checklists ?? {}), [f]: v }; })} placeholder="Nova etapa" />
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-3">
        <div className="flex items-baseline justify-between gap-2 flex-wrap">
          <h2 className="section-title">Canais</h2>
          <Button size="sm" variant="outline" onClick={() => update((d) => { d.channels.push({ id: uid(), name: "Novo canal", kind: "venda", fee: 0 }); })}>Novo canal</Button>
        </div>
        <div className="overflow-x-auto border rounded-md">
          <table className="w-full text-sm min-w-[520px]">
            <thead className="text-xs text-muted-foreground bg-muted/50"><tr className="border-b"><th className="text-left font-medium px-3 py-2">Canal</th><th className="text-left font-medium px-2">Papel</th><th className="text-right font-medium px-2">Comissão %</th><th /></tr></thead>
            <tbody>
              {ws.channels.map((c, i) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="px-2 py-1.5"><Input id={`ch-name-${c.id}`} aria-label="Nome do canal" className="h-8" value={c.name} onChange={(e) => update((d) => { d.channels[i].name = e.target.value; })} /></td>
                  <td className="px-2 py-1.5 w-48">
                    <select id={`ch-kind-${c.id}`} aria-label="Papel do canal" className={selectCls + " h-8"} value={c.kind} onChange={(e) => update((d) => { d.channels[i].kind = e.target.value as ChannelKind; })}>
                      {Object.entries(KIND).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                    </select>
                  </td>
                  <td className="px-2 py-1.5 w-28"><Input id={`ch-fee-${c.id}`} aria-label="Comissão" type="number" min={0} max={100} step="0.1" className="h-8 text-right" value={c.fee} onChange={(e) => update((d) => { d.channels[i].fee = Number(e.target.value); })} /></td>
                  <td className="px-2 w-10">
                    <Button size="sm" variant="ghost" aria-label={`Remover ${c.name}`} className="text-muted-foreground" disabled={ws.weekly.some((w) => w.channelId === c.id) || ws.campaigns.some((x) => x.channelId === c.id)} title="Canais com resultados ou campanhas não podem ser removidos" onClick={() => update((d) => { d.channels.splice(i, 1); })}><X className="size-4" /></Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-3">
        <div className="flex items-baseline justify-between gap-2 flex-wrap">
          <h2 className="section-title">Cardápio / produtos</h2>
          <Button size="sm" variant="outline" onClick={() => update((d) => { d.products.push({ id: uid(), name: "Novo produto", price: 0, cost: 0, hero: false }); })}>Novo produto</Button>
        </div>
        <div className="overflow-x-auto border rounded-md">
          <table className="w-full text-sm min-w-[620px] tabular-nums">
            <thead className="text-xs text-muted-foreground bg-muted/50"><tr className="border-b"><th className="text-left font-medium px-3 py-2">Produto</th><th className="text-right font-medium px-2">Preço (R$)</th><th className="text-right font-medium px-2">Custo (R$)</th><th className="text-right font-medium px-2">Margem</th><th className="text-center font-medium px-2">Carro-chefe</th><th /></tr></thead>
            <tbody>
              {ws.products.map((p, i) => {
                const m = p.price ? (p.price - p.cost) / p.price : 0;
                return (
                  <tr key={p.id} className="border-b last:border-0">
                    <td className="px-2 py-1.5"><Input id={`pr-name-${p.id}`} aria-label="Produto" className="h-8" value={p.name} onChange={(e) => update((d) => { d.products[i].name = e.target.value; })} /></td>
                    <td className="px-2 py-1.5 w-28"><Input id={`pr-price-${p.id}`} aria-label="Preço" type="number" min={0} step="any" className="h-8 text-right" value={p.price} onChange={(e) => update((d) => { d.products[i].price = Number(e.target.value); })} /></td>
                    <td className="px-2 py-1.5 w-28"><Input id={`pr-cost-${p.id}`} aria-label="Custo" type="number" min={0} step="any" className="h-8 text-right" value={p.cost} onChange={(e) => update((d) => { d.products[i].cost = Number(e.target.value); })} /></td>
                    <td className={`px-2 text-right w-32 ${m < 0.5 ? "text-warn" : ""}`}>{num(m * 100)}%<div className="text-xs text-muted-foreground">{brl(p.price - p.cost, 2)}/un.</div></td>
                    <td className="px-2 text-center"><Switch id={`pr-hero-${p.id}`} aria-label="Carro-chefe" checked={p.hero} onCheckedChange={(v) => update((d) => { d.products[i].hero = v; })} /></td>
                    <td className="px-2 w-10"><Button size="sm" variant="ghost" aria-label={`Remover ${p.name}`} className="text-muted-foreground" onClick={() => update((d) => { d.products.splice(i, 1); })}><X className="size-4" /></Button></td>
                  </tr>
                );
              })}
              {ws.products.length === 0 && <tr><td colSpan={6} className="px-3 py-4 text-muted-foreground">Nenhum produto cadastrado.</td></tr>}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted-foreground">Margem abaixo de 50% fica em amarelo. Em marketplace de delivery, a comissão sai dessa margem: confira se o produto continua de pé depois dela.</p>
      </section>

      <section className="grid gap-3">
        <div className="flex items-baseline justify-between gap-2 flex-wrap">
          <h2 className="section-title">Datas que vendem</h2>
          <Button size="sm" variant="outline" onClick={() => update((d) => { d.dates.push({ md: "01-01", name: "Nova data" }); })}>Nova data</Button>
        </div>
        <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {[...ws.dates].map((k, i) => ({ k, i })).sort((a, b) => a.k.md.localeCompare(b.k.md)).map(({ k, i }) => (
            <li key={i} className="flex gap-2 items-center">
              <Input id={`dt-md-${i}`} aria-label="Dia e mês (MM-DD)" className="h-8 w-20 font-mono text-xs" value={k.md} onChange={(e) => update((d) => { d.dates[i].md = e.target.value; })} />
              <Input id={`dt-name-${i}`} aria-label="Nome da data" className="h-8" value={k.name} onChange={(e) => update((d) => { d.dates[i].name = e.target.value; })} />
              <Button size="sm" variant="ghost" aria-label="Remover data" className="text-muted-foreground" onClick={() => update((d) => { d.dates.splice(i, 1); })}><X className="size-4" /></Button>
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">Formato MM-DD. Datas móveis (Páscoa, Dia das Mães, Black Friday) precisam ser conferidas todo ano.</p>
      </section>
    </div>
  );
}
