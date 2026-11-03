import type { ReactNode } from "react";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { Workspace } from "./types";

export interface ViewProps {
  ws: Workspace;
  update: (fn: (d: Workspace) => void) => void;
  go: (view: string) => void;
}

export function PageHead({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 border-b pb-5">
      <div className="min-w-0">
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="font-display text-2xl md:text-[1.75rem] leading-tight mt-1 text-balance">{title}</h1>
      </div>
      {children && <div className="flex flex-wrap gap-2">{children}</div>}
    </header>
  );
}

export function Field({ label, htmlFor, children, hint, className }: { label: string; htmlFor: string; children: ReactNode; hint?: string; className?: string }) {
  return (
    <div className={cn("grid gap-1.5 min-w-0", className)}>
      <Label htmlFor={htmlFor} className="text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      {children}
      {hint && <p className="text-[11px] text-muted-foreground">{hint}</p>}
    </div>
  );
}

const TONES: Record<string, string> = {
  good: "bg-good/12 text-good border-good/30",
  warn: "bg-warn/12 text-warn border-warn/30",
  bad: "bg-bad/12 text-bad border-bad/30",
  neutral: "bg-muted text-muted-foreground border-border",
  brand: "bg-brand/12 text-brand-ink border-brand/30",
};

export function Pill({ tone = "neutral", children, className }: { tone?: keyof typeof TONES | string; children: ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium whitespace-nowrap", TONES[tone] ?? TONES.neutral, className)}>
      {children}
    </span>
  );
}

export function Empty({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="border border-dashed rounded-md px-5 py-8 text-center grid gap-2 justify-items-center">
      <p className="font-medium">{title}</p>
      <p className="text-sm text-muted-foreground max-w-[46ch]">{body}</p>
      {action}
    </div>
  );
}

export const selectCls =
  "flex h-9 w-full rounded-md border border-input bg-card px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";
