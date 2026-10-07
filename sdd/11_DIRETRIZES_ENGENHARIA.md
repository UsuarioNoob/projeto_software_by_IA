# Diretrizes de Engenharia

## DE-001 — Separação de responsabilidades
Cada módulo deve possuir responsabilidade única.

## DE-002 — Configuração externa
Credenciais, modelos e parâmetros devem ficar fora da lógica de negócio.

## DE-003 — Erros explícitos
Evitar `except Exception` como padrão.

## DE-004 — Tipagem
Funções públicas devem possuir type hints.

## DE-005 — Logging
Substituir `print()` por `logging`.

## DE-006 — Testabilidade
Chamadas externas devem poder ser substituídas por mocks.

## DE-007 — Compatibilidade
Mudanças em interfaces públicas devem preservar backward compatibility ou ser versionadas.

## DE-008 — IA como implementadora
A IA deve receber:

```text
CONTEXTO
+ CONTRATO
+ TESTES
+ RESTRIÇÕES
```

## DE-009 — Testes protegidos
A implementação não deve alterar testes apenas para fazê-los passar.
