# Fixtures e Mocks

## Arquivo

```text
tests/conftest.py
```

## Fixtures recomendadas

```python
@pytest.fixture
def documento_valido():
    ...

@pytest.fixture
def documentos_validos():
    ...

@pytest.fixture
def pasta_documentos(tmp_path):
    ...

@pytest.fixture
def chroma_temporario(tmp_path):
    ...

@pytest.fixture
def resposta_openrouter_mock():
    ...
```

## Mocks obrigatórios em testes unitários

- OpenRouter;
- requests;
- embedding quando o objetivo não for testar embedding;
- filesystem quando necessário;
- relógio/tempo quando houver dependência temporal.

## Regra

Teste unitário não deve depender de:

- internet;
- token real;
- ChromaDB de produção;
- arquivos de produção.
