# Avaliação de Qualidade RAG

## Dataset

Criar:

```text
tests/evaluation/questions.json
```

Exemplo:

```json
[
  {
    "id": "RAG001",
    "question": "Qual ato dispõe sobre Cartório Acolhedor?",
    "expected_document": "Provimento 360/2026",
    "expected_terms": ["Cartório Acolhedor"]
  }
]
```

## Métricas

### HitRate@K

```text
perguntas com documento esperado no top-k
/
total de perguntas
```

Meta inicial:

```text
HitRate@5 >= 90%
```

### Recall@K

```text
documentos relevantes recuperados
/
total de documentos relevantes
```

### MRR

```text
posição 1 = 1.00
posição 2 = 0.50
posição 3 = 0.33
```

### Faithfulness
A resposta não deve introduzir fatos não suportados pelo contexto.

### Out-of-scope
Perguntas sem resposta na base devem retornar ausência de informação.
