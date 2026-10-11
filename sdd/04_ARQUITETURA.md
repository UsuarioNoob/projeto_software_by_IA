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
  +-----------------------------+
  |                             |
  v                             v
Busca textual em           Embedding da pergunta
Assunto e Ementa                |
  |                             v
  |                       Similarity Search
  |                             |
  |                             v
  |                      Top-K semântico
  |                             |
  +--------------+--------------+
                 |
                 v
      Combinação sem duplicidades
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

Correspondências textuais diretas são priorizadas e podem superar o `Top-K`. A parcela semântica
permanece limitada pela configuração `TOP_K`. O LLM valida se o contexto combinado realmente
sustenta a resposta antes de qualquer fonte ser apresentada ao usuário.
