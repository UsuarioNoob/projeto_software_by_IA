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

---

## ADR-005 — Preparação da base antes da interface

**Decisão:** executar configuração, conexão com ChromaDB, validação do fingerprint e eventual
reindexação no callback `on_app_startup` do Chainlit.

**Motivo:** impedir que o usuário acesse um chat ainda indisponível, preparar recursos pesados uma
única vez por processo e reutilizar o estado pronto entre conversas.

**Consequência:** falhas de preparação são propagadas e interrompem o startup do servidor. O
callback `on_chat_start` apenas associa o estado global já preparado à sessão do usuário.
