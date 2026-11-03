import { Button } from "@/components/ui/button";
import { PageHead, Empty, type ViewProps } from "../ui";
import { brl, num, periods, delta, fmtDay, iso, parseIso, weeksOf, totals } from "../lib/metrics";
import type { Workspace } from "../types";

function Kpi({ label, value, sub, d, goodWhenUp = true, goal }: { label: string; value: string; sub?: string; d?: number; goodWhenUp?: boolean; goal?: { pct: number; text: string } }) {
  const has = d !== undefined && Number.isFinite(d) && d !== 0;
  const up = (d ?? 0) > 0;
  const good = has && up === goodWhenUp;
  return (
    <div className="kpi grid gap-1 min-w-0">
      <p className="eyebrow">{label}</p>
      <p className="font-display text-[1.6rem] leading-none tabular-nums mt-1">{value}</p>
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground mt-1">
        {has && <span className={good ? "text-good font-medium" : "text-bad font-medium"}>{up ? "▲" : "▼"} {num(Math.abs((d ?? 0) * 100), 0)}%</span>}
        {sub && <span>{sub}</span>}
      </div>
      {goal && (
        <div className="mt-2 grid gap-1">
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div className="h-full rounded-full bg-brand" style={{ width: `${Math.min(100, goal.pct * 100)}%` }} />
          </div>
          <p className="text-[11px] text-muted-foreground">{goal.text}</p>
        </div>
      )}
    </div>
  );
}

function WeeklyChart({ ws }: { ws: Workspace }) {
  const weeks = weeksOf(ws).slice(-12);
  const sales = ws.channels.filter((c) => c.kind === "venda");
  const data = weeks.map((w) => ({
    w,
    parts: sales.map((c) => ws.weekly.filter((r) => r.week === w && r.channelId === c.id).reduce((a, r) => a + r.orders, 0)),
  }));
  const max = Math.max(1, ...data.map((d) => d.parts.reduce((a, b) => a + b, 0)));
  const step = niceStep(max);
  const top = Math.ceil(max / step) * step;
  const W = 640, H = 220, L = 40, B = 26, T = 10;
  const bw = (W - L - 8) / Math.max(1, data.length);
  const y = (v: number) => H - B - (v / top) * (H - B - T);
  const shades = [1, 0.6, 0.38, 0.22];
  return (
    <figure className="grid gap-3 min-w-0">
      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        {sales.map((c, i) => (
          <span key={c.id} className="inline-flex items-center gap-1.5">
            <span className="size-2.5 rounded-sm bg-brand" style={{ opacity: shades[i % 4] }} />
            {c.name}
          </span>
        ))}
      </div>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full min-w-[480px] h-auto" role="img" aria-label={`${ws.vocab.orders} por semana e canal`}>
          {Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step).map((v) => (
            <g key={v}>
              <line x1={L} x2={W} y1={y(v)} y2={y(v)} className="stroke-border" strokeDasharray={v ? "2 4" : undefined} />
              <text x={L - 6} y={y(v) + 4} textAnchor="end" className="fill-muted-foreground text-[10px] tabular-nums">{num(v)}</text>
            </g>
          ))}
          {data.map((d, i) => {
            let acc = 0;
            const x = L + i * bw + bw * 0.18;
            const total = d.parts.reduce((a, b) => a + b, 0);
            return (
              <g key={d.w}>
                <title>{`${fmtDay(d.w)}: ${num(total)} ${ws.vocab.orders}`}</title>
                {d.parts.map((p, j) => {
                  const y0 = y(acc), y1 = y(acc + p);
                  acc += p;
                  return p ? <rect key={j} x={x} width={bw * 0.64} y={y1} height={Math.max(0, y0 - y1)} className="fill-brand" opacity={shades[j % 4]} /> : null;
                })}
                {i === data.length - 1 && <text x={x + bw * 0.32} y={y(total) - 5} textAnchor="middle" className="fill-foreground text-[10px] font-semibold tabular-nums">{num(total)}</text>}
                <text x={x + bw * 0.32} y={H - 8} textAnchor="middle" className="fill-muted-foreground text-[10px]">{fmtDay(d.w)}</text>
              </g>
            );
          })}
        </svg>
      </div>
    </figure>
  );
}
function niceStep(max: number) {
  const raw = max / 4;
  const p = Math.pow(10, Math.floor(Math.log10(raw)));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= raw) ?? p * 10;
}

