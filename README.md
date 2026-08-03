# rag-fastapi

Um sistema de **RAG (Retrieval-Augmented Generation)** - ou seja, uma API
que responde perguntas com base em documentos próprios, em vez de depender
só do conhecimento genérico do LLM. Construído para aprender o fluxo
essencial de um RAG: ingestão -> indexação vetorial -> busca semântica ->
geração de resposta.

🔗 **Em produção:** `https://rag-fastapi-production-f63c.up.railway.app`

---

## O que o projeto faz, na prática

1. Você guarda documentos (`.md`, `.txt`, `.pdf`) numa pasta
2. O sistema **lê** esses documentos, **quebra** em pedaços menores (chunks)
   e gera um **embedding** (vetor numérico que representa o significado do
   texto) para cada pedaço
3. Esses vetores ficam guardados num **banco vetorial** (ChromaDB)
4. Quando alguém faz uma pergunta pela API, o sistema:
   - transforma a pergunta em embedding também
   - busca no ChromaDB os pedaços de texto mais **semanticamente parecidos**
     com a pergunta (não é busca por palavra-chave, é por significado)
   - manda esses pedaços + a pergunta pro LLM (OpenAI)
   - o LLM formula uma resposta **baseada apenas nesse contexto**
   - a API devolve a resposta junto com as fontes usadas (rastreabilidade)

```
documentos/ ----> ingestion.py -> ChromaDB (banco vetorial local)
                                        │
pergunta ----> POST /query ----> query_engine.py ----> LLM (OpenAI) ----> resposta + fontes
```

Por que isso é diferente de simplesmente perguntar pro ChatGPT? Porque a
resposta é ancorada nos **seus** documentos — o LLM não inventa nem usa
conhecimento genérico da internet, ele só reformula o que está nos chunks
recuperados. Isso é a base de qualquer assistente de IA corporativo,
chatbot de suporte com base de conhecimento própria, etc.

---

## Stack e por quê

| Tecnologia | Papel | Por que essa escolha |
|---|---|---|
| **LlamaIndex** | Orquestra ingestão, chunking, embeddings e query | Framework focado em RAG, mais direto que montar tudo na mão |
| **ChromaDB** | Banco vetorial | Roda embutido (sem servidor separado), ideal pra aprender sem complexidade de infra |
| **FastAPI** | Expõe tudo como API HTTP | Tipagem nativa com Pydantic, documentação automática (Swagger) |
| **Pydantic** | Valida todo dado que entra/sai da API | Garante que a API nunca devolve texto solto sem estrutura |
| **OpenAI API** | Gera embeddings e a resposta final | LLM usado tanto pra "entender" o texto quanto pra escrever a resposta |
| **Railway** | Hospeda a API publicamente | Deploy simples direto do GitHub, sem configurar servidor manualmente |

---

## Estrutura do repositório, arquivo por arquivo

```
junior-rag-fastapi/
├── data/
│   └── documents/          # documentos que serão indexados (gerado, não versionado)
├── scripts/
│   └── generate_sample_docs.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── schemas.py
│   ├── ingestion.py
│   ├── query_engine.py
│   └── api.py
├── storage/
│   └── chroma/              # banco vetorial persistido (gerado, não versionado)
├── tests/
│   └── test_query_engine.py
├── .env.example
├── .env                      # suas variáveis reais (nunca versionado)
├── .gitignore
├── Procfile
├── pytest.ini
├── requirements.txt
└── README.md
```

### `src/config.py`
Centraliza a leitura de variáveis de ambiente (`.env` local, ou Variables no
Railway em produção) usando `pydantic-settings`. Define `openai_api_key`,
`llm_model` e `embedding_model`. **Nenhum outro arquivo deve ler variável de
ambiente diretamente** — tudo passa por aqui, o que facilita trocar de
provedor de LLM no futuro sem caçar `os.environ` espalhado pelo código.

### `src/schemas.py`
Define os **contratos de dados** da API usando Pydantic:
- `QueryRequest` — o que a API espera receber (`question`, `top_k`)
- `SourceChunk` — um trecho de documento usado como fonte de uma resposta
- `QueryResponse` — o formato de saída (`answer` + lista de `sources`)

Isso garante que a API nunca devolve um formato inesperado — se algo no
código tentar retornar um campo errado, o FastAPI já barra antes de
responder ao cliente.

### `src/ingestion.py`
Responsável por **popular o banco vetorial**:
1. Lê todos os arquivos de `data/documents/` (`SimpleDirectoryReader`)
2. Divide cada documento em chunks menores (`SentenceSplitter`, embutido no
   `VectorStoreIndex`)
3. Gera embeddings para cada chunk (chamando a API da OpenAI)
4. Salva tudo na coleção `docs` do ChromaDB, persistida em `storage/chroma/`

Roda como script (`python -m src.ingestion`) ou é disparado via API
(`POST /ingest`) — os dois caminhos chamam a mesma função `run_ingestion()`.

