# Prompt: relatório de pedidos do iFood (Claude no Chrome)

Cole o texto abaixo no Claude no Chrome, com o Portal do Parceiro do iFood aberto e logado. Troque o período na primeira linha. O resultado é um CSV no formato que a tela "Importar iFood" da gestão lê.

---

```
Período: de 03/11/2026 até hoje.

Você vai montar um relatório dos meus pedidos do iFood da loja LUV Brownies, usando o Portal do Parceiro do iFood (portal.ifood.com.br), onde já estou logada.

REGRAS DE SEGURANÇA (obrigatórias)
- Só leitura. Não clique em nada que altere a loja: não mude cardápio, preços, horários, promoções, cupons, status da loja, configurações nem dados bancários. Não aceite, cancele ou responda pedidos. Não fale com clientes nem com o suporte.
- Não copie nome, telefone, CPF ou endereço de clientes para o relatório.
- Se aparecer login, código de verificação, termo de aceite ou qualquer confirmação, pare e me avise.
- Nunca invente valores. Se um valor não estiver visível, deixe a célula vazia e explique na coluna observacoes.

ONDE BUSCAR
1. Primeiro procure em Financeiro um relatório por pedido (nomes possíveis: Conciliação, Extrato, Repasses, Relatório financeiro). Se houver exportação em Excel/CSV, use os dados dela.
2. Para os itens de cada pedido (quais produtos e quantidades) e para o que faltar, abra a tela de Pedidos / Histórico de pedidos e o detalhe de cada pedido do período.
3. Inclua pedidos cancelados, com status "cancelado" e os valores que o portal mostrar para eles.

O QUE ENTREGAR
Um CSV com separador ponto e vírgula (;), uma linha por pedido, exatamente com este cabeçalho e nesta ordem:

pedido_id;data;hora;status;itens;subtotal_itens;taxa_entrega_cliente;desconto_loja;desconto_ifood;comissao;taxa_pagamento;outras_taxas;valor_liquido;data_repasse;repasse_status;observacoes

Como preencher cada coluna:
- pedido_id: número/código do pedido como aparece no portal (o curto, se houver os dois, coloque o curto aqui e o longo em observacoes).
- data: data do pedido no formato AAAA-MM-DD. hora: HH:MM.
- status: concluido ou cancelado.
- itens: todos os itens do pedido, separados por " | ", no formato QTDx NOME @PRECO_UNITARIO. Se o item tiver sabores escolhidos (como Dupla ou Caixa Presente), coloque os sabores entre parênteses, separados por vírgula, um por brownie.
  Exemplo: 2x Tradicional @10,00 | 1x Dupla (Nutella, Brookie) @20,00
  Use os nomes do meu cardápio: Tradicional, Red Velvet, Brookie, Nutella, Dupla, Caixa Presente. Se o nome no iFood for diferente, use o do cardápio que corresponde e anote o nome original em observacoes. Adicionais pagos entram como itens próprios.
- Valores em reais, sem "R$", com vírgula decimal e sem separador de milhar (ex.: 1234,50). Todos positivos; descontos e taxas também vão positivos.
- subtotal_itens: soma dos itens, antes de qualquer desconto.
- taxa_entrega_cliente: taxa de entrega paga pelo cliente (0 se não houve).
- desconto_loja: descontos, cupons e campanhas pagos pela LOJA (que saem do meu repasse).
- desconto_ifood: descontos, cupons e campanhas pagos pelo IFOOD (que não saem do meu repasse).
- comissao: comissão do iFood sobre o pedido.
- taxa_pagamento: taxa de pagamento online / transação.
- outras_taxas: qualquer outra cobrança ligada ao pedido (entrega, anúncio, mensalidade rateada etc.). Descreva o que é em observacoes.
- valor_liquido: quanto o iFood vai me repassar (ou repassou) por esse pedido.
- data_repasse: data do repasse em AAAA-MM-DD (prevista ou realizada).
- repasse_status: previsto ou pago.
- observacoes: tudo que precisar explicar; vazio se não houver nada.

CONFERÊNCIA ANTES DE ENTREGAR
Para cada pedido, confira se: valor_liquido = subtotal_itens − desconto_loja − comissao − taxa_pagamento − outras_taxas (considerando a taxa de entrega, se ela entrar no repasse). Se não bater, mantenha os valores do portal e explique a diferença em observacoes.

FORMA DE ENTREGA
1. Se conseguir, gere um arquivo ifood-pedidos.csv para download. Em todo caso, mostre o CSV completo num bloco de código, sem cortar linhas.
2. Depois do CSV, escreva um resumo curto: número de pedidos (concluídos e cancelados), soma do subtotal, dos descontos da loja, dos descontos do iFood, da comissão, das taxas e do valor líquido; e a lista do que não encontrou ou ficou em dúvida.
```

---

## Formato (para a importação)

| Coluna | Tipo | Uso na gestão |
|---|---|---|
| `pedido_id` | texto | identifica o pedido; reimportar não duplica |
| `data`, `hora` | AAAA-MM-DD, HH:MM | data da venda |
| `status` | `concluido` / `cancelado` | cancelado não vira venda |
| `itens` | `QTDx NOME (SABOR, SABOR) @PRECO` separados por ` \| ` | produtos, estoque e custo |
| `subtotal_itens` | número | receita bruta |
| `taxa_entrega_cliente` | número | informativo (entrega feita pelo iFood) |
| `desconto_loja` | número | desconto da venda (reduz a receita) |
| `desconto_ifood` | número | informativo (não reduz a receita) |
| `comissao`, `taxa_pagamento`, `outras_taxas` | número | comissão e taxas da venda |
| `valor_liquido` | número | valor a receber no caixa |
| `data_repasse` | AAAA-MM-DD | vencimento do recebimento |
| `repasse_status` | `previsto` / `pago` | recebimento pendente ou baixado |
| `observacoes` | texto | guardado na venda |
