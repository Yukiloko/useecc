import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { PageHead, Empty, selectCls, type ViewProps } from "../ui";
import { num } from "../lib/metrics";
import { uid } from "../templates";
import { toast } from "sonner";

async function copy(text: string, el?: HTMLElement | null) {
  try {
    await navigator.clipboard.writeText(text);
    toast.success("Mensagem copiada");
  } catch {
    if (el instanceof HTMLTextAreaElement) {
      el.focus();
      el.select();
    }
    toast("Selecionei o texto. Use Ctrl+C / Copiar.");
  }
}

export function Customers({ ws, update }: ViewProps) {
  const V = ws.vocab;
  const total = ws.segments.reduce((a, s) => a + s.count, 0);
  const max = Math.max(1, ...ws.segments.map((s) => s.count));
  return (
    <div className="grid gap-8">
      <PageHead eyebrow={`${V.customers} e relacionamento`} title="Segmentos, mensagens e régua de contato">
        <Button size="sm" variant="outline" onClick={() => update((d) => { d.segments.push({ id: uid(), name: "Novo segmento", rule: "", count: 0, message: "Oi, {nome}!" }); })}>Novo segmento</Button>
      </PageHead>

      <section className="grid gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="section-title">Segmentos da base · {num(total)} {V.customers}</h2>
          <p className="text-xs text-muted-foreground">Atualize as quantidades a partir da sua lista de {V.customers} ou do relatório do marketplace. Use {"{nome}"} na mensagem.</p>
        </div>
        {ws.segments.length === 0 && <Empty title="Sem segmentos" body="Separe sua base por comportamento (novos, recorrentes, em risco) e tenha uma mensagem pronta para cada grupo." />}
        <ul className="grid gap-px bg-border border rounded-md overflow-hidden">
          {ws.segments.map((s, i) => (
            <li key={s.id} className="bg-card p-4 grid md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)] gap-4">
              <div className="grid gap-2 content-start">
                <Input id={`seg-name-${s.id}`} aria-label="Nome do segmento" className="font-medium h-8" value={s.name} onChange={(e) => update((d) => { d.segments[i].name = e.target.value; })} />
                <Input id={`seg-rule-${s.id}`} aria-label="Regra" className="h-8 text-xs" placeholder="Regra: ex. sem pedir há 30 dias" value={s.rule} onChange={(e) => update((d) => { d.segments[i].rule = e.target.value; })} />
                <div className="flex items-center gap-2">
                  <Input id={`seg-count-${s.id}`} aria-label={`Quantidade de ${V.customers}`} type="number" min={0} className="h-8 w-24 tabular-nums" value={s.count || ""} placeholder="0" onChange={(e) => update((d) => { d.segments[i].count = Number(e.target.value); })} />
                  <div className="flex-1 h-1.5 bg-muted rounded-full"><div className="h-1.5 rounded-full bg-brand" style={{ width: `${(s.count / max) * 100}%` }} /></div>
                </div>
              </div>
              <div className="grid gap-2 min-w-0">
                <Textarea id={`seg-msg-${s.id}`} aria-label="Mensagem" rows={3} value={s.message} onChange={(e) => update((d) => { d.segments[i].message = e.target.value; })} />
                <div className="flex flex-wrap gap-2 justify-end">
                  <Button size="sm" variant="ghost" className="text-muted-foreground" onClick={() => update((d) => { d.segments.splice(i, 1); })}>Remover</Button>
                  <Button size="sm" variant="outline" onClick={(e) => copy(s.message, (e.currentTarget.closest("li") as HTMLElement)?.querySelector("textarea"))}>Copiar mensagem</Button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="grid gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="section-title">Régua de relacionamento</h2>
          <Button size="sm" variant="outline" onClick={() => update((d) => { d.journeys.push({ id: uid(), trigger: "Novo gatilho", delay: "D+1", channelId: d.channels[0]?.id ?? "", message: "", active: true }); })}>Novo contato</Button>
        </div>
        <p className="text-xs text-muted-foreground -mt-1">Cada linha é um contato automático ou manual que acontece depois de um gatilho. D+1 = um dia depois; H+2 = duas horas depois.</p>
        <div className="overflow-x-auto border rounded-md">
          <table className="w-full text-sm min-w-[720px]">
            <thead className="text-xs text-muted-foreground bg-muted/50">
              <tr className="border-b">
                <th className="text-left font-medium px-3 py-2">Gatilho</th>
                <th className="text-left font-medium px-2">Quando</th>
                <th className="text-left font-medium px-2">Canal</th>
                <th className="text-left font-medium px-2">O que enviar</th>
                <th className="text-center font-medium px-2">Ativo</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {ws.journeys.map((j, i) => (
                <tr key={j.id} className={`border-b last:border-0 ${j.active ? "" : "opacity-55"}`}>
                  <td className="px-2 py-1.5 w-44"><Input id={`jr-trigger-${j.id}`} aria-label="Gatilho" className="h-8" value={j.trigger} onChange={(e) => update((d) => { d.journeys[i].trigger = e.target.value; })} /></td>
                  <td className="px-2 py-1.5 w-20"><Input id={`jr-delay-${j.id}`} aria-label="Quando" className="h-8 font-mono" value={j.delay} onChange={(e) => update((d) => { d.journeys[i].delay = e.target.value; })} /></td>
                  <td className="px-2 py-1.5 w-48">
                    <select id={`jr-ch-${j.id}`} aria-label="Canal" className={selectCls + " h-8"} value={j.channelId} onChange={(e) => update((d) => { d.journeys[i].channelId = e.target.value; })}>
                      {ws.channels.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </td>
                  <td className="px-2 py-1.5"><Input id={`jr-msg-${j.id}`} aria-label="O que enviar" className="h-8" value={j.message} onChange={(e) => update((d) => { d.journeys[i].message = e.target.value; })} /></td>
                  <td className="px-2 text-center"><Switch id={`jr-on-${j.id}`} aria-label="Ativo" checked={j.active} onCheckedChange={(v) => update((d) => { d.journeys[i].active = v; })} /></td>
                  <td className="px-2"><Button size="sm" variant="ghost" aria-label="Remover contato" className="text-muted-foreground" onClick={() => update((d) => { d.journeys.splice(i, 1); })}>×</Button></td>
                </tr>
              ))}
              {ws.journeys.length === 0 && <tr><td colSpan={6} className="px-3 py-4 text-sm text-muted-foreground">Nenhum contato na régua.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
