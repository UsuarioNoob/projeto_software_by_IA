# Riscos e Limitações

## R-001 — Schema implícito
Ausência de validação pode causar `KeyError` ou base inconsistente.

## R-002 — Indexação parcial
Ignorar arquivos com erro pode produzir uma base incompleta.

## R-003 — Fingerprint incompleto
Considerar apenas documentos pode deixar o índice semanticamente inválido após alteração de parâmetros.

## R-004 — Chamadas síncronas
`requests` síncrono pode bloquear o event loop do Chainlit.

## R-005 — Top-K fixo
Pode ser inadequado para consultas distintas.

## R-006 — Dependência externa
OpenRouter pode falhar por timeout, rate limit ou indisponibilidade.

## R-007 — Ausência de testes
O projeto atual depende excessivamente de validação manual.
