# Testes — Fingerprint

## TDD-HASH-001
Mesmos arquivos devem produzir mesmo hash.

## TDD-HASH-002
Conteúdo alterado deve mudar o hash.

## TDD-HASH-003
Arquivo adicionado deve mudar o hash.

## TDD-HASH-004
Arquivo removido deve mudar o hash.

## TDD-HASH-005
Arquivo renomeado deve mudar o hash.

## TDD-HASH-006
Ordem do filesystem não deve alterar resultado.

## TDD-HASH-007
Mudança do modelo de embedding deve invalidar fingerprint.

## TDD-HASH-008
Mudança de `chunk_size` deve invalidar fingerprint.

## TDD-HASH-009
Mudança de `chunk_overlap` deve invalidar fingerprint.

## TDD-HASH-010
Falha de indexação não deve salvar novo fingerprint.
