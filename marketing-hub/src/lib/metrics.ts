import type { Workspace, WeeklyEntry } from "../types";

export const brl = (n: number, digits = 0) =>
  (Number.isFinite(n) ? n : 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: digits, minimumFractionDigits: digits });
export const num = (n: number, digits = 0) =>
  (Number.isFinite(n) ? n : 0).toLocaleString("pt-BR", { maximumFractionDigits: digits, minimumFractionDigits: digits });

export function mondayOf(d: Date) {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const day = (x.getDay() + 6) % 7;
  x.setDate(x.getDate() - day);
  return x;
}
export const iso = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
export const parseIso = (s: string) => {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, (m || 1) - 1, d || 1);
};
export const fmtDay = (s: string) => parseIso(s).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });

export interface Totals {
  orders: number;
  revenue: number;
  net: number;
  adSpend: number;
  newCustomers: number;
  ticket: number;
  cac: number;
  mer: number;
}

export function totals(ws: Workspace, rows: WeeklyEntry[]): Totals {
  const fee = (id: string) => ws.channels.find((c) => c.id === id)?.fee ?? 0;
  const t = rows.reduce(
    (a, r) => {
      a.orders += r.orders;
      a.revenue += r.revenue;
      a.net += r.revenue * (1 - fee(r.channelId) / 100);
      a.adSpend += r.adSpend;
      a.newCustomers += r.newCustomers;
      return a;
    },
    { orders: 0, revenue: 0, net: 0, adSpend: 0, newCustomers: 0 },
  );
  return {
    ...t,
    ticket: t.orders ? t.revenue / t.orders : 0,
    cac: t.newCustomers ? t.adSpend / t.newCustomers : 0,
    mer: t.adSpend ? t.revenue / t.adSpend : 0,
  };
}

/** Semanas distintas registradas, da mais antiga para a mais recente. */
export const weeksOf = (ws: Workspace) => Array.from(new Set(ws.weekly.map((w) => w.week))).sort();

export function periods(ws: Workspace) {
  const weeks = weeksOf(ws);
  const cur = weeks.slice(-4);
  const prev = weeks.slice(-8, -4);
  return {
    weeks,
    cur,
    prev,
    curT: totals(ws, ws.weekly.filter((w) => cur.includes(w.week))),
    prevT: totals(ws, ws.weekly.filter((w) => prev.includes(w.week))),
  };
}

export const delta = (a: number, b: number) => (b ? (a - b) / b : 0);
