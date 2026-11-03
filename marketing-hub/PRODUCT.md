# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Uma pessoa só: a dona ou o dono da marca de brownies. Ela planeja o conteúdo, posta, cria as promoções, lança os números da semana e decide onde investir, tudo sozinha e no meio da operação da cozinha. Não há social media, equipe nem agência usando a ferramenta.

## Product Purpose

Juntar num lugar só o marketing de uma marca de brownies que vende por delivery: o que postar e quando, quais campanhas e cupons estão rodando, quanto cada canal vende e quanto fica depois das comissões, e com quais grupos de clientes falar. O sucesso é a dona saber em poucos minutos por semana se o marketing está dando retorno e o que fazer em seguida.

A mesma estrutura precisa poder ser replicada para outras frentes de negócio. Quais frentes serão ainda não está definido; a ferramenta deve estar pronta para quando surgirem.

## Positioning

Pensada para quem vende comida por delivery e paga comissão de marketplace: mostra o faturamento líquido por canal e quanto foi perdido em comissão, e organiza a recompra pelo WhatsApp. A estrutura de um negócio (canais, comissões, segmentos, régua de contato, metas e datas) pode ser copiada para outra frente sem levar os dados.

## Operating Context

- Canais de venda atuais: iFood, WhatsApp / pedido direto, site ou app próprio e outros marketplaces. 99Food entra em breve.
- Divulgação no Instagram e anúncios no Meta Ads; relacionamento por WhatsApp (conversa e lista de transmissão).
- Os números vêm dos painéis de cada canal e são lançados à mão uma vez por semana. Não há integração automática.
- Datas comemorativas (Páscoa, Dia dos Namorados, Dia do Chocolate, Black Friday, Natal) puxam campanhas e conteúdo.

## Capabilities and Constraints

- App React publicado como Artifact no claude.ai, privado para a dona; os dados de cada negócio ficam no banco do Artifact (`workspaces/<id>`), com `localStorage` como reserva fora do claude.ai.
- Telas: visão geral, calendário de conteúdo, campanhas, clientes e régua de relacionamento, resultados semanais, playbook do negócio e negócios (modelos e replicação).
- Termos usados: pedido, ticket médio, comissão, faturamento líquido, CAC, MER (faturamento ÷ investimento em mídia), ROAS, régua de relacionamento, segmentos, pilares de conteúdo.
- Em aberto: quais serão as outras frentes de negócio; quando a 99Food entra; se haverá integração automática com os canais.

## Brand Commitments

Nenhum ainda. Nome, tom de voz, cores e fontes da marca de brownies não estão definidos. O negócio de exemplo se chama "Brownieria (exemplo)" e não representa a marca real.

## Evidence on Hand

- Os números, posts e campanhas do negócio de exemplo são fictícios e estão marcados como exemplo na interface.
- Não existem ainda dados reais de vendas, depoimentos, avaliações ou fotos de produto. Não inventar.

## Product Principles

- Uma pessoa, poucos minutos por semana: cada tela precisa responder rápido o que está bom, o que está fora da meta e o que fazer.
- Mostrar dinheiro de verdade: faturamento líquido de comissão vale mais que faturamento bruto.
- Replicável por estrutura: o que é de um negócio específico fica nos dados; o que serve para qualquer frente fica no modelo.
- Nada de número inventado: o que não foi lançado aparece vazio, com o caminho para lançar.
