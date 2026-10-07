# Decisões Arquiteturais

## ADR-001 — ChromaDB persistente

**Decisão:** utilizar `PersistentClient`.

**Motivo:** evitar reindexação completa em toda inicialização.

---

## ADR-002 — HuggingFace Embeddings

**Decisão:** utilizar modelo multilíngue.

**Motivo:** suportar conteúdo e perguntas em português/espanhol.

---

## ADR-003 — Chainlit

**Decisão:** utilizar Chainlit como interface.

**Motivo:** simplificar interação conversacional.

---

## ADR-004 — Fingerprint da indexação

**Decisão recomendada:** fingerprint deve incluir:

```text
documentos
modelo_embedding
chunk_size
chunk_overlap
schema_version
```

**Motivo:** qualquer um desses fatores altera semanticamente o índice.
