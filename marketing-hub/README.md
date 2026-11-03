# Central de Marketing

Central para gerenciar o marketing de uma marca de brownies que vende por delivery. A mesma estrutura pode ser copiada para outras frentes de negócio.

## Telas

A visão geral mostra pedidos, faturamento bruto e líquido (já descontada a comissão de cada canal), ticket médio, CAC e MER (faturamento dividido pelo investimento em mídia). Compara as últimas 4 semanas com as 4 anteriores e com a meta, e lista o que pede atenção: CAC acima da meta, orçamento quase no fim, clientes em risco e data comemorativa sem post.

No calendário ficam os posts de cada dia, com canal, pilar, formato e status, além das datas que vendem. Em campanhas você registra orçamento, gasto, cupom, pedidos e receita, e a tela calcula ROAS e custo por pedido. Em clientes ficam os grupos da base, cada um com uma mensagem pronta para copiar, e a sequência de contatos depois de cada pedido. Em resultados você lança os números da semana por canal.

O playbook guarda tom de voz, público, metas, pilares, formatos, canais com comissão, cardápio com margem e datas. Em negócios você cria uma frente nova a partir de um modelo (doceria delivery, restaurante delivery, loja online, serviços com agenda ou em branco) ou replica a estrutura do negócio aberto.

## Código

- `src/types.ts`: modelo de dados, com um `Workspace` por negócio.
- `src/templates.ts`: modelos de negócio e a função de replicação.
- `src/store.ts`: salva cada negócio no banco do Artifact em `workspaces/<id>`. Fora do claude.ai, salva no `localStorage`.
- `src/views/`: uma tela por arquivo.

## Build

```bash
pnpm install
./node_modules/.bin/vite build
node scripts/build-artifact.mjs   # gera artifact/central-de-marketing.html
```
