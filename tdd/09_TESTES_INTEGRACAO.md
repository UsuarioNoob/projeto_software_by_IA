# Testes de Integração

## INT-001 — Documento até chunk

```text
XLSX -> Pandas -> Document -> SentenceSplitter -> Node
```

## INT-002 — Chunk até ChromaDB

```text
Chunk -> Embedding real -> Chroma temporário
```

## INT-003 — Retrieval real

Base controlada:

```text
A = cartórios
B = motocicletas
C = bancos de dados
```

Pergunta sobre cartórios deve recuperar A no topo.

## INT-004 — Persistência
Dados devem sobreviver à reconexão.

## INT-005 — Pipeline RAG sem API real

```text
documento
-> chunk
-> embedding
-> Chroma
-> retrieval
-> contexto
-> LLM mock
```
