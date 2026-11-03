import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { PageHead, Field, Pill, Empty, selectCls, type ViewProps } from "../ui";
import { brl, num, fmtDay, iso } from "../lib/metrics";
import { uid } from "../templates";
import type { Campaign, CampaignStatus } from "../types";

const STATUS: Record<CampaignStatus, { label: string; tone: string }> = {
  planejada: { label: "Planejada", tone: "neutral" },
  ativa: { label: "Ativa", tone: "good" },
  pausada: { label: "Pausada", tone: "warn" },
  encerrada: { label: "Encerrada", tone: "neutral" },
};
const OBJECTIVES = ["Novos clientes", "Recompra", "Ticket médio", "Reativação", "Data comemorativa", "Lançamento", "Seguidores / alcance"];

export function Campaigns({ ws, update }: ViewProps) {
  const [edit, setEdit] = useState<Campaign | null>(null);
  const V = ws.vocab;
  const ch = (id: string) => ws.channels.find((c) => c.id === id)?.name ?? "—";
  const order: CampaignStatus[] = ["ativa", "planejada", "pausada", "encerrada"];
  const list = [...ws.campaigns].sort((a, b) => order.indexOf(a.status) - order.indexOf(b.status) || b.start.localeCompare(a.start));
  const tot = ws.campaigns.reduce((a, c) => ({ spent: a.spent + c.spent, revenue: a.revenue + c.revenue, orders: a.orders + c.orders }), { spent: 0, revenue: 0, orders: 0 });

  const blank = (): Campaign => ({
    id: uid(), name: "", channelId: ws.channels.find((c) => c.kind === "midia")?.id ?? ws.channels[0]?.id ?? "",
    objective: OBJECTIVES[0], start: iso(new Date()), end: iso(new Date(Date.now() + 14 * 864e5)), budget: 0, spent: 0, orders: 0, revenue: 0, coupon: "", status: "planejada",
  });
  const save = (c: Campaign) => {
    update((d) => {
      const i = d.campaigns.findIndex((x) => x.id === c.id);
      if (i >= 0) d.campaigns[i] = c; else d.campaigns.push(c);
    });
    setEdit(null);
  };

  return (
    <div className="grid gap-6">
      <PageHead title="Campanhas e promoções" sub="O que está rodando, quanto já custou e quanto voltou em vendas.">
        <Button size="sm" onClick={() => setEdit(blank())}>Nova campanha</Button>
      </PageHead>

      <div className="flex flex-wrap gap-x-10 gap-y-3 text-sm">
        <div><p className="eyebrow">Investido</p><p className="font-display text-xl tabular-nums">{brl(tot.spent)}</p></div>
        <div><p className="eyebrow">Receita atribuída</p><p className="font-display text-xl tabular-nums">{brl(tot.revenue)}</p></div>
        <div><p className="eyebrow">Retorno (ROAS)</p><p className="font-display text-xl tabular-nums">{tot.spent ? num(tot.revenue / tot.spent, 1) + "×" : "—"}</p></div>
        <div><p className="eyebrow">Custo por {V.order}</p><p className="font-display text-xl tabular-nums">{tot.orders ? brl(tot.spent / tot.orders, 2) : "—"}</p></div>
      </div>

      {list.length === 0 ? (
        <Empty title="Nenhuma campanha" body="Cadastre anúncios, cupons e ações de data comemorativa. O painel calcula retorno e custo por pedido e avisa quando passar da meta." action={<Button size="sm" onClick={() => setEdit(blank())}>Criar campanha</Button>} />
      ) : (
        <div className="overflow-x-auto border rounded-md">
          <table className="w-full text-sm tabular-nums min-w-[760px]">
            <thead className="text-xs text-muted-foreground bg-muted/50">
              <tr className="border-b">
                <th className="text-left font-medium px-3 py-2">Campanha</th>
                <th className="text-left font-medium">Período</th>
                <th className="text-left font-medium">Status</th>
                <th className="text-right font-medium">Orçamento</th>
                <th className="text-right font-medium">{V.orders.charAt(0).toUpperCase() + V.orders.slice(1)}</th>
                <th className="text-right font-medium">Custo/{V.order}</th>
                <th className="text-right font-medium px-3">ROAS</th>
              </tr>
            </thead>
            <tbody>
              {list.map((c) => {
                const cpa = c.orders ? c.spent / c.orders : 0;
                const roas = c.spent ? c.revenue / c.spent : 0;
                const used = c.budget ? c.spent / c.budget : 0;
                return (
                  <tr key={c.id} className="border-b last:border-0 hover:bg-muted/40 cursor-pointer" onClick={() => setEdit(c)}>
                    <td className="px-3 py-2.5">
                      <button className="text-left font-medium hover:underline" onClick={(e) => { e.stopPropagation(); setEdit(c); }}>{c.name}</button>
                      <div className="text-xs text-muted-foreground">{ch(c.channelId)}, {c.objective.toLowerCase()}{c.coupon && <>, cupom <span className="font-mono">{c.coupon}</span></>}</div>
                    </td>
                    <td className="text-xs text-muted-foreground whitespace-nowrap">{fmtDay(c.start)} – {fmtDay(c.end)}</td>
                    <td><Pill tone={STATUS[c.status].tone}>{STATUS[c.status].label}</Pill></td>
                    <td className="text-right">
                      {brl(c.spent)} <span className="text-muted-foreground">/ {brl(c.budget)}</span>
                      <div className="h-1 bg-muted rounded-full mt-1 ml-auto w-24"><div className={`h-1 rounded-full ${used > 0.9 ? "bg-warn" : "bg-brand"}`} style={{ width: `${Math.min(100, used * 100)}%` }} /></div>
                    </td>
                    <td className="text-right">{num(c.orders)}</td>
                    <td className={`text-right ${cpa > ws.goals.cac ? "text-bad font-medium" : ""}`}>{cpa ? brl(cpa, 2) : "—"}</td>
                    <td className={`text-right px-3 font-medium ${roas && roas < ws.goals.mer ? "text-warn" : ""}`}>{roas ? num(roas, 1) + "×" : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-muted-foreground">Custo por {V.order} em vermelho passou da meta de CAC ({brl(ws.goals.cac)}). ROAS em amarelo está abaixo da meta de {num(ws.goals.mer, 1)}×.</p>

      <CampaignDialog c={edit} ws={ws} onClose={() => setEdit(null)} onSave={save} onDelete={(id) => { update((d) => { d.campaigns = d.campaigns.filter((x) => x.id !== id); }); setEdit(null); }} />
    </div>
  );
}

function CampaignDialog({ c, ws, onClose, onSave, onDelete }: { c: Campaign | null; ws: ViewProps["ws"]; onClose: () => void; onSave: (c: Campaign) => void; onDelete: (id: string) => void }) {
  const [v, setV] = useState<Campaign | null>(c);
  const [lastId, setLastId] = useState<string | null>(null);
  if (c && c.id !== lastId) { setLastId(c.id); setV(c); }
  if (!c && lastId) setLastId(null);
  const exists = c && ws.campaigns.some((x) => x.id === c.id);
  const set = <K extends keyof Campaign>(k: K, val: Campaign[K]) => setV((x) => (x ? { ...x, [k]: val } : x));
  const n = (k: "budget" | "spent" | "orders" | "revenue") => (
    <Input id={`camp-${k}`} type="number" min={0} step="any" inputMode="decimal" value={v ? v[k] : 0} onChange={(e) => set(k, Number(e.target.value))} />
  );
  return (
    <Dialog open={!!c} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader><DialogTitle className="font-display">{exists ? "Editar campanha" : "Nova campanha"}</DialogTitle></DialogHeader>
        {v && (
          <form className="grid gap-4" onSubmit={(e) => { e.preventDefault(); onSave(v); }}>
            <Field label="Nome" htmlFor="camp-name"><Input id="camp-name" value={v.name} onChange={(e) => set("name", e.target.value)} placeholder="Ex.: Caixa presente Dia dos Namorados" required /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Canal" htmlFor="camp-channel">
                <select id="camp-channel" className={selectCls} value={v.channelId} onChange={(e) => set("channelId", e.target.value)}>
                  {ws.channels.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
                </select>
              </Field>
              <Field label="Objetivo" htmlFor="camp-obj">
                <select id="camp-obj" className={selectCls} value={v.objective} onChange={(e) => set("objective", e.target.value)}>
                  {OBJECTIVES.map((o) => <option key={o}>{o}</option>)}
                </select>
              </Field>
              <Field label="Início" htmlFor="camp-start"><Input id="camp-start" type="date" value={v.start} onChange={(e) => set("start", e.target.value)} /></Field>
              <Field label="Fim" htmlFor="camp-end"><Input id="camp-end" type="date" value={v.end} onChange={(e) => set("end", e.target.value)} /></Field>
              <Field label="Status" htmlFor="camp-status">
                <select id="camp-status" className={selectCls} value={v.status} onChange={(e) => set("status", e.target.value as CampaignStatus)}>
                  {Object.entries(STATUS).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
                </select>
              </Field>
              <Field label="Cupom" htmlFor="camp-coupon"><Input id="camp-coupon" className="font-mono uppercase" value={v.coupon} onChange={(e) => set("coupon", e.target.value.toUpperCase())} placeholder="NAMORADOS15" /></Field>
              <Field label="Orçamento (R$)" htmlFor="camp-budget">{n("budget")}</Field>
              <Field label="Gasto até agora (R$)" htmlFor="camp-spent">{n("spent")}</Field>
              <Field label={`${ws.vocab.orders} atribuídos`} htmlFor="camp-orders">{n("orders")}</Field>
              <Field label="Receita atribuída (R$)" htmlFor="camp-revenue">{n("revenue")}</Field>
            </div>
            <DialogFooter className="gap-2 sm:justify-between">
              {exists ? <Button type="button" variant="ghost" className="text-bad" onClick={() => onDelete(v.id)}>Excluir</Button> : <span />}
              <Button type="submit">Salvar campanha</Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
