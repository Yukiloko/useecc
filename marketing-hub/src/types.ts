export type ChannelKind = "venda" | "midia" | "relacionamento";

export interface Channel {
  id: string;
  name: string;
  kind: ChannelKind;
  /** Comissão/taxa cobrada pelo canal sobre a venda, em % (ex.: marketplace de delivery). */
  fee: number;
}

export interface Product {
  id: string;
  name: string;
  price: number;
  cost: number;
  hero: boolean;
}

export type PostStatus = "ideia" | "producao" | "agendado" | "publicado";

export interface Post {
  id: string;
  date: string; // YYYY-MM-DD
  title: string;
  channelId: string;
  pillar: string;
  format: string;
  status: PostStatus;
  notes: string;
}

export type CampaignStatus = "planejada" | "ativa" | "pausada" | "encerrada";

export interface Campaign {
  id: string;
  name: string;
  channelId: string;
  objective: string;
  start: string;
  end: string;
  budget: number;
  spent: number;
  orders: number;
  revenue: number;
  coupon: string;
  status: CampaignStatus;
}

export interface Segment {
  id: string;
  name: string;
  rule: string;
  count: number;
  message: string;
}

export interface Journey {
  id: string;
  trigger: string;
  delay: string;
  channelId: string;
  message: string;
  active: boolean;
}

export interface WeeklyEntry {
  id: string;
  week: string; // YYYY-MM-DD (segunda-feira)
  channelId: string;
  orders: number;
  revenue: number;
  adSpend: number;
  newCustomers: number;
}

export interface KeyDate {
  md: string; // MM-DD
  name: string;
}

export interface Goals {
  orders: number; // pedidos / mês
  revenue: number; // faturamento bruto / mês
  cac: number; // custo máximo por cliente novo
  mer: number; // receita ÷ investimento em mídia
}

export interface Vocabulary {
  order: string; // "pedido", "venda", "agendamento"
  orders: string;
  customer: string;
  customers: string;
}

export interface Workspace {
  id: string;
  name: string;
  vertical: string;
  templateId: string;
  color: string;
  createdAt: string;
  vocab: Vocabulary;
  goals: Goals;
  voice: string;
  persona: string;
  hashtags: string;
  formats: string[];
  pillars: string[];
  channels: Channel[];
  products: Product[];
  posts: Post[];
  campaigns: Campaign[];
  segments: Segment[];
  journeys: Journey[];
  weekly: WeeklyEntry[];
  dates: KeyDate[];
  example?: boolean;
}
