# Requisitos Não Funcionais

## RNF-001 — Segurança
Tokens e credenciais não devem ser armazenados diretamente no código.

## RNF-002 — Persistência
O índice vetorial deve sobreviver à reinicialização da aplicação.

## RNF-003 — Desempenho
Embeddings não devem ser regenerados sem necessidade.

## RNF-004 — Modularidade
Interface, orquestração, documentos, embedding e integração LLM devem permanecer desacoplados.

## RNF-005 — Portabilidade
Caminhos devem ser construídos com `pathlib`.

## RNF-006 — Observabilidade
O sistema deve evoluir de `print()` para logging estruturado.

## RNF-007 — Configurabilidade
Modelo, coleção, caminhos e parâmetros de chunking devem ser configuráveis.

## RNF-008 — Determinismo
O fingerprint dos documentos deve ser reproduzível.

## RNF-009 — Testabilidade
Integrações externas devem ser mockáveis.

## RNF-010 — Manutenibilidade
Cada módulo deve possuir responsabilidade única e interfaces claras.
