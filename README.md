# useecc — vídeos de texto animado com narração

Esqueleto em [Remotion](https://www.remotion.dev) para gerar vídeos verticais (1080×1920) no estilo "texto que aparece palavra por palavra + narração", e medir quanto custa e quanto tempo leva cada um.

## Começando

```bash
npm install
npm run studio                          # pré-visualiza no navegador
npm run render -- exemplo --minutos 20  # gera out/exemplo.mp4 e registra o custo
npm run custos                          # resumo de custo, margem e R$/hora
```

`--minutos` é o tempo que **você** gastou no vídeo (roteiro, conversa com o Claude, ajustes). Esse número a máquina não tem como medir, e é ele que decide se R$ 50 por vídeo compensa.

## Criando um vídeo

Copie `videos/exemplo.json` para `videos/<nome>.json` e edite:

```jsonc
{
  "handle": "seuperfil",
  "narracao": { "provedor": "nenhum", "vozId": "", "modelo": "eleven_multilingual_v2" },
  "cenas": [
    {
      "texto": "Quanto eu cobro por um vídeo?", // o que aparece na tela
      "fala": "Quanto eu cobro por um vídeo editado com IA?", // opcional: o que é falado
      "destaque": ["cobro"],                     // palavras na cor de destaque
      "icone": "arquivo"                          // "arquivo" | "dinheiro" | "nenhum"
    }
  ]
}
```

Depois: `npm run render -- <nome>`.

## Narração plugável

| `provedor`   | O que faz |
|--------------|-----------|
| `nenhum`     | Sem áudio. A duração de cada cena é estimada pelo número de palavras. |
| `arquivos`   | Usa `public/audio/<nome>/cena-1.mp3`, `cena-2.mp3`… gravados por você ou exportados de qualquer ferramenta de voz. |
| `elevenlabs` | Gera cada cena pela API da ElevenLabs (voz clonada inclusive). Precisa de `ELEVENLABS_API_KEY` no ambiente e `vozId` no JSON. Áudios já gerados ficam em cache e não são cobrados de novo. |

Nos provedores com áudio, cada cena dura o tamanho da fala mais meio segundo. Para outro serviço de voz, adicione uma função ao lado de `gerarElevenLabs` em `scripts/narrar.ts`.

## Custos

Os parâmetros ficam em `custos.config.json`: cotação do dólar, assinaturas mensais, vídeos por mês, preço do TTS por mil caracteres e o preço que você cobra. Cada render acrescenta uma linha em `relatorio/historico.csv`, e o `npm run custos` faz a média. Confira os preços atuais dos planos antes de usar os números.

## Estrutura

```
src/TextoAnimado.tsx              composição: fundo, @handle, cenas em sequência
src/components/TextoRevelado.tsx  palavras saindo do desfoque
src/components/IconeCard.tsx      cartão de ícone com entrada em mola
src/duracao.ts                    duração das cenas (áudio real ou estimativa)
scripts/narrar.ts                 provedores de narração
scripts/render.ts                 narração + render + registro no CSV
scripts/custos.ts                 resumo de custo por vídeo
```

## Licença do Remotion

O Remotion é gratuito para pessoas físicas e empresas com até 3 funcionários. Acima disso exige licença paga. Veja https://www.remotion.dev/license.
