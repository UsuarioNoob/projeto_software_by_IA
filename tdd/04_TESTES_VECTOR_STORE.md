# Testes — Vector Store

## TDD-VEC-001
Conectar deve criar ou recuperar a coleção.

## TDD-VEC-002
Dados devem persistir após reconexão.

## TDD-VEC-003
Indexar N chunks deve persistir N registros esperados.

## TDD-VEC-004
`recriar=False` com coleção populada não deve regenerar embeddings.

## TDD-VEC-005
`recriar=True` deve eliminar dados antigos.

## TDD-VEC-006
Mudança de coleção não deve contaminar outra coleção.

## TDD-VEC-007
Falha de persistência deve gerar erro explícito.