export function Overview({ ws, go }: ViewProps) {
  const { cur, curT, prevT, prev } = periods(ws);
  const V = ws.vocab;
  const today = iso(new Date());
  const in7 = iso(new Date(Date.now() + 7 * 864e5));
  const nextPosts = ws.posts.filter((p) => p.date >= today && p.date <= in7).sort((a, b) => a.date.localeCompare(b.date));
  const now = new Date();
  const upcoming = ws.dates
    .map((d) => {
      let dt = new Date(now.getFullYear(), Number(d.md.slice(0, 2)) - 1, Number(d.md.slice(3)));
      if (dt < new Date(now.getFullYear(), now.getMonth(), now.getDate())) dt = new Date(now.getFullYear() + 1, dt.getMonth(), dt.getDate());
      return { ...d, dt, days: Math.round((dt.getTime() - now.getTime()) / 864e5) };
    })
    .filter((d) => d.days <= 60)
    .sort((a, b) => a.days - b.days);
  const active = ws.campaigns.filter((c) => c.status === "ativa");
  const ch = (id: string) => ws.channels.find((c) => c.id === id)?.name ?? "—";
  // metas são mensais; 4 semanas ≈ 0,92 mês
  const monthFactor = 28 / 30.4;

  const alerts: { tone: string; text: string; to: string }[] = [];
  active.forEach((c) => {
    const cpa = c.orders ? c.spent / c.orders : 0;
    if (c.orders && cpa > ws.goals.cac) alerts.push({ tone: "bad", text: `“${c.name}”: custo por ${V.order} de ${brl(cpa, 2)} está acima da meta de CAC (${brl(ws.goals.cac)}).`, to: "campanhas" });
    if (c.budget && c.spent / c.budget > 0.9) alerts.push({ tone: "warn", text: `“${c.name}” já usou ${num((c.spent / c.budget) * 100)}% do orçamento.`, to: "campanhas" });
  });
  const risk = ws.segments.find((s) => /risco/i.test(s.name));
  if (risk && risk.count > 0) alerts.push({ tone: "warn", text: `${num(risk.count)} ${V.customers} em “${risk.name}”. Dispare a mensagem de reativação.`, to: "clientes" });
  upcoming.filter((d) => d.days <= 21).forEach((d) => {
    const planned = ws.posts.some((p) => Math.abs(parseIso(p.date).getTime() - d.dt.getTime()) < 7 * 864e5);
    if (!planned) alerts.push({ tone: "warn", text: `${d.name} em ${d.days} dias e nenhum post planejado na semana.`, to: "calendario" });
  });
  const lastWeek = weeksOf(ws).slice(-1)[0];
  if (lastWeek && Date.now() - parseIso(lastWeek).getTime() > 14 * 864e5) alerts.push({ tone: "neutral", text: `Último registro de resultados é da semana de ${fmtDay(lastWeek)}. Atualize os números.`, to: "resultados" });

  const sales = ws.channels.filter((c) => c.kind === "venda");
  const curRows = ws.weekly.filter((w) => cur.includes(w.week));

  return (
    <div className="grid gap-8">
      <PageHead eyebrow={cur.length ? `Últimas ${cur.length} semanas registradas · ${fmtDay(cur[0])} a ${fmtDay(cur[cur.length - 1])}` : "Visão geral"} title={`Como está o marketing de ${ws.name}`}>
        <Button variant="outline" size="sm" onClick={() => go("resultados")}>Registrar semana</Button>
      </PageHead>

      {ws.example && (
        <p className="text-sm rounded-md border border-warn/40 bg-warn/10 px-4 py-2.5">
          Os números deste negócio são <strong>exemplo</strong> para mostrar o painel funcionando. Apague ou substitua em Resultados e Campanhas.
        </p>
      )}

      {!cur.length ? (
        <Empty title="Nenhum resultado registrado ainda" body={`Registre os ${V.orders}, faturamento e investimento de cada semana por canal. O painel calcula ticket médio, CAC, MER e receita líquida das comissões.`} action={<Button size="sm" onClick={() => go("resultados")}>Registrar a primeira semana</Button>} />
      ) : (
        <>
          <section className="kpis grid grid-cols-2 lg:grid-cols-5 [&>*:last-child]:col-span-2 lg:[&>*:last-child]:col-span-1 gap-px bg-border border rounded-md overflow-hidden">
            <Kpi label={V.orders} value={num(curT.orders)} d={prev.length ? delta(curT.orders, prevT.orders) : undefined} goal={{ pct: curT.orders / (ws.goals.orders * monthFactor), text: `meta ${num(ws.goals.orders)}/mês` }} />
            <Kpi label="Faturamento bruto" value={brl(curT.revenue)} sub={`líquido ${brl(curT.net)}`} d={prev.length ? delta(curT.revenue, prevT.revenue) : undefined} goal={{ pct: curT.revenue / (ws.goals.revenue * monthFactor), text: `meta ${brl(ws.goals.revenue)}/mês` }} />
            <Kpi label="Ticket médio" value={brl(curT.ticket, 2)} d={prev.length ? delta(curT.ticket, prevT.ticket) : undefined} />
            <Kpi label={`CAC · custo por ${V.customer} novo`} value={curT.cac ? brl(curT.cac, 2) : "—"} sub={`meta até ${brl(ws.goals.cac)}`} d={prev.length && prevT.cac ? delta(curT.cac, prevT.cac) : undefined} goodWhenUp={false} />
            <Kpi label="MER · receita ÷ mídia" value={curT.mer ? num(curT.mer, 1) + "×" : "—"} sub={`meta ${num(ws.goals.mer, 1)}×`} d={prev.length && prevT.mer ? delta(curT.mer, prevT.mer) : undefined} />
          </section>

          <div className="grid lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] gap-8">
            <section className="grid gap-4 min-w-0">
              <h2 className="section-title">{V.orders} por semana</h2>
              <WeeklyChart ws={ws} />
            </section>
            <section className="grid gap-3 min-w-0 content-start">
              <h2 className="section-title">Por canal de venda · 4 semanas</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm tabular-nums">
                  <thead className="text-xs text-muted-foreground">
                    <tr className="border-b"><th className="text-left font-medium py-2">Canal</th><th className="text-right font-medium">{V.orders}</th><th className="text-right font-medium">Comissão</th><th className="text-right font-medium">Líquido</th></tr>
                  </thead>
                  <tbody>
                    {sales.map((c) => {
                      const t = totals(ws, curRows.filter((r) => r.channelId === c.id));
                      return (
                        <tr key={c.id} className="border-b last:border-0">
                          <td className="py-2 pr-2">{c.name}<div className="text-[11px] text-muted-foreground">{num(curT.revenue ? (t.revenue / curT.revenue) * 100 : 0)}% da receita</div></td>
                          <td className="text-right">{num(t.orders)}</td>
                          <td className="text-right text-muted-foreground">{c.fee ? `${num(c.fee)}%` : "—"}</td>
                          <td className="text-right font-medium">{brl(t.net)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted-foreground">Comissão perdida no período: <strong className="text-foreground">{brl(curT.revenue - curT.net)}</strong>. Cada {V.order} que migra para canal próprio economiza essa taxa.</p>
            </section>
          </div>
        </>
      )}

      <div className="grid md:grid-cols-3 gap-8">
        <section className="grid gap-3 content-start min-w-0">
          <h2 className="section-title">Pede atenção</h2>
          {alerts.length ? (
            <ul className="grid gap-2">
              {alerts.slice(0, 6).map((a, i) => (
                <li key={i}>
                  <button onClick={() => go(a.to)} className={`alert alert-${a.tone} text-left w-full text-sm`}>{a.text}</button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Nada fora da meta agora.</p>
          )}
        </section>
        <section className="grid gap-3 content-start min-w-0">
          <h2 className="section-title">Próximos 7 dias</h2>
          {nextPosts.length ? (
            <ul className="grid divide-y border-y">
              {nextPosts.slice(0, 6).map((p) => (
                <li key={p.id} className="py-2 flex gap-3 items-baseline text-sm">
                  <span className="font-mono text-xs text-muted-foreground w-11 shrink-0 whitespace-nowrap">{p.date.slice(8)}/{p.date.slice(5, 7)}</span>
                  <span className="min-w-0 flex-1 truncate">{p.title}</span>
                  <span className="text-[11px] text-muted-foreground shrink-0 max-w-[7rem] truncate">{p.format}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Nenhum post para a semana. <button className="underline" onClick={() => go("calendario")}>Planejar no calendário</button></p>
          )}
          <h3 className="eyebrow mt-3">Datas que vendem · 60 dias</h3>
          <ul className="grid gap-1 text-sm">
            {upcoming.slice(0, 5).map((d) => (
              <li key={d.md + d.name} className="flex justify-between gap-3"><span className="min-w-0 truncate">{d.name}</span><span className="text-muted-foreground tabular-nums shrink-0">{d.days === 0 ? "hoje" : `em ${d.days} d`}</span></li>
            ))}
            {!upcoming.length && <li className="text-muted-foreground">Nenhuma data cadastrada nos próximos 60 dias.</li>}
          </ul>
        </section>
        <section className="grid gap-3 content-start min-w-0">
          <h2 className="section-title">Campanhas ativas</h2>
          {active.length ? (
            <ul className="grid divide-y border-y">
              {active.map((c) => (
                <li key={c.id} className="py-2.5 grid gap-1 text-sm">
                  <div className="flex justify-between gap-2"><span className="font-medium truncate">{c.name}</span><span className="tabular-nums shrink-0">{c.spent ? num(c.revenue / c.spent, 1) + "×" : "—"}</span></div>
                  <div className="flex justify-between gap-2 text-xs text-muted-foreground"><span className="truncate">{ch(c.channelId)}{c.coupon && ` · ${c.coupon}`}</span><span className="tabular-nums shrink-0">{brl(c.spent)} de {brl(c.budget)}</span></div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Nenhuma campanha rodando.</p>
          )}
        </section>
      </div>
    </div>
  );
}
