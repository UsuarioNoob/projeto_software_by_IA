# Testes — Chunks

## TDD-CHUNK-001
Um registro válido deve gerar ao menos um chunk.

## TDD-CHUNK-002
O texto deve conter Tipo, Número, Assunto, Ementa e Situação.

## TDD-CHUNK-003
Metadata obrigatória deve existir.

## TDD-CHUNK-004
IDs dos chunks devem ser únicos.

## TDD-CHUNK-005
Texto maior que `chunk_size` deve gerar múltiplos chunks.

## TDD-CHUNK-006
O `chunk_overlap` deve ser respeitado.

## TDD-CHUNK-007
Valores nulos não devem produzir exceções inesperadas.
