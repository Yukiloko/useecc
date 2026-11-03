import type { Channel, Journey, KeyDate, Segment, Vocabulary, Workspace, Goals, Product } from "./types";

export const uid = () => Math.random().toString(36).slice(2, 10);

interface TemplateDef {
  id: string;
  label: string;
  vertical: string;
  blurb: string;
  color: string;
  vocab: Vocabulary;
  goals: Goals;
  voice: string;
  persona: string;
  hashtags: string;
  formats: string[];
  pillars: string[];
  channels: Omit<Channel, "id">[];
  products: Omit<Product, "id">[];
  segments: Omit<Segment, "id" | "count">[];
  journeys: (Omit<Journey, "id" | "channelId" | "active"> & { channel: string })[];
  dates: KeyDate[];
}

const deliveryVocab: Vocabulary = { order: "pedido", orders: "pedidos", customer: "cliente", customers: "clientes" };

const commonDates: KeyDate[] = [
  { md: "02-14", name: "Valentine's / esquenta Namorados" },
  { md: "03-15", name: "Dia do Consumidor" },
  { md: "05-12", name: "Dia das Mães (2º domingo, conferir)" },
  { md: "06-12", name: "Dia dos Namorados" },
  { md: "08-10", name: "Dia dos Pais (2º domingo, conferir)" },
  { md: "10-12", name: "Dia das Crianças" },
  { md: "11-28", name: "Black Friday (última sexta, conferir)" },
  { md: "12-25", name: "Natal" },
];

