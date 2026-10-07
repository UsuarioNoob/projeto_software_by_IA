# Cobertura e Pipeline de Testes

## Cobertura mínima

```text
Projeto geral >= 80%
```

Módulos críticos:

```text
mod_docs.py           >= 90%
mod_api_ia.py         >= 90%
mod_orquestrator.py   >= 90%
```

## Execução

```bash
pytest
```

Detalhado:

```bash
pytest -v
```

Cobertura:

```bash
pytest --cov=. --cov-report=term-missing
```

## Definição de pronto

```text
[ ] requisito definido
[ ] teste escrito
[ ] teste falhou inicialmente
[ ] implementação criada
[ ] teste passou
[ ] regressão preservada
[ ] código refatorado
[ ] cobertura mantida
```
