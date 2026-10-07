# Contratos de Dados

## Schema de entrada

| Campo | Obrigatório | Uso |
|---|---:|---|
| Tipo | Sim | Conteúdo + metadata |
| Número do Documento | Sim | Conteúdo + metadata |
| Assunto | Sim | Conteúdo |
| Ementa | Sim | Conteúdo |
| Situação | Sim | Conteúdo + metadata |
| Data do Diário | Sim | Metadata |
| Número Diário | Sim | Metadata |
| Link web | Sim | Metadata |

## Texto indexado

```text
Tipo: <valor>
Número: <valor>
Assunto: <valor>
Ementa: <valor>
Situação: <valor>
```

## Metadata mínima

```json
{
  "tipo": "...",
  "numero": "...",
  "situacao": "...",
  "data_diario": "...",
  "numero_diario": "...",
  "link_web": "..."
}
```

## Normalização

- `NaN` deve ser convertido para `None`;
- datas devem ser serializadas em formato estável;
- valores incompatíveis com ChromaDB devem ser convertidos para tipos suportados.