export const TEMPLATES: TemplateDef[] = [
  {
    id: "doceria-delivery",
    label: "Doceria delivery",
    vertical: "Brownies e doces por delivery",
    blurb: "Marketplaces de delivery, Instagram e WhatsApp. Foco em recompra e datas de presente.",
    color: "#6B3A22",
    vocab: deliveryVocab,
    goals: { orders: 900, revenue: 42000, cac: 18, mer: 6 },
    voice: "Próxima, divertida e indulgente. Falamos de prazer sem culpa, com humor leve. Frases curtas, emoji com moderação (🍫 no máximo um por post).",
    persona: "Mulheres e homens de 22–38 anos, moram a até 6 km da cozinha, pedem doce à noite (19h–23h) e em fins de semana. Compram para si e para presentear.",
    hashtags: "#brownie #brownierecheado #docedelivery #chocolate",
    formats: ["Reels", "Carrossel", "Stories", "Foto", "Live", "Status WhatsApp"],
    pillars: ["Desejo (close no recheio)", "Bastidores da cozinha", "Prova social", "Presente / ocasião", "Oferta"],
    channels: [
      { name: "iFood", kind: "venda", fee: 23 },
      { name: "WhatsApp / pedido direto", kind: "venda", fee: 0 },
      { name: "Instagram", kind: "midia", fee: 0 },
      { name: "Meta Ads", kind: "midia", fee: 0 },
      { name: "Lista de transmissão WhatsApp", kind: "relacionamento", fee: 0 },
    ],
    products: [
      { name: "Brownie tradicional", price: 12, cost: 4.2, hero: false },
      { name: "Brownie recheado de Ninho com Nutella", price: 18, cost: 6.5, hero: true },
      { name: "Caixa presente 6 un.", price: 79, cost: 28, hero: true },
    ],
    segments: [
      { name: "Novos (1 pedido)", rule: "1 pedido nos últimos 30 dias", message: "Oi, {nome}! Que bom que você provou nosso brownie 🍫 Seu cupom de 10% para o 2º pedido: VOLTA10. Vale 15 dias." },
      { name: "Recorrentes", rule: "2–4 pedidos em 60 dias", message: "{nome}, chegou sabor novo e você prova primeiro. Quer que eu separe um pra hoje?" },
      { name: "Fãs (VIP)", rule: "5+ pedidos em 90 dias", message: "{nome}, você é da casa! Este mês tem brownie extra na sua caixa, por nossa conta." },
      { name: "Em risco", rule: "Sem pedir há 30–60 dias", message: "Sentimos sua falta, {nome}. Frete grátis pra você até domingo com o cupom SAUDADE." },
      { name: "Inativos", rule: "Sem pedir há 60+ dias", message: "{nome}, mudou muita coisa por aqui: sabores novos e caixa presente. Dá uma olhada no cardápio?" },
    ],
    journeys: [
      { trigger: "Pedido entregue", delay: "D+1", channel: "WhatsApp / pedido direto", message: "Pedir avaliação no iFood + foto no stories marcando o perfil." },
      { trigger: "1º pedido", delay: "D+7", channel: "WhatsApp / pedido direto", message: "Cupom de 2º pedido (VOLTA10), validade 15 dias." },
      { trigger: "Sem pedir", delay: "D+30", channel: "Lista de transmissão WhatsApp", message: "Oferta de reativação com frete grátis." },
      { trigger: "Aniversário do cliente", delay: "D-3", channel: "WhatsApp / pedido direto", message: "Brownie de presente no pedido da semana do aniversário." },
    ],
    dates: [
      ...commonDates,
      { md: "04-05", name: "Páscoa (data móvel, conferir)" },
      { md: "07-07", name: "Dia Mundial do Chocolate" },
      { md: "12-08", name: "Dia do Brownie nos EUA (gancho de conteúdo)" },
    ],
  },
  {
    id: "restaurante-delivery",
    label: "Restaurante delivery",
    vertical: "Hamburgueria, pizzaria, marmita",
    blurb: "Mesmo motor da doceria com picos de almoço e jantar e combos como produto de entrada.",
    color: "#B5441B",
    vocab: deliveryVocab,
    goals: { orders: 1500, revenue: 75000, cac: 22, mer: 7 },
    voice: "Direta, com fome e sem frescura. Mostrar o produto grande, quente e suculento.",
    persona: "Jovens adultos 18–35 que pedem 2+ vezes por semana, sensíveis a combo e frete.",
    hashtags: "#delivery #hamburguer #combo",
    formats: ["Reels", "Carrossel", "Stories", "Foto"],
    pillars: ["Produto em close", "Combo do dia", "Bastidores", "Prova social", "Oferta"],
    channels: [
      { name: "iFood", kind: "venda", fee: 23 },
      { name: "App / site próprio", kind: "venda", fee: 4 },
      { name: "Instagram", kind: "midia", fee: 0 },
      { name: "Meta Ads", kind: "midia", fee: 0 },
      { name: "WhatsApp", kind: "relacionamento", fee: 0 },
    ],
    products: [{ name: "Combo da casa", price: 39.9, cost: 15, hero: true }],
    segments: [
      { name: "Novos", rule: "1 pedido em 30 dias", message: "Valeu pelo pedido, {nome}! No próximo, batata grátis com o cupom VOLTA." },
      { name: "Recorrentes", rule: "2+ pedidos em 30 dias", message: "{nome}, o combo da semana já está no ar." },
      { name: "Em risco", rule: "Sem pedir há 21–45 dias", message: "{nome}, faz tempo! Frete grátis hoje." },
      { name: "Inativos", rule: "Sem pedir há 45+ dias", message: "{nome}, temos novidade no cardápio." },
    ],
    journeys: [
      { trigger: "Pedido entregue", delay: "D+1", channel: "WhatsApp", message: "Pedir avaliação." },
      { trigger: "Sem pedir", delay: "D+21", channel: "WhatsApp", message: "Cupom de reativação." },
    ],
    dates: [...commonDates, { md: "05-28", name: "Dia do Hambúrguer" }, { md: "07-10", name: "Dia da Pizza" }],
  },
  {
    id: "ecommerce",
    label: "Loja online",
    vertical: "Moda, cosméticos, presentes",
    blurb: "Troca pedido por venda, adiciona e-mail e carrinho abandonado na régua.",
    color: "#2F5D62",
    vocab: { order: "venda", orders: "vendas", customer: "cliente", customers: "clientes" },
    goals: { orders: 400, revenue: 60000, cac: 45, mer: 4 },
    voice: "Inspiradora e clara. Mostrar uso real, tamanhos e benefícios antes do preço.",
    persona: "Defina aqui quem compra, onde vive e o que a faz comprar.",
    hashtags: "",
    formats: ["Reels", "Carrossel", "Stories", "E-mail", "Foto"],
    pillars: ["Lançamento", "Como usar", "Prova social", "Bastidores", "Oferta"],
    channels: [
      { name: "Site (loja virtual)", kind: "venda", fee: 5 },
      { name: "Marketplace", kind: "venda", fee: 16 },
      { name: "Instagram", kind: "midia", fee: 0 },
      { name: "Meta Ads", kind: "midia", fee: 0 },
      { name: "Google Ads", kind: "midia", fee: 0 },
      { name: "E-mail", kind: "relacionamento", fee: 0 },
    ],
    products: [],
    segments: [
      { name: "Novos", rule: "1 compra", message: "Bem-vinda, {nome}! 10% na próxima com BEMVINDA." },
      { name: "Recorrentes", rule: "2+ compras em 180 dias", message: "{nome}, chegou coleção nova e você vê antes." },
      { name: "Carrinho abandonado", rule: "Carrinho sem compra em 24h", message: "{nome}, seus itens ainda estão reservados." },
      { name: "Inativos", rule: "Sem comprar há 180+ dias", message: "{nome}, sentimos sua falta." },
    ],
    journeys: [
      { trigger: "Carrinho abandonado", delay: "H+2", channel: "E-mail", message: "Lembrete com foto do produto." },
      { trigger: "Compra entregue", delay: "D+5", channel: "E-mail", message: "Pedir avaliação com foto." },
    ],
    dates: commonDates,
  },
  {
    id: "servicos",
    label: "Serviços com agenda",
    vertical: "Estética, clínica, estúdio, aulas",
    blurb: "Troca pedido por agendamento e mede custo por agendamento e retorno.",
    color: "#5B4B8A",
    vocab: { order: "agendamento", orders: "agendamentos", customer: "paciente/cliente", customers: "pacientes/clientes" },
    goals: { orders: 200, revenue: 40000, cac: 60, mer: 5 },
    voice: "Acolhedora e profissional. Explicar o resultado e tirar dúvidas antes de vender.",
    persona: "Defina aqui quem agenda e qual dor resolve.",
    hashtags: "",
    formats: ["Reels", "Carrossel", "Stories", "Antes e depois", "Live"],
    pillars: ["Educação", "Antes e depois", "Prova social", "Bastidores", "Oferta"],
    channels: [
      { name: "WhatsApp / agenda", kind: "venda", fee: 0 },
      { name: "App de agendamento", kind: "venda", fee: 8 },
      { name: "Instagram", kind: "midia", fee: 0 },
      { name: "Google Meu Negócio", kind: "midia", fee: 0 },
      { name: "Meta Ads", kind: "midia", fee: 0 },
    ],
    products: [],
    segments: [
      { name: "1ª visita", rule: "1 atendimento", message: "{nome}, como você se sentiu após o atendimento?" },
      { name: "Retorno pendente", rule: "Passou do prazo de retorno", message: "{nome}, já está na hora do seu retorno. Quer que eu reserve um horário?" },
      { name: "Fiéis", rule: "4+ atendimentos no ano", message: "{nome}, você tem prioridade na agenda deste mês." },
    ],
    journeys: [
      { trigger: "Atendimento realizado", delay: "D+1", channel: "WhatsApp / agenda", message: "Pós-atendimento e pedido de avaliação no Google." },
      { trigger: "Prazo de retorno", delay: "D+30", channel: "WhatsApp / agenda", message: "Convite para reagendar." },
    ],
    dates: commonDates,
  },
  {
    id: "em-branco",
    label: "Em branco",
    vertical: "Qualquer negócio",
    blurb: "Só a estrutura: você define canais, pilares, segmentos e metas.",
    color: "#3D4A5C",
    vocab: { order: "venda", orders: "vendas", customer: "cliente", customers: "clientes" },
    goals: { orders: 100, revenue: 10000, cac: 30, mer: 4 },
    voice: "",
    persona: "",
    hashtags: "",
    formats: ["Reels", "Carrossel", "Stories", "Foto"],
    pillars: ["Produto", "Bastidores", "Prova social", "Oferta"],
    channels: [
      { name: "Canal de venda principal", kind: "venda", fee: 0 },
      { name: "Instagram", kind: "midia", fee: 0 },
    ],
    products: [],
    segments: [],
    journeys: [],
    dates: commonDates,
  },
];

