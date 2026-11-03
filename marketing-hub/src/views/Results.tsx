import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHead, Field, Empty, type ViewProps } from "../ui";
import { brl, num, fmtDay, iso, mondayOf, parseIso, totals, weeksOf } from "../lib/metrics";
import { uid } from "../templates";
import type { WeeklyEntry } from "../types";
import { toast } from "sonner";

type Row = { orders: number; revenue: number; newCustomers: number; adSpend: number };

export function Results({ ws, update }: ViewProps) {
  const V = ws.vocab;
  const sales = ws.channels.filter((c) => c.kind === "venda");
  const media = ws.channels.filter((c) => c.kind === "midia");
  const [week, setWeek] = useState(() => iso(mondayOf(new Date(Date.now() - 7 * 864e5))));
  const load = (w: string) => {
    const r: Record<string, Row> = {};
    ws.channels.forEach((c) => {
      const e = ws.weekly.find((x) => x.week === w && x.channelId === c.id);
      r[c.id] = { orders: e?.orders ?? 0, revenue: e?.revenue ?? 0, newCustomers: e?.newCustomers ?? 0, adSpend: e?.adSpend ?? 0 };
    });
    return r;
  };
  const [rows, setRows] = useState<Record<string, Row>>(() => load(week));
  const pick = (w: string) => {
    const m = iso(mondayOf(parseIso(w)));
    setWeek(m);
    setRows(load(m));
  };
  const setCell = (id: string, k: keyof Row, v: number) => setRows((r) => ({ ...r, [id]: { ...r[id], [k]: v } }));
  const saveWeek = () => {
    update((d) => {
      d.weekly = d.weekly.filter((x) => x.week !== week);
      ws.channels.forEach((c) => {
        const r = rows[c.id];
        if (!r) return;
        if (r.orders || r.revenue || r.newCustomers || r.adSpend) {
          const e: WeeklyEntry = { id: uid(), week, channelId: c.id, ...r };
          d.weekly.push(e);
        }
      });
    });
    toast.success(`Semana de ${fmtDay(week)} salva`);
  };
  const weeks = weeksOf(ws).reverse();
  const numIn = (id: string, k: keyof Row, label: string) => (
    <Input
      id={`res-${id}-${k}`}
      aria-label={label}
      type="number"
      min={0}
      step="any"
      inputMode="decimal"
      className="text-right tabular-nums h-8"
      value={rows[id]?.[k] || ""}
      placeholder="0"
      onChange={(e) => setCell(id, k, Number(e.target.value))}
    />
  );

  return (
    <div className="grid gap-8">
      <PageHead title="Resultados da semana" sub="Lance os números uma vez por semana. A visão geral é calculada a partir daqui." />
      <section className="grid gap-4">
        <div className="flex flex-wrap items-end gap-4">
          <Field label="Semana começando em (segunda)" htmlFor="res-week">
            <Input id="res-week" type="date" value={week} onChange={(e) => e.target.value && pick(e.target.value)} className="w-48" />
          </Field>
          <p className="text-xs text-muted-foreground pb-2">Puxe os números do painel de cada canal (ex.: relatório financeiro do marketplace, gerenciador de anúncios).</p>
        </div>
        <div className="overflow-x-auto border rounded-md">
          <table className="w-full text-sm min-w-[560px]">
            <thead className="text-xs text-muted-foreground bg-muted/50">
              <tr className="border-b">
                <th className="text-left font-medium px-3 py-2">Canal de venda</th>
                <th className="text-right font-medium px-2">{V.orders.charAt(0).toUpperCase() + V.orders.slice(1)}</th>
                <th className="text-right font-medium px-2">Faturamento (R$)</th>
                <th className="text-right font-medium px-2">{V.customers.charAt(0).toUpperCase() + V.customers.slice(1)} novos</th>
              </tr>
            </thead>
            <tbody>
              {sales.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="px-3 py-1.5">{c.name}{c.fee ? <span className="text-xs text-muted-foreground"> ({c.fee}% de comissão)</span> : null}</td>
                  <td className="px-2 py-1.5 w-28">{numIn(c.id, "orders", `${V.orders} ${c.name}`)}</td>
                  <td className="px-2 py-1.5 w-36">{numIn(c.id, "revenue", `Faturamento ${c.name}`)}</td>
                  <td className="px-2 py-1.5 w-28">{numIn(c.id, "newCustomers", `Novos ${c.name}`)}</td>
                </tr>
              ))}
            </tbody>
            {media.length > 0 && (
              <>
                <thead className="text-xs text-muted-foreground bg-muted/50">
                  <tr className="border-y"><th className="text-left font-medium px-3 py-2" colSpan={3}>Mídia e anúncios</th><th className="text-right font-medium px-2">Investido (R$)</th></tr>
                </thead>
                <tbody>
                  {media.map((c) => (
                    <tr key={c.id} className="border-b last:border-0">
                      <td className="px-3 py-1.5" colSpan={3}>{c.name}</td>
                      <td className="px-2 py-1.5 w-28">{numIn(c.id, "adSpend", `Investimento ${c.name}`)}</td>
                    </tr>
                  ))}
                </tbody>
              </>
            )}
          </table>
        </div>
        <div><Button onClick={saveWeek}>Salvar semana de {fmtDay(week)}</Button></div>
      </section>

      <section className="grid gap-3">
        <h2 className="section-title">Histórico</h2>
        {weeks.length === 0 ? (
          <Empty title="Sem histórico" body="As semanas salvas aparecem aqui e alimentam a visão geral." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm tabular-nums min-w-[620px]">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b">
                  <th className="text-left font-medium py-2">Semana</th>
                  <th className="text-right font-medium">{V.orders.charAt(0).toUpperCase() + V.orders.slice(1)}</th>
                  <th className="text-right font-medium">Bruto</th>
                  <th className="text-right font-medium">Líquido</th>
                  <th className="text-right font-medium">Ticket</th>
                  <th className="text-right font-medium">Mídia</th>
                  <th className="text-right font-medium">CAC</th>
                  <th className="text-right font-medium">MER</th>
                </tr>
              </thead>
              <tbody>
                {weeks.map((w) => {
                  const t = totals(ws, ws.weekly.filter((x) => x.week === w));
                  return (
                    <tr key={w} className={`border-b last:border-0 ${w === week ? "bg-muted/50" : ""}`}>
                      <td className="py-2"><button className="underline-offset-2 hover:underline" onClick={() => pick(w)}>{fmtDay(w)}</button></td>
                      <td className="text-right">{num(t.orders)}</td>
                      <td className="text-right">{brl(t.revenue)}</td>
                      <td className="text-right">{brl(t.net)}</td>
                      <td className="text-right">{brl(t.ticket, 2)}</td>
                      <td className="text-right">{brl(t.adSpend)}</td>
                      <td className={`text-right ${t.cac > ws.goals.cac ? "text-bad" : ""}`}>{t.cac ? brl(t.cac, 2) : "—"}</td>
                      <td className="text-right">{t.mer ? num(t.mer, 1) + "×" : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
