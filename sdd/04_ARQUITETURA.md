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
Embedding da pergunta
  |
  v
Similarity Search
  |
  v
Top-K
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
