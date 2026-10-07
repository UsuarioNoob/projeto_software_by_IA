# Matriz de Rastreabilidade

Esta matriz liga requisitos do SDD aos testes correspondentes.

| Requisito | Descrição | Testes principais |
|---|---|---|
| RF-001 | Carregar documentos | TDD-DOC-001 a 009 |
| RF-002 | Formatos suportados | TDD-DOC-003 a 006 |
| RF-004 | Criar chunks | TDD-CHUNK-001 a 007 |
| RF-005 | Gerar embeddings | TDD-VEC-003 |
| RF-006 | Persistir embeddings | TDD-VEC-002 |
| RF-007 | Detectar alteração | TDD-HASH-001 a 009 |
| RF-008 | Reindexar | TDD-HASH-007 a 010 |
| RF-009 | Reutilizar índice | TDD-VEC-004 |
| RF-010 | Receber pergunta | TDD-SEARCH-001 |
| RF-011 | Retrieval | TDD-SEARCH-003 a 007 |
| RF-012 | Montar contexto | TDD-RAG-006 |
| RF-013 | Consultar LLM | TDD-LLM-005 a 017 |
| RF-014 | Controlar alucinação | RAG-EVAL Faithfulness |
| RF-015 | Tratar falhas | TDD-LLM-008 a 017 |
| RF-016 | Exibir resposta | E2E-004 a 006 |

## Regra

Todo novo requisito funcional deve possuir pelo menos um teste associado antes de ser considerado implementável.
