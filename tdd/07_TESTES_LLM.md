# Testes — Integração LLM

Todos os testes unitários desta área devem usar MOCK.

## TDD-LLM-001
Token `None` deve gerar erro.

## TDD-LLM-002
Token vazio deve gerar erro.

## TDD-LLM-003
Token simples deve virar `Bearer <token>`.

## TDD-LLM-004
Token já iniciado com `Bearer` não deve ser duplicado.

## TDD-LLM-005
Payload deve conter modelo e mensagens.

## TDD-LLM-006
Requisição deve possuir timeout.

## TDD-LLM-007
HTTP 200 deve extrair `message.content`.

## TDD-LLM-008
HTTP 401 deve gerar erro de autenticação.

## TDD-LLM-009
HTTP 429 deve ser tratado como rate limit.

## TDD-LLM-010
HTTP 500 deve gerar erro de serviço externo.

## TDD-LLM-011
Timeout deve gerar erro de conexão.

## TDD-LLM-012
ConnectionError deve ser tratado.

## TDD-LLM-013
JSON inválido deve gerar erro.

## TDD-LLM-014
`choices` ausente deve gerar erro.

## TDD-LLM-015
`choices=[]` deve gerar erro.

## TDD-LLM-016
`message` ausente deve gerar erro.

## TDD-LLM-017
`content` ausente deve gerar erro.
