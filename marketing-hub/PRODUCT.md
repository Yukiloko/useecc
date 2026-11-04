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

- Cuiabá (MT). Produção na cozinha de casa, à noite (18h às 22h) e nos fins de semana, porque a dona tem outro emprego das 8h às 18h.
- Canais de venda: iFood como vitrine (comissão de 23% mais 3,2% de pagamento online) e WhatsApp com o sistema Anota AI, com entrega pelo iFood ou retirada sem taxa. A meta do plano é levar a maior parte das vendas para o WhatsApp e a retirada. A 99Food não é usada hoje; entrar nela é só uma possibilidade, sem data.
- Divulgação no Instagram e anúncios no Meta Ads; relacionamento por WhatsApp (conversa e lista de transmissão).
- Os números vêm dos painéis de cada canal e são lançados à mão uma vez por semana. Não há integração automática.
- Datas comemorativas (Páscoa, Dia dos Namorados, Dia do Chocolate, Black Friday, Natal) puxam campanhas e conteúdo.

## Capabilities and Constraints

- App React publicado como Artifact no claude.ai, privado para a dona; os dados de cada negócio ficam no banco do Artifact (`workspaces/<id>`), com `localStorage` como reserva fora do claude.ai.
- Telas: visão geral, calendário de conteúdo, campanhas, clientes e régua de relacionamento, resultados semanais, playbook do negócio e negócios (modelos e replicação).
- Termos usados: pedido, ticket médio, comissão, faturamento líquido, CAC, MER (faturamento ÷ investimento em mídia), ROAS, régua de relacionamento, segmentos, pilares de conteúdo.
- Em aberto: quais serão as outras frentes de negócio; se a 99Food vai entrar e quando; se haverá integração automática com os canais.

## Brand Commitments

- Nome: LUV Brownies. Instagram: @luv.browniess.
- Identidade (artes no Canva: "LUV-posts-editavel", "Menu de sabores da LUV Brownies", "Post de apresentação da LUV Brownies"): vermelho #B5122F, creme #FFF1DC e marrom chocolate; mascote de um brownie que anda; letreiro "LUV" em letras grossas e arredondadas.
- Voz: o LUV fala em primeira pessoa ("Prazer, eu sou o LUV"), com humor leve e frases curtas. Promessa: "Seu novo brownie favorito." Textura: "casquinha por fora, molhadinho por dentro". Chamada: "Peça pelo link na bio ou pelo direct."
- Cardápio do plano (brownies de 80 g): Tradicional R$ 10, Red Velvet R$ 12, Brookie R$ 12, Nutella R$ 15, Dupla R$ 20 e Caixa Presente com 4 sabores e cartão escrito à mão R$ 45. As artes do Canva citam "Com Cobertura" no lugar da Nutella; qual fica no cardápio está em aberto.
- Decisões da dona: sem cupom, sem frete grátis e sem oferta de abertura. Garantia "Chegou Inteiro": foto em até 1 hora e devolução do valor do item por Pix.

## Evidence on Hand

- Os números, posts e campanhas do negócio de exemplo são fictícios e estão marcados como exemplo na interface.
- Fotos de produto no Google Drive, pasta "Gestão brownies/brownies LOV/Melhores" (tradicional, textura, metade cookie, cobertura, embalados, kit com 4).
- Planilha "Controle de Vendas de Brownies" no Drive: primeiras vendas a R$ 10 por unidade.
- Plano de negócios de 03/11/2026 (enviado pela dona, não versionado aqui): preços, custos, ponto de equilíbrio de 6 brownies por dia, oferta "Luv 80 g, Chegou Inteiro", posicionamento de presente pronto, calendário de lançamento (pré-venda em 21/11, lançamento em 28/11) e orçamento de marketing de R$ 200. Os números são projeções e o painel de compradores é simulado.
- A primeira noite de vendas (03/11) teve zero vendas.
- Não existem ainda depoimentos nem avaliações publicadas. Não inventar.

## Product Principles

- Uma pessoa, poucos minutos por semana: cada tela precisa responder rápido o que está bom, o que está fora da meta e o que fazer.
- Mostrar dinheiro de verdade: faturamento líquido de comissão vale mais que faturamento bruto.
- Replicável por estrutura: o que é de um negócio específico fica nos dados; o que serve para qualquer frente fica no modelo.
- Nada de número inventado: o que não foi lançado aparece vazio, com o caminho para lançar.
