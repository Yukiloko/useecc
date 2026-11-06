# Publicar na internet (PythonAnywhere)

Assim a gestão fica num endereço como `https://luvbrownies.pythonanywhere.com`, aberta no celular ou em qualquer computador, com senha.

O PythonAnywhere tem plano grátis que serve para este uso. Ele guarda o banco de dados no disco de verdade (em hospedagens como o Render grátis, o disco é apagado a cada reinício e você perderia os lançamentos). No plano grátis, entre no painel uma vez a cada 3 meses e clique em **"Run until 3 months from today"**, senão o site é desligado (os dados não se perdem). O plano pago (US$ 5/mês) tira essa exigência e permite domínio próprio.

## 1. Criar a conta
Em https://www.pythonanywhere.com › **Pricing & signup** › **Create a Beginner account**. O nome de usuário vira o endereço do site (ex.: `luvbrownies`).

## 2. Baixar o código
No painel, aba **Consoles** › **Bash**. Cole:

```bash
git clone -b claude/amazing-mccarthy-b11w16 https://github.com/yukiloko/useecc.git
```

Se o repositório for privado, o git vai pedir usuário e senha. Na senha, use um **token do GitHub** (GitHub › Settings › Developer settings › Personal access tokens › Fine-grained, com acesso de leitura ao repositório `useecc`).

Sem git: baixe o .zip do branch no GitHub, envie pela aba **Files** e descompacte no console com `unzip`.

## 3. Instalar
Ainda no console:

```bash
cd ~/useecc/gestao && python3.13 -m venv ~/.venv-luv && ~/.venv-luv/bin/pip install -r requirements.txt
```

Se `python3.13` não existir lá, use a versão mais nova que existir (ex.: `python3.12`) e escolha a mesma no passo 4.

## 4. Criar o site
Aba **Web** › **Add a new web app** › **Next** › **Manual configuration** › **Python 3.13** › **Next**.

Na página do site, preencha:
- **Source code:** `/home/SEU_USUARIO/useecc/gestao`
- **Virtualenv:** `/home/SEU_USUARIO/.venv-luv`
- **Force HTTPS:** ligado

Clique no link do **WSGI configuration file**, apague tudo e cole (trocando o usuário e a senha):

```python
import os
import sys

os.environ["LUV_SENHA"] = "escolha-uma-senha-forte"

sys.path.insert(0, "/home/SEU_USUARIO/useecc/gestao")
from wsgi import application  # noqa
```

Salve, volte à aba **Web** e clique em **Reload**. Pronto: abra `https://SEU_USUARIO.pythonanywhere.com`.

Quer testar primeiro com os dados de exemplo? Adicione `os.environ["LUV_DEMO"] = "1"` no arquivo WSGI. Para usar de verdade, apague essa linha e clique em Reload: os bancos real e de exemplo são arquivos separados.

## No celular
Abra o endereço no Safari ou Chrome e use **Compartilhar › Adicionar à Tela de Início**. Fica com cara de aplicativo.

## Atualizar quando houver mudanças no código
No console Bash:

```bash
cd ~/useecc && git pull && ~/.venv-luv/bin/pip install -r gestao/requirements.txt
```

Depois **Reload** na aba Web.

## Backup
O banco é o arquivo `~/useecc/gestao/dados/luv.db`. Aba **Files** › entre na pasta › clique no arquivo para baixar. Faça isso de vez em quando.

## Trocar a senha
Edite `LUV_SENHA` no arquivo WSGI e clique em Reload. Para desconectar todos os aparelhos, apague também `dados/chave-secreta.txt` antes do Reload.
