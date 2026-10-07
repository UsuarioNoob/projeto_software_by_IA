# Testes — Retrieval

## TDD-SEARCH-001
Pergunta vazia deve gerar erro.

## TDD-SEARCH-002
`top_k <= 0` deve gerar erro.

## TDD-SEARCH-003
Quantidade retornada deve ser `<= top_k`.

## TDD-SEARCH-004
Pergunta sobre cartórios deve ranquear documento sobre cartórios antes de documentos irrelevantes.

## TDD-SEARCH-005
Coleção vazia deve gerar erro explícito.

## TDD-SEARCH-006
A ordem dos resultados deve respeitar relevância.

## TDD-SEARCH-007
Metadata original deve permanecer acessível após retrieval.
