# Arquitetura do Sistema

## Visão de alto nível

```text
Usuário
  |
  v
Chainlit / mod_ui.py
  |
  v
mod_orquestrator.py
  |
  +------------------------+
  |                        |
  v                        v
mod_embedding.py      mod_api_ia.py
  |                        |
  v                        v
ChromaDB              OpenRouter
```

## Pipeline de indexação

```text
docs/
  |
  v
mod_docs.py
  |
  v
Document
  |
  v
SentenceSplitter
  |
  v
Chunks
  |
  v
Embedding
  |
  v
ChromaDB
```

## Pipeline de consulta

```text
Pergunta
  |
  v
Busca textual em Assunto e Ementa
  |
  +--> encontrou correspondências
  |       |
  |       v
  |    Maior cobertura temática
  |
  `--> não encontrou correspondências
          |
          v
      Embedding da pergunta
          |
          v
      Similarity Search
          |
          v
      Top-K semântico
  |
  v
Contexto
  |
  v
Prompt
  |
  v
LLM
  |
  v
Resposta
```

Correspondências textuais diretas com maior cobertura temática são priorizadas e podem superar o
`Top-K`. Quando elas existem, vizinhos puramente semânticos não são acrescentados. A busca semântica,
limitada pela configuração `TOP_K`, funciona como fallback. O LLM ainda valida se o contexto
recuperado realmente sustenta a resposta. As fontes permanecem internas ao pipeline e não são
acrescentadas automaticamente à mensagem apresentada ao usuário.