export function buildWorkspace(templateId: string, name: string): Workspace {
  const t = TEMPLATES.find((x) => x.id === templateId) ?? TEMPLATES[TEMPLATES.length - 1];
  const channels = t.channels.map((c) => ({ ...c, id: uid() }));
  const byName = (n: string) => channels.find((c) => c.name === n)?.id ?? channels[0]?.id ?? "";
  return {
    id: uid(),
    name: name.trim() || t.label,
    vertical: t.vertical,
    templateId: t.id,
    color: t.color,
    createdAt: new Date().toISOString(),
    vocab: { ...t.vocab },
    goals: { ...t.goals },
    voice: t.voice,
    persona: t.persona,
    hashtags: t.hashtags,
    formats: [...t.formats],
    pillars: [...t.pillars],
    channels,
    products: t.products.map((p) => ({ ...p, id: uid() })),
    segments: t.segments.map((s) => ({ ...s, id: uid(), count: 0 })),
    journeys: t.journeys.map(({ channel, ...j }) => ({ ...j, id: uid(), channelId: byName(channel), active: true })),
    weekly: [],
    posts: [],
    campaigns: [],
    dates: [...t.dates],
  };
}

/** Copia a estrutura (canais, pilares, segmentos, réguas, metas, datas) sem os dados do dia a dia. */
export function replicateWorkspace(src: Workspace, name: string, vertical: string): Workspace {
  const idMap = new Map<string, string>();
  const channels = src.channels.map((c) => {
    const id = uid();
    idMap.set(c.id, id);
    return { ...c, id };
  });
  return {
    ...structuredClone(src),
    id: uid(),
    name: name.trim() || src.name + " (cópia)",
    vertical: vertical.trim() || src.vertical,
    createdAt: new Date().toISOString(),
    channels,
    products: [],
    segments: src.segments.map((s) => ({ ...s, id: uid(), count: 0 })),
    journeys: src.journeys.map((j) => ({ ...j, id: uid(), channelId: idMap.get(j.channelId) ?? channels[0]?.id ?? "" })),
    posts: [],
    campaigns: [],
    weekly: [],
    example: false,
  };
}
