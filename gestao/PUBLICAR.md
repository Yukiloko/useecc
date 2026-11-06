# Publicar na internet

O resultado é um endereço como `https://luv-gestao.onrender.com`, que abre no celular ou no computador e pede senha.

| | Render + Supabase (recomendado) | PythonAnywhere |
|---|---|---|
| Como configura | Só cliques no navegador | Alguns comandos num console |
| Onde ficam os dados | Supabase (Postgres) | Arquivo no próprio servidor |
| Atualização do código | Automática pelo GitHub | Um comando + Reload |
| Plano grátis | Dorme após 15 min sem uso e leva ~1 min para acordar | Sempre ligado, mas precisa renovar a cada 3 meses com um clique |
| Para não dormir | Render Starter, US$ 7/mês | — |

## Opção 1: Render + Supabase

### 1. Banco no Supabase
1. Em https://supabase.com, crie um projeto novo (**New project**). Em **Region**, escolha **East US (North Virginia)**: precisa ser perto do servidor do Render, senão as telas ficam lentas.
2. Na senha do banco, use só letras e números (símbolos como `@` e `#` quebram o endereço de conexão). Anote a senha.
3. Com o projeto criado, clique em **Connect** no topo. Em **Connection string**, escolha **URI** e o método **Transaction pooler**. Copie o endereço e troque `[YOUR-PASSWORD]` pela senha do passo 2.

As tabelas são criadas sozinhas na primeira vez que a gestão abrir. Elas ficam com RLS ligado: a API pública do Supabase não enxerga os dados, só a ferramenta.

Atenção: no plano grátis, o Supabase pausa o projeto depois de 7 dias sem nenhum acesso. Usando a gestão toda semana, isso não acontece. Se pausar, é só entrar no painel do Supabase e clicar em **Restore** (os dados ficam guardados).

### 2. Site no Render
1. Em https://render.com, entre com a conta do GitHub.
2. **New** › **Blueprint** › escolha o repositório `useecc` e o branch `claude/amazing-mccarthy-b11w16`.
3. O Render lê o arquivo `render.yaml` e pede dois valores:
   - `DATABASE_URL`: o endereço do Supabase do passo 1.3
   - `LUV_SENHA`: a senha que você vai usar para entrar na gestão
4. **Apply**. Em uns 3 minutos o endereço aparece no painel (algo como `luv-gestao.onrender.com`).

Cada mudança enviada para esse branch no GitHub atualiza o site sozinha.

### Backup
No painel do Supabase, **Table Editor** › cada tabela › **Export to CSV**. Na própria gestão dá para exportar os lançamentos e a DRE em CSV. Os planos pagos do Supabase têm backup diário automático.

## Opção 2: PythonAnywhere (sem Supabase)

Guarda tudo num arquivo SQLite no servidor. Não dorme, mas no plano grátis é preciso entrar a cada 3 meses e clicar em **"Run until 3 months from today"**.

1. Crie a conta em https://www.pythonanywhere.com (**Beginner account**). O usuário vira o endereço.
2. Aba **Consoles** › **Bash**, e rode:
   ```bash
   git clone -b claude/amazing-mccarthy-b11w16 https://github.com/yukiloko/useecc.git
   ```
   ```bash
   cd ~/useecc/gestao && python3.13 -m venv ~/.venv-luv && ~/.venv-luv/bin/pip install -r requirements.txt
   ```
   Se o repositório for privado, o git pede usuário e senha: na senha use um token do GitHub (Settings › Developer settings › Personal access tokens). Se `python3.13` não existir, use a versão mais nova disponível e a mesma no passo 3.
3. Aba **Web** › **Add a new web app** › **Manual configuration** › **Python 3.13**. Preencha **Source code** `/home/SEU_USUARIO/useecc/gestao`, **Virtualenv** `/home/SEU_USUARIO/.venv-luv` e ligue **Force HTTPS**.
4. Abra o **WSGI configuration file**, apague tudo e cole:
   ```python
   import os
   import sys

   os.environ["LUV_SENHA"] = "escolha-uma-senha-forte"

   sys.path.insert(0, "/home/SEU_USUARIO/useecc/gestao")
   from wsgi import application  # noqa
   ```
5. **Reload**. Para atualizar depois: `cd ~/useecc && git pull` no console e **Reload**. Backup: baixe `~/useecc/gestao/dados/luv.db` pela aba **Files**.

## Vercel

Também funciona com o Supabase (`vercel.json` e `api/index.py` já estão prontos): importe o repositório com **Root Directory** `gestao`, defina `DATABASE_URL` e `LUV_SENHA` e, em **Settings › Functions**, escolha a mesma região do Supabase. Só que o plano grátis do Vercel é para uso pessoal e não comercial; para o negócio, o certo é o Pro (US$ 20/mês).

## No celular
Abra o endereço no Safari ou Chrome e use **Compartilhar › Adicionar à Tela de Início**.

## Trocar a senha
Mude `LUV_SENHA` (no Render: **Environment**; no PythonAnywhere: arquivo WSGI e **Reload**). Para desconectar todos os aparelhos, apague a linha `chave_secreta` da tabela `config`.
