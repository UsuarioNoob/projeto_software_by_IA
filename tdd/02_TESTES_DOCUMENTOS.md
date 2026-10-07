# Testes — Documentos

## TDD-DOC-001 — Pasta inexistente
Esperado: `FileNotFoundError` ou exceção equivalente.

## TDD-DOC-002 — Pasta vazia
Esperado: `[]`.

## TDD-DOC-003 — CSV válido
Validar quantidade, campos e tipos.

## TDD-DOC-004 — XLSX válido
Validar leitura e consolidação.

## TDD-DOC-005 — Múltiplos arquivos
A quantidade final deve ser a soma dos registros.

## TDD-DOC-006 — Extensão desconhecida
Arquivos não suportados devem ser ignorados.

## TDD-DOC-007 — Campo obrigatório ausente
Esperado: `SchemaValidationError`.

## TDD-DOC-008 — NaN
Esperado: normalização para `None`.

## TDD-DOC-009 — Arquivo inválido
A base não deve ser considerada válida após falha de leitura relevante.