### `src/query_engine.py`
Responsável por **responder perguntas**:
1. Abre o índice já existente em `storage/chroma/` (não reindexa nada, só
   lê o que já foi processado pela ingestão)
2. Usa `as_query_engine(similarity_top_k=N)` pra buscar os `N` chunks mais
   relevantes pra pergunta
3. Manda pergunta + chunks pro LLM e recebe a resposta
4. Converte a resposta bruta do LlamaIndex nos schemas Pydantic
   (`QueryResponse`/`SourceChunk`), incluindo de qual arquivo cada trecho
   veio e o quão relevante ele foi (`score`)

### `src/api.py`
A camada HTTP, feita com FastAPI. Três rotas:
- `GET /health` — checagem simples de que o serviço está de pé (usado por
  monitoramento/uptime)
- `POST /query` — recebe uma pergunta, devolve `QueryResponse`
- `POST /ingest` — dispara a ingestão sob demanda (útil depois de adicionar
  novos documentos, sem precisar redeployar)

Erros de LLM/Chroma são capturados e viram HTTP 500/502 com mensagem clara,
em vez de derrubar o servidor.

### `scripts/generate_sample_docs.py`
Gera 3 documentos markdown fake (política de reembolso, SLA de suporte,
onboarding) direto em `data/documents/`. Existe pra resolver um problema de
**reprodutibilidade**: qualquer pessoa que clonar o repo consegue rodar o
projeto do zero sem precisar dos seus documentos reais, e os testes
automatizados têm respostas conhecidas pra validar contra ("30 dias", "24
horas" etc.).

### `tests/test_query_engine.py`
Testes automatizados (pytest) que fazem perguntas cuja resposta certa você
já sabe (baseado nos documentos de exemplo) e conferem que a resposta e as
fontes vêm corretas. Marcados com `@pytest.mark.llm` porque fazem chamadas
reais à API da OpenAI (custam requisição/dinheiro), então dá pra pular esse
grupo em ambientes sem API key configurada.

### `Procfile`
Diz ao Railway como iniciar a aplicação em produção:
```
web: uvicorn src.api:app --host 0.0.0.0 --port $PORT
```
`--host 0.0.0.0` faz o servidor aceitar conexões de fora do container (não
só de dentro dele). `--port $PORT` usa a porta que o Railway injeta
dinamicamente — nunca uma porta fixa, porque cada plataforma de deploy pode
usar uma porta diferente.

### `pytest.ini`
Configura o pytest: registra o marcador `llm` e define `pythonpath = .`,
que resolve o erro clássico `ModuleNotFoundError: No module named 'src'`
(sem isso, o pytest não sabe que a raiz do projeto deve entrar no
`sys.path`).

### `.env.example` vs `.env`
`.env.example` é o **molde**, versionado no Git, mostrando quais variáveis
existem sem expor valores reais. `.env` é o arquivo com suas chaves de
verdade — nunca deve ir pro GitHub (é assim que segredos vazam
publicamente).

---

## Quick Start (local)

```bash
git clone <seu-repo>
cd junior-rag-fastapi
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# preencha OPENAI_API_KEY no .env

python -m scripts.generate_sample_docs   # cria documentos de exemplo
python -m src.ingestion                    # indexa no ChromaDB

uvicorn src.api:app --reload
```

Testa em `http://localhost:8000/docs` (Swagger UI).

## Deploy (Railway)

1. Suba o repo pro GitHub
2. No Railway: **New Project → Deploy from GitHub repo**
3. Em **Variables**, adicione `OPENAI_API_KEY`, `LLM_MODEL`,
   `EMBEDDING_MODEL`
4. Em **Settings → Networking**, gere um domínio público e confirme que a
   porta exibida corresponde à porta que o Uvicorn realmente usa (o
   Railway injeta isso via `$PORT` — não precisa fixar manualmente)
5. Depois do primeiro deploy bem-sucedido, chame `POST /ingest` uma vez
   pra popular o índice em produção (a ingestão não roda mais
   automaticamente no boot, de propósito — ver seção abaixo)

## Por que a ingestão não roda automaticamente no boot

Numa primeira versão, o `Procfile` rodava a ingestão antes do servidor
subir (`python -m src.ingestion && uvicorn ...`). Isso causou um problema
real em produção: se a ingestão falhar ou travar (ex: erro de conexão com
a OpenAI), o `&&` nunca deixa o Uvicorn iniciar — a API inteira fica fora
do ar por causa de um problema que deveria afetar só a indexação. Por isso
a ingestão foi desacoplada e vira uma chamada explícita ao endpoint
`/ingest`, sob seu controle.


## Roadmap de evolução (opcional)

1. Trocar Chroma local por **Qdrant** via Docker Compose
2. Adicionar uma segunda fonte de dado (ex: SQLite) com Text-to-SQL
3. Adicionar um `RouterQueryEngine` pra decidir entre as duas fontes
4. Expor o RAG como servidor **MCP**, pra ser consumido por um agente
   