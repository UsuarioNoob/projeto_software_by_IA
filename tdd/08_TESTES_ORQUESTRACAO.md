# Testes — Orquestração

## TDD-RAG-001
Fluxo nominal:

```text
buscar_chunks
  |
  v
montar_contexto
  |
  v
openrouter
```

## TDD-RAG-002
`top_k` deve ser propagado corretamente.

## TDD-RAG-003
Sem documentos recuperados, o LLM não deve ser chamado.

## TDD-RAG-004
Falha no retrieval deve impedir chamada ao LLM.

## TDD-RAG-005
Falha do LLM deve ser traduzida para erro apropriado.

## TDD-RAG-006
Contexto deve preservar ordem e metadata.

## TDD-RAG-007
Resposta sem base suficiente deve ser explícita.
