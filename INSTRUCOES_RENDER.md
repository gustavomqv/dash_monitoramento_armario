# Publicar no Render

Coloque na raiz de um repositório GitHub os arquivos `app.py`, `requirements.txt`,
`render.yaml`, `.python-version` e a pasta `assets/`. O CSS dentro de `assets/`
é carregado automaticamente pelo Dash.

No Render, crie um **Web Service** para esse repositório (ou um Blueprint que use
`render.yaml`). O serviço instala `requirements.txt` e inicia com Gunicorn.

Em **Environment**, configure `DB_PASSWORD` com a senha do banco. Ela não deve
ser adicionada ao repositório. Os outros valores já têm padrão no código:
`DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PORT` podem ser definidos no Render se
precisarem mudar.

Se criar o serviço manualmente, use:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:server --bind 0.0.0.0:$PORT`

No computador, execute `python app.py` com `DB_PASSWORD` definida no terminal.
O importador e o CSV usados para corrigir as datas não são necessários para
publicar o aplicativo.
