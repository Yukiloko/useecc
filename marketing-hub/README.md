# Central de Marketing

Central para gerenciar o marketing de um negócio de delivery (brownies) e replicar a mesma estrutura para outras frentes de negócio.

## O que tem
- **Visão geral**: pedidos, faturamento bruto e líquido de comissões, ticket médio, CAC e MER (receita ÷ mídia) das últimas 4 semanas contra as 4 anteriores e contra a meta; gráfico semanal por canal; alertas (CAC acima da meta, orçamento quase no fim, clientes em risco, data comemorativa sem post).
- **Calendário**: posts por dia com canal, pilar, formato e status; datas que vendem; equilíbrio de pilares no mês.
- **Campanhas**: orçamento, gasto, cupom, pedidos e receita atribuídos, ROAS e custo por pedido.
- **Clientes**: segmentos com quantidade e mensagem pronta (copiar), régua de relacionamento.
- **Resultados**: registro semanal por canal de venda e investimento por canal de mídia.
- **Playbook**: identidade, tom de voz, persona, metas, pilares, formatos, canais com comissão, cardápio com margem, datas.
- **Negócios**: criar a partir de modelos (doceria delivery, restaurante delivery, loja online, serviços com agenda, em branco) ou **replicar a estrutura** do negócio aberto para uma nova frente.

## Estrutura
- `src/types.ts`: modelo de dados (um `Workspace` por negócio).
- `src/templates.ts`: modelos de negócio e a função de replicação.
- `src/store.ts`: persistência (banco do Artifact em `workspaces/<id>`; sem ele, `localStorage`).
- `src/views/*`: telas.

## Build
```bash
pnpm install
./node_modules/.bin/vite build
node scripts/build-artifact.mjs   # gera artifact/central-de-marketing.html
```
